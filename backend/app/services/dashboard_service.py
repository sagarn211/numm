from collections import defaultdict
from datetime import datetime, timedelta, timezone

from sqlalchemy import case, func

from app.models.audit_log import AuditLog
from app.models.cpse import CPSE
from app.models.demand_record import DemandRecord
from app.models.import_batch import ImportBatch
from app.models.inventory import Inventory
from app.models.material import Material
from app.models.material_mapping import MaterialMapping
from app.models.material_match import MaterialMatch
from app.models.national_material import NationalMaterial


def comprehensive_dashboard_metrics(db):
    total_materials = db.query(func.count(Material.id)).scalar() or 0
    risky_union = db.query(
        MaterialMatch.material_a_id.label("material_id")
    ).filter(MaterialMatch.classification.in_(["EXACT", "NEAR_DUPLICATE"]), MaterialMatch.status == "PENDING").union(
        db.query(MaterialMatch.material_b_id.label("material_id")).filter(
            MaterialMatch.classification.in_(["EXACT", "NEAR_DUPLICATE"]), MaterialMatch.status == "PENDING"
        )
    ).subquery()
    risky_count = db.query(func.count()).select_from(risky_union).scalar() or 0
    class_counts = dict(db.query(
        MaterialMatch.classification, func.count(MaterialMatch.id)
    ).group_by(MaterialMatch.classification).all())
    mapped_count = db.query(func.count(func.distinct(MaterialMapping.material_id))).scalar() or 0
    mapped_ids = {material_id for (material_id,) in db.query(MaterialMapping.material_id).all()}

    cpse_codes = defaultdict(set)
    for sector, code in db.query(CPSE.sector, CPSE.code).all():
        cpse_codes[sector or "Unknown"].add(code)
    sector_rows = {}
    for sector, materials, mapped, risky in db.query(
        CPSE.sector,
        func.count(func.distinct(Material.id)),
        func.count(func.distinct(MaterialMapping.material_id)),
        func.count(func.distinct(risky_union.c.material_id)),
    ).outerjoin(Material, Material.cpse_id == CPSE.id).outerjoin(
        MaterialMapping, MaterialMapping.material_id == Material.id
    ).outerjoin(
        risky_union, risky_union.c.material_id == Material.id
    ).group_by(CPSE.sector).all():
        sector_rows[sector or "Unknown"] = {
            "materials": materials,
            "mapped": mapped,
            "duplicate_candidates": risky,
            "cpses": cpse_codes[sector or "Unknown"],
        }

    demand_by_material = defaultdict(float)
    for material_id, quantity in db.query(
        DemandRecord.material_id, func.sum(DemandRecord.required_quantity)
    ).group_by(DemandRecord.material_id).all():
        demand_by_material[material_id] = float(quantity or 0)
    national_by_material = dict(db.query(
        MaterialMapping.material_id,
        func.min(MaterialMapping.national_material_id),
    ).group_by(MaterialMapping.material_id).all())
    demand_by_national = defaultdict(float)
    for material_id, quantity in demand_by_material.items():
        demand_by_national[national_by_material.get(material_id)] += quantity
    national_codes = dict(db.query(
        NationalMaterial.id, NationalMaterial.national_code
    ).filter(NationalMaterial.id.in_([
        national_id for national_id in demand_by_national if national_id is not None
    ])).all()) if any(national_id is not None for national_id in demand_by_national) else {}
    inventory_by_material = defaultdict(lambda: {"quantity": 0.0, "priced_value": 0.0, "priced_quantity": 0.0})
    effective = case(
        (Inventory.available_quantity - Inventory.reserved_quantity > 0,
         Inventory.available_quantity - Inventory.reserved_quantity),
        else_=0,
    )
    for material_id, quantity, priced_value, priced_quantity in db.query(
        Inventory.material_id,
        func.sum(effective),
        func.sum(case((Inventory.unit_cost.isnot(None), effective * Inventory.unit_cost), else_=0)),
        func.sum(case((Inventory.unit_cost.isnot(None), effective), else_=0)),
    ).group_by(Inventory.material_id).all():
        inventory_by_material[material_id] = {
            "quantity": float(quantity or 0),
            "priced_value": float(priced_value or 0),
            "priced_quantity": float(priced_quantity or 0),
        }
    recent_since = datetime.utcnow() - timedelta(days=365)
    recent_unit_cost = dict(db.query(
        Inventory.material_id, func.avg(Inventory.unit_cost)
    ).filter(
        Inventory.unit_cost.isnot(None), Inventory.last_updated >= recent_since
    ).group_by(Inventory.material_id).all())
    excess_quantity = 0.0
    shortage_quantity = 0.0
    savings = 0.0
    priced_surplus_records = 0
    for material_id, row in inventory_by_material.items():
        surplus = max(row["quantity"] - demand_by_material[material_id], 0)
        shortage_quantity += max(demand_by_material[material_id] - row["quantity"], 0)
        excess_quantity += surplus
        if material_id in recent_unit_cost:
            savings += surplus * float(recent_unit_cost[material_id])
            priced_surplus_records += 1
    for material_id, quantity in demand_by_material.items():
        if material_id not in inventory_by_material:
            shortage_quantity += quantity

    cpse_quality = []
    for cpse in db.query(CPSE).order_by(CPSE.code).all():
        cpse_materials = db.query(Material).filter(Material.cpse_id == cpse.id).all()
        count = len(cpse_materials)

        def coverage(predicate):
            return round(sum(predicate(item) for item in cpse_materials) * 100 / count, 2) if count else 0

        description = coverage(lambda item: bool(item.description))
        category = coverage(lambda item: bool(item.category and item.category != "UNCLASSIFIED"))
        unit = coverage(lambda item: bool(item.unit))
        manufacturer = coverage(lambda item: bool(item.manufacturer))
        mapping = coverage(lambda item: item.id in mapped_ids)
        classification = coverage(lambda item: bool(item.classification_source))
        cpse_quality.append({
            "cpse_id": cpse.id,
            "cpse_code": cpse.code,
            "sector": cpse.sector,
            "materials": count,
            "mapping_coverage_percent": mapping,
            "data_quality_score": round(
                (description + category + unit + manufacturer + mapping + classification) / 6, 2
            ),
        })

    reviewed = db.query(MaterialMatch.reviewed_at, MaterialMatch.created_at).filter(
        MaterialMatch.reviewed_at.isnot(None)
    ).all()
    def utc_aware(value):
        return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)

    average_review_hours = round(
        sum(
            (utc_aware(reviewed_at) - utc_aware(created_at)).total_seconds()
            for reviewed_at, created_at in reviewed
        ) / 3600 / len(reviewed),
        2,
    ) if reviewed else 0
    total_import_rows, failed_import_rows = db.query(
        func.coalesce(func.sum(ImportBatch.total_rows), 0),
        func.coalesce(func.sum(ImportBatch.failed_rows), 0),
    ).one()

    from app.services.stock_analytics_service import stock_analytics
    comparable_stock = stock_analytics(db)
    from app.services.data_quality_service import quality_metrics
    quality = quality_metrics(db)
    duplicate_total = db.query(MaterialMatch).filter(
        MaterialMatch.classification.in_(["EXACT", "NEAR_DUPLICATE"])
    ).count()
    duplicate_reviewed = db.query(MaterialMatch).filter(
        MaterialMatch.classification.in_(["EXACT", "NEAR_DUPLICATE"]),
        MaterialMatch.status.in_(["APPROVED", "REJECTED"]),
    ).count()
    all_matches = db.query(MaterialMatch).count()
    reviewed_matches = db.query(MaterialMatch).filter(MaterialMatch.status != "PENDING").count()
    harmonization_factors = {
        "mapping_coverage": round(mapped_count * 100 / total_materials, 2) if total_materials else 0,
        "duplicate_rationalization": round(duplicate_reviewed * 100 / duplicate_total, 2) if duplicate_total else 100,
        "technical_completeness": quality["technical_readiness_percent"],
        "classification_completeness": quality["category_completeness"],
        "approval_completion": round(reviewed_matches * 100 / all_matches, 2) if all_matches else 100,
        "data_quality": quality["data_quality_score"],
    }
    harmonization_index = round(sum(harmonization_factors.values()) / len(harmonization_factors), 2)

    return {
        "harmonization": {
            "index": harmonization_index,
            "factors": harmonization_factors,
            "formula": "Equal-weight mean of mapping coverage, duplicate rationalization, technical completeness, classification completeness, approval completion, and explainable data quality",
            "mapped_materials": mapped_count,
            "unmapped_materials": max(total_materials - mapped_count, 0),
            "approved_mappings": db.query(MaterialMapping).filter(MaterialMapping.approved_by.isnot(None)).count(),
            "pending_reviews": db.query(MaterialMatch).filter(MaterialMatch.status == "PENDING").count(),
        },
        "stock_analytics": comparable_stock,
        "duplicate_risk_percent": round(risky_count * 100 / total_materials, 2) if total_materials else 0,
        "duplicate_candidate_materials": risky_count,
        "match_classification_counts": dict(class_counts),
        "mapping_coverage_percent": round(mapped_count * 100 / total_materials, 2) if total_materials else 0,
        "average_approval_turnaround_hours": average_review_hours,
        "import_error_rate_percent": round(failed_import_rows * 100 / total_import_rows, 2) if total_import_rows else 0,
        "excess_inventory_quantity": comparable_stock["by_unit"][0]["surplus"] if len(comparable_stock["by_unit"]) == 1 else None,
        "shortage_quantity": comparable_stock["by_unit"][0]["shortage"] if len(comparable_stock["by_unit"]) == 1 else None,
        "estimated_savings_opportunity": None,
        "savings_assumption": "Reusable surplus quantity × average recorded unit cost updated in the last 365 days; excludes unpriced inventory.",
        "priced_surplus_records": priced_surplus_records,
        "demand_by_national_code": [
            {
                "national_material_id": national_id,
                "national_code": national_codes.get(national_id) if national_id is not None else "UNMAPPED",
                "required_quantity": round(quantity, 2),
            }
            for national_id, quantity in sorted(
                demand_by_national.items(), key=lambda item: (item[0] is None, item[0] or 0)
            )
        ],
        "cpse_metrics": cpse_quality,
        "sectors": [{
            "name": sector, "materials": row["materials"], "matched": row["mapped"],
            "duplicates": row["duplicate_candidates"],
            "standardization": round(row["mapped"] * 100 / row["materials"], 2) if row["materials"] else 0,
            "cpseList": sorted(row["cpses"]),
        } for sector, row in sorted(sector_rows.items())],
        "audit_events": db.query(AuditLog).count(),
    }
