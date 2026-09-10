from fastapi import APIRouter, Depends, HTTPException
import math
from app.models.material import Material
from app.services.cleaning_service import normalize_uom
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.models.demand_record import DemandRecord
from app.services.demand_service import aggregated_demand
from app.models.user import User
from app.utils.rbac import ensure_cpse_access, is_system_admin, require_permission
from app.services.audit_service import snapshot_model, write_audit

router = APIRouter(prefix="/api/demand", tags=["Demand"])

@router.post("")
def create(
    cpse_id: int, material_id: int, period: str, required_quantity: float,
    uom: str = "EA", db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("demand.write")),
):
    ensure_cpse_access(current_user, cpse_id)
    material = db.query(Material).filter(Material.id == material_id, Material.cpse_id == cpse_id).first()
    if not material:
        raise HTTPException(400, "Material must belong to the selected CPSE")
    if not math.isfinite(required_quantity) or required_quantity < 0 or not period.strip():
        raise HTTPException(400, "A period and finite non-negative quantity are required")
    uom = normalize_uom(uom)
    if uom != normalize_uom(material.unit):
        raise HTTPException(400, "Demand must use the material base unit")
    obj = DemandRecord(cpse_id=cpse_id, material_id=material_id, period=period, required_quantity=required_quantity, uom=uom)
    db.add(obj); db.commit(); db.refresh(obj)
    write_audit(db, "DEMAND_CREATED", "DemandRecord", obj.id, current_user.id, {"after": snapshot_model(obj)})
    return obj

@router.get("")
def list_all(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("demand.read")),
):
    query = db.query(DemandRecord)
    if not is_system_admin(current_user):
        if current_user.cpse_id is None:
            return []
        query = query.filter(DemandRecord.cpse_id == current_user.cpse_id)
    return query.order_by(DemandRecord.id.desc()).all()

@router.get("/aggregate")
def aggregate(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("demand.read")),
):
    if not is_system_admin(current_user) and current_user.cpse_id is None:
        return []
    cpse_id = None if is_system_admin(current_user) else current_user.cpse_id
    return aggregated_demand(db, cpse_id)
