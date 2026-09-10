from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.models.national_material import NationalMaterial
from app.models.material_mapping import MaterialMapping
from app.models.material import Material
from app.models.request_item import RequestItem
from app.schemas.national_material import NationalMaterialCreate, NationalMaterialUpdate
from app.services.national_code_service import create_national_material, validate_national_code
from app.services.mapping_service import map_material
from app.services.inventory_service import national_availability
from app.services.audit_service import snapshot_model, write_audit
from app.models.user import User
from app.utils.rbac import require_permission
from app.services.national_material_360_service import national_material_360

router = APIRouter(prefix="/api/national-materials", tags=["National Materials"])

@router.post("")
def create(
    payload: NationalMaterialCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("national.write")),
):
    return create_national_material(
        db, payload.description, payload.category, payload.unit, payload.specifications,
        subcategory=payload.subcategory,
        actor_id=current_user.id,
    )

@router.get("")
def list_all(
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("national.read")),
):
    limit = min(max(limit, 1), 500)
    offset = max(offset, 0)
    materials = db.query(NationalMaterial).order_by(
        NationalMaterial.id.desc()
    ).offset(offset).limit(limit).all()
    material_ids = [material.id for material in materials]
    mappings_by_national = {}
    mappings = db.query(MaterialMapping).filter(
        MaterialMapping.national_material_id.in_(material_ids)
    ).all() if material_ids else []
    for mapping in mappings:
        mappings_by_national.setdefault(mapping.national_material_id, []).append({
            column.name: getattr(mapping, column.name)
            for column in MaterialMapping.__table__.columns
        })
    return [
        {
            **{
                column.name: getattr(material, column.name)
                for column in NationalMaterial.__table__.columns
            },
            "mappings": mappings_by_national.get(material.id, []),
        }
        for material in materials
    ]

@router.get("/{national_id}/availability")
def availability(
    national_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("national.read")),
):
    return national_availability(db, national_id)


@router.get("/{national_id}/360")
def material_360(
    national_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("national.read")),
):
    result = national_material_360(db, national_id)
    if not result:
        raise HTTPException(404, "National material not found")
    return result


@router.post("/{national_id}/mappings/{material_id}")
def add_mapping(
    national_id: int,
    material_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("national.write")),
):
    national = db.query(NationalMaterial).filter(
        NationalMaterial.id == national_id
    ).first()
    material = db.query(Material).filter(Material.id == material_id).first()
    if not national or not material:
        raise HTTPException(404, "National material or source material not found")
    mapping = map_material(
        db,
        material.id,
        national.id,
        mapping_type="MANUAL_REVIEW",
        approved_by=current_user.id,
    )
    db.commit()
    db.refresh(mapping)
    return mapping


@router.delete("/{national_id}/mappings/{material_id}")
def remove_mapping(
    national_id: int,
    material_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("national.write")),
):
    mapping = db.query(MaterialMapping).filter(
        MaterialMapping.national_material_id == national_id,
        MaterialMapping.material_id == material_id,
    ).with_for_update().first()
    if not mapping:
        raise HTTPException(404, "Material mapping not found")
    mapping_id = mapping.id
    before = snapshot_model(mapping)
    material = db.query(Material).filter(Material.id == material_id).first()
    if material:
        material.approved_standard_description = None
    db.delete(mapping)
    write_audit(
        db,
        "MAPPING_REMOVED",
        "MaterialMapping",
        mapping_id,
        current_user.id,
        {"before": before, "reason": "Reviewer removed mapping"},
        commit=False,
    )
    db.commit()
    return {"message": "Material mapping removed"}


@router.get("/validate/{national_code}")
def validate_code(
    national_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("national.read")),
):
    return validate_national_code(db, national_code)

@router.get("/{national_id}")
def get_one(
    national_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("national.read")),
):
    obj = db.query(NationalMaterial).filter(NationalMaterial.id == national_id).first()
    if not obj:
        raise HTTPException(404, "National material not found")
    mappings = db.query(MaterialMapping).filter(MaterialMapping.national_material_id == national_id).all()
    return {"material": obj, "mappings": mappings}

@router.put("/{national_id}")
def update(
    national_id: int,
    payload: NationalMaterialUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("national.write")),
):
    obj = db.query(NationalMaterial).filter(NationalMaterial.id == national_id).first()
    if not obj:
        raise HTTPException(404, "National material not found")
    before = snapshot_model(obj)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(obj, key, value)
    if obj.status == "ACTIVE":
        from app.services.identity_service import validate_members
        validate_members(db, national_id, [])
    write_audit(db, "NATIONAL_MATERIAL_UPDATED", "NationalMaterial", obj.id, current_user.id, {
        "before": before, "after": snapshot_model(obj), "national_code_immutable": obj.national_code,
    }, commit=False)
    db.commit(); db.refresh(obj)
    return obj


@router.delete("/{national_id}")
def delete(
    national_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("national.write")),
):
    obj = db.query(NationalMaterial).filter(NationalMaterial.id == national_id).first()
    if not obj:
        raise HTTPException(404, "National material not found")
    if db.query(MaterialMapping).filter(MaterialMapping.national_material_id == national_id).first():
        raise HTTPException(409, "This National Material has CPSE mappings and cannot be deleted")
    if db.query(RequestItem).filter(RequestItem.national_material_id == national_id).first():
        raise HTTPException(409, "This National Material is used by material requests and cannot be deleted")
    code = obj.national_code
    db.delete(obj)
    write_audit(db, "NATIONAL_MATERIAL_DELETED", "NationalMaterial", national_id, current_user.id, {"national_code": code}, commit=False)
    db.commit()
    return {"message": "National material deleted"}
