from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.schemas.material import MaterialCreate, MaterialUpdate
from app.services.material_service import create_material, get_material, material_query
from app.services.cleaning_service import clean_description, normalize_uom, standardize_description
from app.utils.pagination import paginate
from app.models.material import Material
from app.models.user import User
from app.models.material_mapping import MaterialMapping
from app.models.national_material import NationalMaterial
from app.models.material_match import MaterialMatch
from app.models.inventory import Inventory
from app.models.demand_record import DemandRecord
from app.utils.rbac import ensure_cpse_access, is_system_admin, require_permission
from app.services.audit_service import snapshot_model, write_audit
from app.services.classification_service import classify_material
from app.services.material_schema_service import canonical_standard_description

router = APIRouter(prefix="/api/materials", tags=["Materials"])


def material_data(material, db: Session):
    """Keep the existing material payload and add its approved National Material Code."""
    data = {column.name: getattr(material, column.name) for column in Material.__table__.columns}
    codes = [code for (code,) in db.query(NationalMaterial.national_code).join(
        MaterialMapping, MaterialMapping.national_material_id == NationalMaterial.id
    ).filter(MaterialMapping.material_id == material.id).all() if code]
    data["national_code"] = ", ".join(codes) if codes else None
    return data

@router.post("")
def create(
    payload: MaterialCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("material.write")),
):
    ensure_cpse_access(current_user, payload.cpse_id)
    return create_material(db, payload, current_user.id)

@router.get("")
def list_legacy(
    search: str | None = None,
    cpse_id: int | None = None,
    category: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("material.read")),
):
    if not is_system_admin(current_user):
        ensure_cpse_access(current_user, current_user.cpse_id)
        cpse_id = current_user.cpse_id
    return [material_data(material, db) for material in material_query(db, search, cpse_id, category, status).all()]

@router.get("/paginated")
def list_paginated(
    search: str | None = None,
    cpse_id: int | None = None,
    category: str | None = None,
    status: str | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("material.read")),
):
    if not is_system_admin(current_user):
        ensure_cpse_access(current_user, current_user.cpse_id)
        cpse_id = current_user.cpse_id
    result = paginate(material_query(db, search, cpse_id, category, status), page, limit)
    result["items"] = [material_data(material, db) for material in result["items"]]
    return result

@router.get("/{material_id}")
def get_one(
    material_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("material.read")),
):
    material = get_material(db, material_id)
    ensure_cpse_access(current_user, material.cpse_id)
    return material_data(material, db)

@router.put("/{material_id}")
def update(
    material_id: int,
    payload: MaterialUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("material.write")),
):
    obj = get_material(db, material_id)
    ensure_cpse_access(current_user, obj.cpse_id)
    has_dependencies = any((
        db.query(MaterialMapping.id).filter(MaterialMapping.material_id == material_id).first(),
        db.query(MaterialMatch.id).filter(or_(
            MaterialMatch.material_a_id == material_id,
            MaterialMatch.material_b_id == material_id,
        )).first(),
        db.query(Inventory.id).filter(Inventory.material_id == material_id).first(),
        db.query(DemandRecord.id).filter(DemandRecord.material_id == material_id).first(),
    ))
    if has_dependencies:
        raise HTTPException(
            409,
            "Material has mappings, matches, inventory, or demand history and cannot be deleted",
        )
    before = snapshot_model(obj)
    data = payload.model_dump(exclude_unset=True)
    if "description" in data and data["description"] is not None:
        obj.description = data.pop("description")
        obj.cleaned_description = clean_description(obj.description)
        obj.normalized_description = standardize_description(obj.cleaned_description)
    if "unit" in data:
        data["unit"] = normalize_uom(data["unit"])
    for k, v in data.items():
        setattr(obj, k, v)
    category_was_corrected = "category" in payload.model_fields_set
    if "description" in payload.model_fields_set or category_was_corrected:
        classification = classify_material(
            obj.cleaned_description,
            obj.category,
            obj.specifications,
            prefer_supplied=category_was_corrected,
        )
        obj.category = classification.category
        obj.subcategory = payload.subcategory or classification.subcategory
        obj.classification_confidence = classification.confidence
        obj.classification_source = classification.source
        obj.classification_version = classification.rule_version
    if {"description", "category", "subcategory", "specifications"} & payload.model_fields_set:
        obj.recommended_standard_description = canonical_standard_description(
            obj.cleaned_description or obj.description, obj.subcategory, obj.specifications
        )
    after = snapshot_model(obj)
    write_audit(db, "MATERIAL_UPDATED", "Material", obj.id, current_user.id, {"before": before, "after": after}, commit=False)
    if category_was_corrected:
        write_audit(db, "MATERIAL_CATEGORY_CORRECTED", "Material", obj.id, current_user.id, {
            "before": {"category": before["category"], "subcategory": before["subcategory"]},
            "after": {"category": obj.category, "subcategory": obj.subcategory},
        }, commit=False)
    db.commit(); db.refresh(obj)
    return obj

@router.delete("/{material_id}")
def delete(
    material_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("material.write")),
):
    obj = get_material(db, material_id)
    ensure_cpse_access(current_user, obj.cpse_id)
    before = snapshot_model(obj)
    db.delete(obj)
    write_audit(db, "MATERIAL_DELETED", "Material", material_id, current_user.id, {"before": before}, commit=False)
    db.commit()
    return {"message": "Material deleted"}
