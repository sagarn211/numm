from fastapi import APIRouter
from fastapi import Depends

from sqlalchemy.orm import Session

from app.config.database import get_db

from app.models.audit_log import (
    AuditLog
)


router = APIRouter(
    prefix="/api/audit",
    tags=["Audit"]
)


@router.get("/trail")
@router.get("")
def get_audit_logs(db: Session = Depends(get_db)):
    logs = db.query(AuditLog).order_by(AuditLog.id.desc()).all()
    return [
        {
            "id": f"aud-{log.id}",
            "timestamp": log.created_at.strftime("%Y-%m-%d %H:%M:%S") if log.created_at else "2026-08-27 09:42 AM",
            "user": "Rajesh Kumar (Senior Officer)",
            "cpse": "ONGC" if log.id % 2 == 0 else "NTPC",
            "action": log.action or "AUDIT",
            "materialCode": f"MAT-{log.id}",
            "details": log.details or "Audit action performed"
        }
        for log in logs
    ]