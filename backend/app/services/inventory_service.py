from fastapi import HTTPException
from app.models.inventory import Inventory
from app.models.material import Material
from app.models.material_mapping import MaterialMapping
from app.models.cpse import CPSE
from app.services.cleaning_service import normalize_uom

def create_inventory(db, payload):
    material = db.query(Material).filter(Material.id == payload.material_id).first()
    if not material:
        raise HTTPException(404, "Material not found")
    if material.cpse_id != payload.cpse_id:
        raise HTTPException(400, "Inventory CPSE must match the material CPSE")
    if normalize_uom(payload.uom) != normalize_uom(material.unit):
        raise HTTPException(400, "Stock must use the material base unit")
    if payload.reserved_quantity > payload.available_quantity:
        raise HTTPException(400, "Reserved quantity cannot exceed available quantity")
    existing = db.query(Inventory).filter(
        Inventory.material_id == payload.material_id,
        Inventory.warehouse == payload.warehouse.strip(),
    ).first()
    if existing:
        raise HTTPException(409, "This material already has stock at the selected warehouse")
    data = payload.model_dump()
    data["warehouse"] = payload.warehouse.strip()
    data["uom"] = payload.uom.strip().upper()
    obj = Inventory(**data)
    db.add(obj); db.flush()
    return obj

def national_availability(db, national_material_id):
    material_ids = [
        m.material_id for m in db.query(MaterialMapping).filter(
            MaterialMapping.national_material_id == national_material_id
        ).all()
    ]
    rows = db.query(Inventory).filter(Inventory.material_id.in_(material_ids)).all() if material_ids else []
    companies, total = [], 0.0
    for r in rows:
        effective = max(r.available_quantity - r.reserved_quantity, 0)
        total += effective
        cpse = db.query(CPSE).filter(CPSE.id == r.cpse_id).first()
        companies.append({
            "inventory_id": r.id,
            "cpse_id": r.cpse_id,
            "cpse_name": cpse.name if cpse else None,
            "material_id": r.material_id,
            "warehouse": r.warehouse,
            "available_quantity": r.available_quantity,
            "reserved_quantity": r.reserved_quantity,
            "effective_available": effective,
            "uom": r.uom,
        })
    return {"national_material_id": national_material_id, "total_available": total, "companies": companies}
