"""Historical, traceable procurement price analytics.

This module deliberately contains no forecast logic.  Values are calculated
only from persisted procurement records whose legacy material has an approved
National Material mapping.
"""
from collections import defaultdict
import re

from sqlalchemy.orm import joinedload

from app.models.cpse import CPSE
from app.models.material_mapping import MaterialMapping
from app.models.national_material import NationalMaterial
from app.models.procurement_record import ProcurementRecord
from app.services.cleaning_service import normalize_uom

_PERIOD = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


def _round(value, digits=4):
    return round(value, digits) if value is not None else None


def _base_query(db, cpse_id=None):
    query = db.query(ProcurementRecord, MaterialMapping.national_material_id).join(
        MaterialMapping, MaterialMapping.material_id == ProcurementRecord.material_id
    )
    if cpse_id is not None:
        query = query.filter(ProcurementRecord.cpse_id == cpse_id)
    return query


def _valid_rows(rows):
    valid, excluded = [], defaultdict(int)
    for record, national_id in rows:
        uom = normalize_uom(record.uom or "")
        currency = (record.currency or "").strip().upper()
        if record.quantity is None or record.quantity <= 0:
            excluded["INVALID_QUANTITY"] += 1
        elif record.unit_price is None or record.unit_price < 0:
            excluded["INVALID_UNIT_PRICE"] += 1
        elif not _PERIOD.match(record.period or ""):
            excluded["INVALID_DATE"] += 1
        elif not uom:
            excluded["INVALID_UOM"] += 1
        elif not re.match(r"^[A-Z]{3}$", currency):
            excluded["INVALID_CURRENCY"] += 1
        else:
            valid.append((record, national_id, uom, currency))
    return valid, dict(excluded)


def _quality(db, cpse_id=None, national_id=None, valid_rows=(), excluded=None):
    all_records = db.query(ProcurementRecord)
    if cpse_id is not None:
        all_records = all_records.filter(ProcurementRecord.cpse_id == cpse_id)
    if national_id is not None:
        mapped_ids = db.query(MaterialMapping.material_id).filter(MaterialMapping.national_material_id == national_id)
        all_records = all_records.filter(ProcurementRecord.material_id.in_(mapped_ids))
    total_records = all_records.count()
    mapped_records = _base_query(db, cpse_id).filter(MaterialMapping.national_material_id == national_id).count() if national_id else _base_query(db, cpse_id).count()
    dimensions = sorted({(uom, currency) for _, _, uom, currency in valid_rows})
    return {
        "valid_records": len(valid_rows),
        "excluded_records": sum((excluded or {}).values()),
        "excluded_by_reason": excluded or {},
        "unmapped_record_count": max(total_records - mapped_records, 0) if national_id is None else 0,
        "uom_conflict": len({uom for uom, _ in dimensions}) > 1,
        "currency_conflict": len({currency for _, currency in dimensions}) > 1,
    }


def _aggregate(rows):
    """Return monthly quantity-weighted aggregates for one UOM/currency."""
    buckets = defaultdict(lambda: {"quantity": 0.0, "spend": 0.0, "transactions": 0, "suppliers": set(), "cpses": set()})
    for row, _, _, _ in rows:
        bucket = buckets[row.period]
        bucket["quantity"] += float(row.quantity)
        bucket["spend"] += float(row.quantity) * float(row.unit_price)
        bucket["transactions"] += 1
        bucket["suppliers"].add(row.supplier)
        bucket["cpses"].add(row.cpse_id)
    series = []
    for period, value in sorted(buckets.items()):
        series.append({
            "period": period,
            "weighted_avg_unit_price": _round(value["spend"] / value["quantity"]),
            "total_quantity": _round(value["quantity"]), "total_spend": _round(value["spend"], 2),
            "transaction_count": value["transactions"], "supplier_count": len(value["suppliers"]),
            "cpse_count": len(value["cpses"]),
        })
    return series


def _movement(series):
    if not series:
        return {"current": None, "previous": None, "absolute_change": None, "change_percent": None, "direction": "STABLE"}
    current = series[-1]["weighted_avg_unit_price"]
    previous = series[-2]["weighted_avg_unit_price"] if len(series) > 1 else None
    change = _round(current - previous) if previous is not None else None
    percent = _round(change * 100 / previous, 2) if previous not in (None, 0) else None
    direction = "UP" if change is not None and change > 0.0001 else "DOWN" if change is not None and change < -0.0001 else "STABLE"
    return {"current": current, "previous": previous, "absolute_change": change, "change_percent": percent, "direction": direction}


def material_price_intelligence(db, national_id, cpse_id=None, uom=None, currency=None, range_months=None):
    national = db.query(NationalMaterial).filter(NationalMaterial.id == national_id).first()
    if not national:
        return None
    valid, excluded = _valid_rows(_base_query(db, cpse_id).filter(MaterialMapping.national_material_id == national_id).all())
    quality = _quality(db, cpse_id, national_id, valid, excluded)
    dimensions = sorted({(row_uom, row_currency) for _, _, row_uom, row_currency in valid})
    chosen_uom, chosen_currency = normalize_uom(uom or ""), (currency or "").upper()
    if not chosen_uom and len(dimensions) == 1:
        chosen_uom, chosen_currency = dimensions[0]
    selected = [row for row in valid if row[2] == chosen_uom and row[3] == chosen_currency] if chosen_uom and chosen_currency else []
    series = _aggregate(selected)
    if range_months and range_months > 0:
        series = series[-range_months:]
    movement = _movement(series)
    total_quantity = sum(point["total_quantity"] for point in series)
    total_spend = sum(point["total_spend"] for point in series)
    cpse_buckets = defaultdict(lambda: {"quantity": 0.0, "spend": 0.0, "transactions": 0})
    for row, _, _, _ in selected:
        bucket = cpse_buckets[row.cpse_id]
        bucket["quantity"] += float(row.quantity); bucket["spend"] += float(row.quantity) * float(row.unit_price); bucket["transactions"] += 1
    cpse_codes = dict(db.query(CPSE.id, CPSE.code).filter(CPSE.id.in_(cpse_buckets)).all()) if cpse_buckets else {}
    national_average = _round(total_spend / total_quantity) if total_quantity else None
    comparison = []
    for cpse, value in cpse_buckets.items():
        weighted = _round(value["spend"] / value["quantity"])
        difference = _round(weighted - national_average)
        comparison.append({"cpse_id": cpse, "cpse_code": cpse_codes.get(cpse, str(cpse)), "weighted_average": weighted,
                           "quantity": _round(value["quantity"]), "transaction_count": value["transactions"],
                           "difference_from_national_average": difference,
                           "difference_percent": _round(difference * 100 / national_average, 2) if national_average else None})
    comparison.sort(key=lambda item: item["weighted_average"])
    prices = [item["weighted_average"] for item in comparison]
    return {
        "national_material_id": national.id, "national_code": national.national_code, "description": national.description,
        "uom": chosen_uom or None, "currency": chosen_currency or None,
        "available_dimensions": [{"uom": item[0], "currency": item[1]} for item in dimensions],
        "latest_weighted_avg": movement["current"], "previous_weighted_avg": movement["previous"],
        "absolute_change": movement["absolute_change"], "change_percent": movement["change_percent"], "direction": movement["direction"],
        "period_high": max((point["weighted_avg_unit_price"] for point in series), default=None),
        "period_low": min((point["weighted_avg_unit_price"] for point in series), default=None),
        "total_quantity": _round(total_quantity), "total_spend": _round(total_spend, 2),
        "participating_cpse_count": len(comparison), "supplier_count": len({row[0].supplier for row in selected}),
        "minimum_cpse_weighted_price": min(prices, default=None), "maximum_cpse_weighted_price": max(prices, default=None),
        "price_spread_percent": _round((max(prices) - min(prices)) * 100 / min(prices), 2) if prices and min(prices) > 0 else None,
        "series": series, "cpse_comparison": comparison, "data_quality": quality,
    }


def list_materials(db, cpse_id=None, search=None, page=1, limit=25):
    # Select distinct integer IDs first. PostgreSQL cannot DISTINCT a row that
    # includes NationalMaterial's JSON columns (specifications/provenance).
    query = db.query(NationalMaterial.id, NationalMaterial.national_code).join(MaterialMapping, MaterialMapping.national_material_id == NationalMaterial.id).join(
        ProcurementRecord, ProcurementRecord.material_id == MaterialMapping.material_id).distinct()
    if cpse_id is not None: query = query.filter(ProcurementRecord.cpse_id == cpse_id)
    if search:
        term = f"%{search.strip()}%"
        query = query.filter((NationalMaterial.national_code.ilike(term)) | (NationalMaterial.description.ilike(term)))
    total = query.count()
    ids = [row[0] for row in query.order_by(NationalMaterial.national_code).offset((page - 1) * limit).limit(limit).all()]
    materials = db.query(NationalMaterial).filter(NationalMaterial.id.in_(ids)).order_by(NationalMaterial.national_code).all() if ids else []
    return {"items": [material_price_intelligence(db, item.id, cpse_id) for item in materials], "page": page, "limit": limit, "total": total}


def highlights(db, cpse_id=None, limit=5):
    rows = list_materials(db, cpse_id, page=1, limit=1000)["items"]
    populated = [row for row in rows if row["latest_weighted_avg"] is not None]
    return {
        "largest_increases": sorted([r for r in populated if r["change_percent"] is not None and r["change_percent"] > 0], key=lambda r: -r["change_percent"])[:limit],
        "largest_decreases": sorted([r for r in populated if r["change_percent"] is not None and r["change_percent"] < 0], key=lambda r: r["change_percent"])[:limit],
        "highest_variance": sorted([r for r in populated if r["price_spread_percent"] is not None], key=lambda r: -r["price_spread_percent"])[:limit],
        "highest_spend": sorted(populated, key=lambda r: -(r["total_spend"] or 0))[:limit],
    }
