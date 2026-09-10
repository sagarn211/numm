import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.models.integration_sync import IntegrationSync
from app.schemas.integration import SAPPushRequest, SAPSyncRequest
from app.services.sap_service import push_mappings_to_sap, reconcile_mappings_with_sap, sync_from_sap
from app.services.erp_connector import connector_for
from app.models.user import User
from app.utils.rbac import ensure_cpse_access, is_system_admin, require_permission

router = APIRouter(prefix="/api/integrations", tags=["Integrations"])
logger = logging.getLogger(__name__)

@router.post("/sap/sync")
async def sync(
    payload: SAPSyncRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("integration.manage")),
):
    ensure_cpse_access(current_user, payload.cpse_id)
    try:
        return await sync_from_sap(db, payload.cpse_id, payload.connector, current_user.id)
    except HTTPException:
        raise
    except Exception:
        logger.exception("SAP sync failed for cpse_id=%s", payload.cpse_id)
        raise HTTPException(502, "SAP sync failed")

@router.get("/sap/status")
def status(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("integration.read")),
):
    query = db.query(IntegrationSync)
    if not is_system_admin(current_user):
        if current_user.cpse_id is None:
            return None
        query = query.filter(IntegrationSync.cpse_id == current_user.cpse_id)
    return query.order_by(IntegrationSync.id.desc()).first()

@router.get("/sap/history")
def history(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("integration.read")),
):
    query = db.query(IntegrationSync)
    if not is_system_admin(current_user):
        if current_user.cpse_id is None:
            return []
        query = query.filter(IntegrationSync.cpse_id == current_user.cpse_id)
    return query.order_by(IntegrationSync.id.desc()).all()

@router.post("/sap/push-mappings")
async def push_mappings(
    payload: SAPPushRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("integration.manage")),
):
    ensure_cpse_access(current_user, payload.cpse_id)
    try:
        return await push_mappings_to_sap(db, payload.cpse_id, payload.connector, current_user.id)
    except HTTPException:
        raise
    except Exception:
        logger.exception("SAP mapping push failed for cpse_id=%s", payload.cpse_id)
        raise HTTPException(502, "SAP mapping push failed")


@router.get("/sap/health/{connector_name}")
async def connector_health(
    connector_name: str,
    current_user: User = Depends(require_permission("integration.read")),
):
    try:
        return await connector_for(connector_name).health_check()
    except Exception:
        logger.exception("SAP connector health check failed for %s", connector_name)
        raise HTTPException(502, "SAP connector unavailable")


@router.post("/sap/reconcile")
async def reconcile(
    payload: SAPPushRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("integration.manage")),
):
    ensure_cpse_access(current_user, payload.cpse_id)
    try:
        return await reconcile_mappings_with_sap(
            db, payload.cpse_id, payload.connector, current_user.id
        )
    except HTTPException:
        raise
    except Exception:
        logger.exception("SAP reconciliation failed for cpse_id=%s", payload.cpse_id)
        raise HTTPException(502, "SAP reconciliation failed")
