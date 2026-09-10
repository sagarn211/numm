from fastapi import HTTPException
from sqlalchemy import or_
from app.models.material import Material
from app.models.cpse import CPSE
from app.models.material_mapping import MaterialMapping
from app.models.national_material import NationalMaterial
from app.services.cleaning_service import clean_description, normalize_uom, standardize_description
from app.services.duplicate_service import material_code_exists
from app.services.classification_service import classify_material
from app.services.audit_service import snapshot_model, write_audit
from app.services.material_schema_service import canonical_standard_description

def create_material(db, payload, actor_id=None):
    if not db.query(CPSE).filter(CPSE.id == payload.cpse_id).first():
        raise HTTPException(404, "CPSE not found")
    code = payload.material_code.strip()
    if material_code_exists(db, payload.cpse_id, code):
        raise HTTPException(409, "Material code already exists for this CPSE")
    cleaned = clean_description(payload.description)
    classification = classify_material(cleaned, payload.category, payload.specifications)
    subcategory = payload.subcategory or classification.subcategory
    obj = Material(
        cpse_id=payload.cpse_id,
        material_code=code,
        description=payload.description.strip(),
        original_description=payload.description,
        cleaned_description=cleaned,
        normalized_description=standardize_description(cleaned),
        category=classification.category,
        subcategory=subcategory,
        classification_confidence=classification.confidence,
        classification_source=classification.source,
        classification_version=classification.rule_version,
        unit=normalize_uom(payload.unit),
        manufacturer=payload.manufacturer,
        model=payload.model,
        specifications=payload.specifications or {},
        recommended_standard_description=canonical_standard_description(
            cleaned, subcategory, payload.specifications or {}
        ),
        source=payload.source.upper(),
    )
    db.add(obj); db.flush()
    write_audit(db, "MATERIAL_CREATED", "Material", obj.id, actor_id, {"after": snapshot_model(obj)}, commit=False)
    db.commit(); db.refresh(obj)
    return obj

def get_material(db, material_id):
    obj = db.query(Material).filter(Material.id == material_id).first()
    if not obj:
        raise HTTPException(404, "Material not found")
    return obj

def material_query(db, search=None, cpse_id=None, category=None, status=None):
    q = db.query(Material)
    if search:
        term = f"%{search}%"
        national_code_match = db.query(MaterialMapping.id).join(
            NationalMaterial, NationalMaterial.id == MaterialMapping.national_material_id
        ).filter(
            MaterialMapping.material_id == Material.id,
            NationalMaterial.national_code.ilike(term),
        ).exists()
        q = q.filter(or_(
            Material.material_code.ilike(term),
            Material.description.ilike(term),
            Material.cleaned_description.ilike(term),
            Material.category.ilike(term),
            Material.subcategory.ilike(term),
            Material.manufacturer.ilike(term),
            Material.model.ilike(term),
            national_code_match,
        ))
    if cpse_id:
        q = q.filter(Material.cpse_id == cpse_id)
    if category:
        q = q.filter(Material.category == category)
    if status:
        q = q.filter(Material.status == status)
    return q.order_by(Material.id.desc())
