from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.models.audit_log import AuditLog
from app.models.material_mapping import MaterialMapping
from app.services.mapping_service import map_material
from app.services.audit_service import write_audit
from app.utils.rbac import require_permission
from app.models.material import Material
from app.services.identity_service import validate_members

router = APIRouter(prefix="/api/mapping-history", tags=["Mapping history"])


class RestoreRequest(BaseModel):
    reason: str = Field(min_length=5, max_length=1000)


class MigrationRow(BaseModel):
    material_id: int
    national_material_id: int
    expected_national_material_id: int | None = None


class MigrationPlan(BaseModel):
    rows: list[MigrationRow] = Field(min_length=1, max_length=500)
    reason: str = Field(min_length=5, max_length=1000)
    confirm: bool = False


@router.post("/migration")
def migrate(payload: MigrationPlan, db: Session = Depends(get_db), user=Depends(require_permission("national.write"))):
    ids = [row.material_id for row in payload.rows]
    if len(set(ids)) != len(ids):
        raise HTTPException(400, "Each source material may occur only once")
    materials = {item.id: item for item in db.query(Material).filter(Material.id.in_(ids)).order_by(Material.id).with_for_update().all()}
    preview = []
    grouped = {}
    for row in payload.rows:
        material = materials.get(row.material_id)
        if not material or material.status != "ACTIVE":
            raise HTTPException(400, "All source materials must exist and be active")
        current = db.query(MaterialMapping).filter(MaterialMapping.material_id == row.material_id).first()
        current_id = current.national_material_id if current else None
        if current_id != row.expected_national_material_id:
            raise HTTPException(409, "Source mapping changed; refresh and review the migration plan")
        grouped.setdefault(row.national_material_id, []).append(material)
        preview.append({"material_id": row.material_id, "before": current_id, "after": row.national_material_id})
    for target, incoming in sorted(grouped.items()):
        validate_members(db, target, incoming)
    if payload.confirm:
        for row in payload.rows:
            map_material(db, row.material_id, row.national_material_id, "MIGRATION", user.id)
        write_audit(db, "LEGACY_MAPPING_MIGRATION", "MaterialMapping", None, user.id,
                    {"reason": payload.reason, "changes": preview}, commit=False)
        db.commit()
    return {"confirmed": payload.confirm, "changes": preview}


@router.get("/{material_id}")
def history(material_id: int, db: Session = Depends(get_db), user=Depends(require_permission("audit.read"))):
    # Includes removed mappings, whose database row no longer exists.
    return [row for row in db.query(AuditLog).filter(AuditLog.entity_type == "MaterialMapping").order_by(AuditLog.id.desc()).all()
            if any((row.details or {}).get(key, {}).get("material_id") == material_id for key in ("before", "after"))]


@router.post("/{event_id}/restore")
def restore(event_id: int, payload: RestoreRequest, db: Session = Depends(get_db), user=Depends(require_permission("national.write"))):
    event = db.query(AuditLog).filter(AuditLog.id == event_id, AuditLog.entity_type == "MaterialMapping").first()
    if not event:
        raise HTTPException(404, "Mapping event not found")
    before, after = (event.details or {}).get("before"), (event.details or {}).get("after")
    if not before or not before.get("national_material_id"):
        raise HTTPException(409, "This event has no previous mapping to restore")
    current = db.query(MaterialMapping).filter(MaterialMapping.material_id == before["material_id"]).with_for_update().first()
    if (after and (not current or current.national_material_id != after.get("national_material_id"))) or (not after and current):
        raise HTTPException(409, "Mapping has changed since this event; review the current mapping first")
    newer = history(before["material_id"], db, user)
    if newer and newer[0].id != event.id:
        raise HTTPException(409, "Only the latest mapping change can be restored")
    mapping = map_material(db, before["material_id"], before["national_material_id"], "RESTORED", user.id)
    write_audit(db, "MAPPING_RESTORE_REQUESTED", "Material", before["material_id"], user.id,
                {"event_id": event.id, "reason": payload.reason}, commit=False)
    db.commit(); db.refresh(mapping)
    return mapping
