from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.models.cpse import CPSE
from app.schemas.cpse import CPSECreate, CPSEUpdate
from app.services.cpse_service import create_cpse, get_cpse
from app.models.user import User
from app.utils.rbac import require_permission
from app.services.audit_service import snapshot_model, write_audit

router = APIRouter(prefix="/api/cpses", tags=["CPSEs"])

@router.post("")
def create(
    payload: CPSECreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("cpse.manage")),
):
    obj = create_cpse(db, payload)
    write_audit(
        db, "CPSE_CREATED", "CPSE", obj.id, current_user.id,
        {"after": snapshot_model(obj)}, commit=False,
    )
    db.commit()
    db.refresh(obj)
    return obj

@router.get("")
def list_all(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("cpse.read")),
):
    return db.query(CPSE).order_by(CPSE.name).all()

@router.get("/{cpse_id}")
def get_one(
    cpse_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("cpse.read")),
):
    return get_cpse(db, cpse_id)

@router.put("/{cpse_id}")
def update(
    cpse_id: int,
    payload: CPSEUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("cpse.manage")),
):
    obj = get_cpse(db, cpse_id)
    before = snapshot_model(obj)
    for k, v in payload.model_dump(exclude_unset=True).items():
        if k == "code":
            if v is None:
                raise HTTPException(400, "code cannot be null")
            v = v.upper()
        setattr(obj, k, v)
    write_audit(
        db, "CPSE_UPDATED", "CPSE", obj.id, current_user.id,
        {"before": before, "after": snapshot_model(obj)}, commit=False,
    )
    db.commit(); db.refresh(obj)
    return obj

@router.delete("/{cpse_id}")
def delete(
    cpse_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("cpse.manage")),
):
    obj = get_cpse(db, cpse_id)
    if obj.materials:
        raise HTTPException(409, "Cannot delete CPSE with materials")
    before = snapshot_model(obj)
    db.delete(obj)
    write_audit(
        db, "CPSE_DELETED", "CPSE", cpse_id, current_user.id,
        {"before": before}, commit=False,
    )
    db.commit()
    return {"message": "CPSE deleted"}
