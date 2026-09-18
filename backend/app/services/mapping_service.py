from app.models.material_mapping import MaterialMapping
from app.services.audit_service import snapshot_model, write_audit

def map_material(db, material_id, national_material_id, mapping_type="MANUAL", approved_by=None):
    from fastapi import HTTPException
    from app.models.material import Material
    from app.services.identity_service import validate_members
    if mapping_type == "FUNCTIONAL_EQUIVALENT":
        raise HTTPException(409, "Substitutes must retain separate material identities")
    material = db.query(Material).filter(Material.id == material_id).with_for_update().first()
    if not material or material.status != "ACTIVE":
        raise HTTPException(409, "An active source material is required")
    validate_members(db, national_material_id, [material])
    from app.models.national_material import NationalMaterial
    national = db.query(NationalMaterial).filter(NationalMaterial.id == national_material_id).first()
    material.approved_standard_description = national.description
    obj = db.query(MaterialMapping).filter(
        MaterialMapping.material_id == material_id,
    ).with_for_update().first()
    if obj:
        if obj.national_material_id != national_material_id:
            raise HTTPException(409, {
                "message": "Mapping conflict: material already belongs to a different National Material",
                "material_id": material_id, "current_national_material_id": obj.national_material_id,
                "requested_national_material_id": national_material_id,
            })
        return obj
    obj = MaterialMapping(
        material_id=material_id,
        national_material_id=national_material_id,
        mapping_type=mapping_type,
        approved_by=approved_by,
    )
    db.add(obj); db.flush()
    write_audit(db, "MAPPING_CREATED", "MaterialMapping", obj.id, approved_by, {
        "after": snapshot_model(obj),
    }, commit=False)
    return obj


def reassign_material_mapping(db, material_id, national_material_id, approved_by=None, reason=None):
    """Explicit governance-only reassignment. Normal approval paths must not call this."""
    from fastapi import HTTPException
    if not (reason or "").strip():
        raise HTTPException(400, "A reason is required to reassign a National Material mapping")
    obj = db.query(MaterialMapping).filter(MaterialMapping.material_id == material_id).with_for_update().first()
    if not obj:
        raise HTTPException(404, "Existing mapping not found")
    if obj.national_material_id == national_material_id:
        return obj
    before = snapshot_model(obj)
    obj.national_material_id = national_material_id
    obj.mapping_type = "GOVERNED_REASSIGNMENT"
    obj.approved_by = approved_by
    db.flush()
    write_audit(db, "MAPPING_REASSIGNED", "MaterialMapping", obj.id, approved_by,
                {"reason": reason, "before": before, "after": snapshot_model(obj)}, commit=False)
    return obj
