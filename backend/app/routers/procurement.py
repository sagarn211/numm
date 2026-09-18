"""Validated procurement history and unit/currency-aware spend analysis."""
import csv
import re
from io import StringIO
from collections import defaultdict
from fastapi import APIRouter, Depends, HTTPException, File, Form, UploadFile, Query
from pydantic import BaseModel, Field, ConfigDict, ValidationError
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.models.procurement_record import ProcurementRecord
from app.models.material import Material
from app.models.cpse import CPSE
from sqlalchemy.exc import IntegrityError
from app.models.material_mapping import MaterialMapping
from app.utils.rbac import require_permission, ensure_cpse_access, is_system_admin
from app.services.cleaning_service import normalize_uom
from app.services.audit_service import write_audit
from app.services.procurement_intelligence_service import procurement_opportunities, reuse_before_buy
from app.services.price_intelligence_service import material_price_intelligence, list_materials, highlights

router = APIRouter(prefix="/api/procurement", tags=["Procurement history"])


class PurchaseLine(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False, str_strip_whitespace=True)
    material_code: str = Field(min_length=1, max_length=120)
    order_number: str = Field(min_length=1, max_length=100)
    line_number: str = Field(min_length=1, max_length=30)
    supplier: str = Field(min_length=1, max_length=255)
    period: str = Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")
    quantity: float = Field(gt=0)
    uom: str = Field(min_length=1, max_length=50)
    unit_price: float = Field(ge=0)
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    lead_time_days: int | None = Field(default=None, ge=0)


class ReusePreview(BaseModel):
    national_material_id: int = Field(gt=0)
    requesting_cpse_id: int = Field(gt=0)
    requested_quantity: float = Field(gt=0, allow_inf_nan=False)
    uom: str = Field(min_length=1, max_length=50)
    period: str | None = Field(default=None, pattern=r"^\d{4}-(0[1-9]|1[0-2])$")


def prepare_lines(db, cpse_id, raw_rows):
    if not raw_rows or len(raw_rows) > 10000:
        raise HTTPException(400, "Provide between 1 and 10000 purchase lines")
    materials = {m.material_code.upper(): m for m in db.query(Material).filter(Material.cpse_id == cpse_id).all()}
    seen = set(db.query(ProcurementRecord.order_number, ProcurementRecord.line_number).filter(ProcurementRecord.cpse_id == cpse_id).all())
    prepared, errors = [], []
    for row_number, raw in enumerate(raw_rows, 2):
        try:
            values = {key: value for key, value in raw.items() if value != ""}
            line = PurchaseLine.model_validate(values)
            material = materials.get(line.material_code.upper())
            if not material:
                raise ValueError("Unknown material for selected CPSE")
            if normalize_uom(line.uom) != normalize_uom(material.unit):
                raise ValueError("UOM must match the material base unit")
            key = (line.order_number, line.line_number)
            if key in seen:
                raise ValueError("Duplicate order line in file or procurement history")
            seen.add(key)
            data = line.model_dump(exclude={"material_code"})
            prepared.append({**data, "cpse_id": cpse_id, "material_id": material.id, "uom": normalize_uom(line.uom)})
        except (ValidationError, ValueError) as exc:
            errors.append({"row": row_number, "message": str(exc)})
    return prepared, errors


@router.post("/import")
async def import_history(file: UploadFile = File(...), cpse_id: int = Form(...), confirm: bool = Form(False),
                         db: Session = Depends(get_db), user=Depends(require_permission("import.manage"))):
    ensure_cpse_access(user, cpse_id)
    if not db.query(CPSE).filter(CPSE.id == cpse_id).with_for_update().first():
        raise HTTPException(404, "CPSE not found")
    content = await file.read(5 * 1024 * 1024 + 1)
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(413, "Purchase history file exceeds 5 MB")
    try:
        rows = list(csv.DictReader(StringIO(content.decode("utf-8-sig"))))
    except (UnicodeError, csv.Error):
        raise HTTPException(400, "Upload a UTF-8 CSV purchase history file")
    prepared, errors = prepare_lines(db, cpse_id, rows)
    if confirm:
        if errors:
            raise HTTPException(400, {"message": "Correct all rows before importing", "errors": errors[:100]})
        for row in prepared:
            db.add(ProcurementRecord(**row))
        write_audit(db, "PROCUREMENT_HISTORY_IMPORTED", "CPSE", cpse_id, user.id,
                    {"filename": file.filename, "lines": len(prepared)}, commit=False)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(409, "An order line was already imported; preview the file again")
    return {"confirmed": confirm, "valid_rows": len(prepared), "errors": errors[:100], "preview": prepared[:5]}


@router.get("/analytics")
def analytics(db: Session = Depends(get_db), user=Depends(require_permission("demand.read"))):
    query = db.query(ProcurementRecord)
    if not is_system_admin(user):
        query = query.filter(ProcurementRecord.cpse_id == user.cpse_id)
    mappings = dict(db.query(MaterialMapping.material_id, MaterialMapping.national_material_id).all())
    grouped = defaultdict(lambda: {"quantity": 0, "spend": 0, "suppliers": set(), "cpses": set(), "lead_times": []})
    for row in query.all():
        national_id = mappings.get(row.material_id)
        key = (national_id, None if national_id else row.material_id, row.period, row.uom, row.currency)
        group = grouped[key]
        group["quantity"] += row.quantity
        group["spend"] += row.quantity * row.unit_price
        group["suppliers"].add(row.supplier)
        group["cpses"].add(row.cpse_id)
        if row.lead_time_days is not None:
            group["lead_times"].append(row.lead_time_days)
    return [{"national_material_id": key[0], "material_id": key[1], "period": key[2], "uom": key[3], "currency": key[4],
             "quantity": value["quantity"], "spend": round(value["spend"], 2),
             "weighted_unit_price": round(value["spend"] / value["quantity"], 4),
             "suppliers": sorted(value["suppliers"]), "participating_cpses": sorted(value["cpses"]),
             "average_lead_time_days": sum(value["lead_times"]) / len(value["lead_times"]) if value["lead_times"] else None}
            for key, value in grouped.items()]


def _price_scope(user):
    """Keep price analytics within the application's existing CPSE visibility."""
    return None if is_system_admin(user) else user.cpse_id


@router.get("/price-intelligence/summary")
def price_intelligence_summary(db: Session = Depends(get_db), user=Depends(require_permission("demand.read"))):
    result = list_materials(db, _price_scope(user), page=1, limit=1)
    return {"materials_with_history": result["total"], "default_material": result["items"][0] if result["items"] else None}


@router.get("/price-intelligence/materials")
def price_intelligence_materials(search: str | None = Query(None, max_length=200), page: int = Query(1, ge=1),
                                limit: int = Query(25, ge=1, le=100), db: Session = Depends(get_db),
                                user=Depends(require_permission("demand.read"))):
    return list_materials(db, _price_scope(user), search, page, limit)


@router.get("/price-intelligence/highlights")
def price_intelligence_highlights(limit: int = Query(5, ge=1, le=20), db: Session = Depends(get_db),
                                  user=Depends(require_permission("demand.read"))):
    return highlights(db, _price_scope(user), limit)


@router.get("/price-intelligence/{national_material_id}")
def price_intelligence_detail(national_material_id: int, uom: str | None = None, currency: str | None = None,
                             range: str | None = Query(None, pattern=r"^(3m|6m|12m|all)$"), db: Session = Depends(get_db),
                             user=Depends(require_permission("demand.read"))):
    months = {"3m": 3, "6m": 6, "12m": 12}.get(range)
    result = material_price_intelligence(db, national_material_id, _price_scope(user), uom, currency, months)
    if not result:
        raise HTTPException(404, "National Material not found")
    return result


@router.get("/price-intelligence/{national_material_id}/trend")
def price_intelligence_trend(national_material_id: int, uom: str | None = None, currency: str | None = None,
                             range: str = Query("12m", pattern=r"^(3m|6m|12m|all)$"), db: Session = Depends(get_db),
                             user=Depends(require_permission("demand.read"))):
    months = {"3m": 3, "6m": 6, "12m": 12}.get(range)
    result = material_price_intelligence(db, national_material_id, _price_scope(user), uom, currency, months)
    if not result: raise HTTPException(404, "National Material not found")
    return {"national_material_id": national_material_id, "uom": result["uom"], "currency": result["currency"], "series": result["series"], "data_quality": result["data_quality"]}


@router.get("/price-intelligence/{national_material_id}/cpse-comparison")
def price_intelligence_cpse_comparison(national_material_id: int, uom: str | None = None, currency: str | None = None,
                                       db: Session = Depends(get_db), user=Depends(require_permission("demand.read"))):
    result = material_price_intelligence(db, national_material_id, _price_scope(user), uom, currency)
    if not result: raise HTTPException(404, "National Material not found")
    return {"national_material_id": national_material_id, "uom": result["uom"], "currency": result["currency"], "weighted_average": result["latest_weighted_avg"], "price_spread_percent": result["price_spread_percent"], "items": result["cpse_comparison"], "data_quality": result["data_quality"]}


@router.get("/opportunities")
def opportunities(period: str | None = None, db: Session = Depends(get_db),
                  user=Depends(require_permission("demand.read"))):
    if period and not re.match(r"^\d{4}-(0[1-9]|1[0-2])$", period):
        raise HTTPException(400, "Period must use YYYY-MM")
    return procurement_opportunities(db, period)


@router.post("/reuse-preview")
def preview_reuse(payload: ReusePreview, db: Session = Depends(get_db),
                  user=Depends(require_permission("request.create", "demand.read"))):
    ensure_cpse_access(user, payload.requesting_cpse_id)
    return reuse_before_buy(db, payload.national_material_id, payload.requesting_cpse_id,
                            payload.requested_quantity, payload.uom, payload.period)
