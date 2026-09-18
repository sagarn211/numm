import httpx
from datetime import datetime
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.config.settings import settings
from app.models.material import Material
from app.models.material_image import MaterialImage
from app.models.material_mapping import MaterialMapping
from app.models.national_material import NationalMaterial
from app.models.cpse import CPSE
from app.models.user import User
from app.services.image_storage_service import upload_image
from app.utils.rbac import ensure_cpse_access, require_permission

router = APIRouter(tags=["Visual material discovery"])
WARNING = "Visual similarity is for candidate discovery only. Technical validation is required."

def primary_url(db, material_id):
    row = db.query(MaterialImage.image_url).filter(MaterialImage.material_id == material_id, MaterialImage.is_primary.is_(True), MaterialImage.verification_status == "VERIFIED").first()
    return row[0] if row else None

@router.post("/api/materials/{material_id}/images")
async def add_image(material_id: int, file: UploadFile = File(...), image_type: str = Form("OTHER"), db: Session = Depends(get_db), current_user: User = Depends(require_permission("material.write"))):
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material: raise HTTPException(404, "Material not found")
    ensure_cpse_access(current_user, material.cpse_id)
    stored = await upload_image(file)
    has_primary = db.query(MaterialImage.id).filter(MaterialImage.material_id == material_id, MaterialImage.is_primary.is_(True)).first()
    image = MaterialImage(material_id=material_id, image_type=image_type.upper(), source_type="WAREHOUSE_UPLOAD", verification_status="PENDING", is_primary=not bool(has_primary), uploaded_by=current_user.id, **stored)
    db.add(image); db.commit(); db.refresh(image)
    return image

@router.post("/api/material-images/{image_id}/verify")
async def verify_image(image_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_permission("material.write"))):
    image = db.query(MaterialImage).filter(MaterialImage.id == image_id).first()
    if not image: raise HTTPException(404, "Material image not found")
    material = db.query(Material).filter(Material.id == image.material_id).first()
    ensure_cpse_access(current_user, material.cpse_id)
    # Verification is explicit; failure to index never invalidates the verified asset.
    image.verification_status, image.verified_by, image.verified_at = "VERIFIED", current_user.id, datetime.utcnow()
    if image.is_primary:
        db.query(MaterialImage).filter(MaterialImage.material_id == image.material_id, MaterialImage.id != image.id).update({MaterialImage.is_primary: False})
    db.commit()
    try:
        async with httpx.AsyncClient(timeout=90) as client:
            source = await client.get(image.image_url); source.raise_for_status()
            response = await client.post(f"{settings.AI_SERVICE_URL}/api/v1/visual-index", files={"file": (image.original_filename or "material.jpg", source.content, source.headers.get("content-type", "image/jpeg"))}, data={"material_image_id": image.id, "material_id": image.material_id})
            response.raise_for_status()
    except Exception:
        # The record remains verified and can be retried by an operations job; never roll back material data.
        return {"image_id": image.id, "verification_status": image.verification_status, "indexed": False, "warning": "Image verified, but visual indexing is pending retry."}
    return {"image_id": image.id, "verification_status": image.verification_status, "indexed": True}

@router.post("/api/visual-search")
async def visual_search(file: UploadFile = File(...), top_k: int = Form(5), db: Session = Depends(get_db), current_user: User = Depends(require_permission("material.read"))):
    # AI service receives only the query image and IDs; PostgreSQL remains authoritative.
    try:
        payload = {"file": (file.filename or "query.jpg", await file.read(), file.content_type or "application/octet-stream")}
        async with httpx.AsyncClient(timeout=90) as client:
            response = await client.post(f"{settings.AI_SERVICE_URL}/api/v1/visual-search", files=payload, data={"top_k": max(1, min(top_k, 20))})
            response.raise_for_status(); result = response.json()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(exc.response.status_code, exc.response.json().get("detail", "Visual search unavailable")) from exc
    except Exception as exc:
        raise HTTPException(503, "Visual search service is unavailable") from exc
    candidates = []
    for candidate in result.get("candidates", []):
        material = db.query(Material).filter(Material.id == candidate.get("material_id")).first()
        if not material or (current_user.cpse_id is not None and material.cpse_id != current_user.cpse_id): continue
        mapping = db.query(MaterialMapping).filter(MaterialMapping.material_id == material.id).first()
        national = db.query(NationalMaterial).filter(NationalMaterial.id == mapping.national_material_id).first() if mapping else None
        cpse = db.query(CPSE).filter(CPSE.id == material.cpse_id).first()
        candidates.append({
            "material_id": material.id,
            "material_code": material.material_code,
            "description": material.description,
            "category": material.category,
            "subcategory": material.subcategory,
            "unit": material.unit,
            "manufacturer": material.manufacturer,
            "model": material.model,
            "specifications": material.specifications or {},
            "status": material.status,
            "cpse_id": material.cpse_id,
            "cpse_code": cpse.code if cpse else None,
            "national_code": national.national_code if national else None,
            "national_description": national.description if national else None,
            "mapping_type": mapping.mapping_type if mapping else None,
            "primary_image_url": primary_url(db, material.id),
            "visual_similarity": candidate["visual_similarity"],
            "warning": WARNING,
        })
    return {"engine": result.get("engine", "CLIP_FAISS"), "model": result.get("model", "clip-ViT-B-32"), "candidates": candidates, "warning": WARNING}
