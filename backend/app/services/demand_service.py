from sqlalchemy import case, func

from app.models.demand_record import DemandRecord
from app.models.material_mapping import MaterialMapping

def aggregated_demand(db, cpse_id=None):
    mapping = db.query(
        MaterialMapping.material_id.label("material_id"),
        func.min(MaterialMapping.national_material_id).label("national_material_id"),
    ).group_by(MaterialMapping.material_id).subquery()
    source_material_id = case(
        (mapping.c.national_material_id.is_(None), DemandRecord.material_id),
        else_=None,
    )
    query = db.query(
        mapping.c.national_material_id,
        source_material_id.label("source_material_id"),
        DemandRecord.period,
        DemandRecord.uom,
        func.sum(DemandRecord.required_quantity).label("required_quantity"),
    ).outerjoin(
        mapping, mapping.c.material_id == DemandRecord.material_id
    )
    if cpse_id is not None:
        query = query.filter(DemandRecord.cpse_id == cpse_id)
    rows = query.group_by(
        mapping.c.national_material_id,
        source_material_id,
        DemandRecord.period,
        DemandRecord.uom,
    ).all()

    return [
        {
            "national_material_id": row.national_material_id,
            "material_id": row.source_material_id,
            "period": row.period,
            "uom": row.uom,
            "required_quantity": row.required_quantity,
        }
        for row in rows
    ]
