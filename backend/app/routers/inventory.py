from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.models.inventory import Inventory
from app.schemas.inventory import InventoryCreate, InventoryUpdate
from app.services.inventory_service import create_inventory
from app.models.material import Material
from app.models.user import User
from app.utils.rbac import ensure_cpse_access, is_system_admin, require_permission
from app.services.audit_service import snapshot_model, write_audit

router = APIRouter(prefix="/api/inventory", tags=["Inventory"])

@router.post("")
def create(
    payload: InventoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("inventory.write")),
):
    ensure_cpse_access(current_user, payload.cpse_id)
    material = db.query(Material).filter(Material.id == payload.material_id).first()
    if not material:
        raise HTTPException(404, "Material not found")
    if material.cpse_id != payload.cpse_id:
        raise HTTPException(400, "Inventory CPSE must match the material CPSE")
    obj = create_inventory(db, payload)
    write_audit(
        db, "INVENTORY_CREATED", "Inventory", obj.id, current_user.id,
        {"after": snapshot_model(obj)}, commit=False,
    )
    db.commit()
    db.refresh(obj)
    return obj

@router.get("")
def list_all(
    cpse_id: int | None = None,
    material_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("inventory.read")),
):
    q = db.query(Inventory)
    if not is_system_admin(current_user):
        if current_user.cpse_id is None:
            return []
        q = q.filter(Inventory.cpse_id == current_user.cpse_id)
    if cpse_id:
        q = q.filter(Inventory.cpse_id == cpse_id)
    if material_id:
        q = q.filter(Inventory.material_id == material_id)
    return q.order_by(Inventory.id.desc()).all()

@router.put("/{inventory_id}")
def update(
    inventory_id: int,
    payload: InventoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("inventory.write")),
):
    obj = db.query(Inventory).filter(Inventory.id == inventory_id).first()
    if not obj:
        raise HTTPException(404, "Inventory record not found")
    ensure_cpse_access(current_user, obj.cpse_id)
    before = snapshot_model(obj)
    changes = {
        key: value
        for key, value in payload.model_dump(exclude_unset=True).items()
        if value is not None
    }
    available = changes.get("available_quantity", obj.available_quantity)
    reserved = changes.get("reserved_quantity", obj.reserved_quantity)
    if available < 0 or reserved < 0:
        raise HTTPException(400, "Quantities cannot be negative")
    if reserved > available:
        raise HTTPException(400, "Reserved quantity cannot exceed available quantity")
    if "warehouse" in changes:
        changes["warehouse"] = changes["warehouse"].strip()
    if "uom" in changes:
        changes["uom"] = changes["uom"].strip().upper()
    for k, v in changes.items():
        setattr(obj, k, v)
    obj.last_updated = datetime.utcnow()
    write_audit(
        db, "INVENTORY_UPDATED", "Inventory", obj.id, current_user.id,
        {"before": before, "after": snapshot_model(obj)}, commit=False,
    )
    db.commit(); db.refresh(obj)
    return obj
