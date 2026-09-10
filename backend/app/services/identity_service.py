"""Conservative engineering identity checks shared by every mapping entry point."""
from types import SimpleNamespace
from fastapi import HTTPException
from app.models.material import Material
from app.models.material_mapping import MaterialMapping
from app.models.national_material import NationalMaterial
from app.services.conflict_resolution_service import propose_canonical
from app.services.cleaning_service import normalize_uom


def validate_members(db, national_id, incoming):
    national = db.query(NationalMaterial).filter(NationalMaterial.id == national_id).with_for_update().first()
    if not national or national.status != "ACTIVE":
        raise HTTPException(409, "An active national material is required")
    members = db.query(Material).join(MaterialMapping, MaterialMapping.material_id == Material.id).filter(
        MaterialMapping.national_material_id == national_id
    ).all()
    canonical = SimpleNamespace(
        id=None, description=national.description, cleaned_description=national.description,
        category=national.category, subcategory=national.subcategory,
        unit=national.unit, specifications=national.specifications or {},
    )
    records = [canonical, *members, *incoming]
    from app.services.conflict_resolution_service import canonical_specs
    if any(str(value).startswith("CONFLICT:") for record in records for value in canonical_specs(record).values()):
        raise HTTPException(409, "Source description and structured attributes contradict each other; correct the source first")
    units = {normalize_uom(item.unit) for item in records if item.unit}
    if len(units) > 1:
        raise HTTPException(409, "Incompatible base units: use a validated conversion before mapping")
    conflicts = [item for item in propose_canonical(records)["conflicts"] if item["requires_review"]]
    if conflicts:
        raise HTTPException(409, {"message": "Material conflicts with national identity or existing members", "conflicts": conflicts})
    return national
