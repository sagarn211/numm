from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.models.audit_log import AuditLog
from app.models.user import User
from app.utils.rbac import require_permission
from app.services.audit_service import verify_audit_chain

router = APIRouter(prefix="/api/audit", tags=["Audit"])

@router.get("/verify")
def verify(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("audit.read")),
):
    return verify_audit_chain(db)

@router.get("")
def list_all(
    limit: int = Query(100, ge=1, le=500),
    action: str | None = None,
    entity_type: str | None = None,
    user_id: int | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("audit.read")),
):
    query = db.query(AuditLog)
    if action:
        query = query.filter(AuditLog.action == action.upper())
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)
    if user_id is not None:
        query = query.filter(AuditLog.user_id == user_id)
    if date_from:
        query = query.filter(AuditLog.created_at >= date_from)
    if date_to:
        query = query.filter(AuditLog.created_at <= date_to)
    return query.order_by(AuditLog.id.desc()).limit(limit).all()
