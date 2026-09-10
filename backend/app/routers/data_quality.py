from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.services.data_quality_service import quality_metrics
from app.services.classification_service import backfill_classifications
from app.services.audit_service import write_audit
from app.models.user import User
from app.utils.rbac import ensure_cpse_access, is_system_admin, require_permission

router = APIRouter(prefix="/api/data-quality", tags=["Data Quality"])

@router.get("")
def metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("data_quality.read")),
):
    return quality_metrics(db)

@router.post("/reclassify")
def reclassify(
    cpse_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("material.write")),
):
    if cpse_id is None:
        if not is_system_admin(current_user):
            raise HTTPException(403, "A CPSE must be specified")
    else:
        ensure_cpse_access(current_user, cpse_id)
    updated = backfill_classifications(db, cpse_id, current_user.id)
    write_audit(db, "MATERIALS_RECLASSIFIED", "Material", None, current_user.id, {
        "cpse_id": cpse_id, "updated": updated,
    }, commit=False)
    db.commit()
    return {"updated": updated, "taxonomy_version": "2026.09"}
