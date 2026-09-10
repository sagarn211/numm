from datetime import datetime
from fastapi import HTTPException
from app.models.material_request import MaterialRequest
from app.models.request_item import RequestItem
from app.models.stock_allocation import StockAllocation
from app.models.inventory import Inventory
from app.models.national_material import NationalMaterial
from app.services.allocation_service import preview_allocation

def create_request(db, requesting_cpse_id, requested_by=None):
    obj = MaterialRequest(requesting_cpse_id=requesting_cpse_id, requested_by=requested_by)
    db.add(obj); db.flush()
    obj.request_number = f"MR-{obj.id:06d}"
    db.commit(); db.refresh(obj)
    return obj

def add_item(db, request_id, payload):
    req = db.query(MaterialRequest).filter(MaterialRequest.id == request_id).first()
    if not req:
        raise HTTPException(404, "Request not found")
    if req.status != "DRAFT":
        raise HTTPException(400, "Only DRAFT requests can be changed")
    if not db.query(NationalMaterial).filter(
        NationalMaterial.id == payload.national_material_id,
        NationalMaterial.status == "ACTIVE",
    ).first():
        raise HTTPException(404, "Active National Material not found")
    obj = RequestItem(
        request_id=request_id,
        national_material_id=payload.national_material_id,
        requested_quantity=payload.requested_quantity,
        uom=payload.uom.strip().upper(),
    )
    db.add(obj); db.commit(); db.refresh(obj)
    return obj

def submit_request(db, request_id):
    req = db.query(MaterialRequest).filter(MaterialRequest.id == request_id).first()
    if not req or req.status != "DRAFT":
        raise HTTPException(400, "Request must be DRAFT")

    if not db.query(RequestItem).filter(RequestItem.request_id == request_id).first():
        raise HTTPException(400, "Add at least one material and quantity before submitting")

    allocation_preview = preview_allocation(db, request_id)
    procurement_required = any(result["unallocated_quantity"] > 0 for result in allocation_preview)
    inventory_ids = sorted({
        allocation["inventory_id"]
        for result in allocation_preview
        for allocation in result["allocations"]
    })
    locked_inventory = db.query(Inventory).filter(
        Inventory.id.in_(inventory_ids)
    ).order_by(Inventory.id.asc()).with_for_update().all() if inventory_ids else []
    inventory_by_id = {inventory.id: inventory for inventory in locked_inventory}
    for result in allocation_preview:
        for a in result["allocations"]:
            inv = inventory_by_id.get(a["inventory_id"])
            if not inv:
                raise HTTPException(409, "Inventory changed during submission; retry")
            effective = max(inv.available_quantity - inv.reserved_quantity, 0)
            allocated_quantity = min(a["allocated_quantity"], effective)
            if allocated_quantity < a["allocated_quantity"]:
                procurement_required = True
            if allocated_quantity <= 0:
                continue
            inv.reserved_quantity += allocated_quantity
            db.add(StockAllocation(
                request_item_id=result["request_item_id"],
                inventory_id=inv.id,
                source_cpse_id=inv.cpse_id,
                allocated_quantity=allocated_quantity,
                status="RESERVED",
            ))

    req.status = "PROCUREMENT_REQUIRED" if procurement_required else "SUBMITTED"
    req.submitted_at = datetime.utcnow()
    db.commit(); db.refresh(req)
    return req

def approve_request(db, request_id, approved_by=None):
    req = db.query(MaterialRequest).filter(MaterialRequest.id == request_id).first()
    if not req or req.status not in {"SUBMITTED", "PROCUREMENT_REQUIRED"}:
        raise HTTPException(400, "Request must be SUBMITTED or PROCUREMENT_REQUIRED")
    req.status = "APPROVED_PROCUREMENT" if req.status == "PROCUREMENT_REQUIRED" else "APPROVED"
    req.approved_at = datetime.utcnow(); req.approved_by = approved_by
    db.commit(); db.refresh(req)
    return req

def reject_request(db, request_id):
    """Reject a submitted request and release its reserved stock."""
    req = db.query(MaterialRequest).filter(MaterialRequest.id == request_id).first()
    if not req or req.status not in {"SUBMITTED", "PROCUREMENT_REQUIRED"}:
        raise HTTPException(400, "Request must be SUBMITTED or PROCUREMENT_REQUIRED")

    item_ids = [item.id for item in db.query(RequestItem).filter(RequestItem.request_id == request_id).all()]
    allocations = db.query(StockAllocation).filter(
        StockAllocation.request_item_id.in_(item_ids),
        StockAllocation.status == "RESERVED",
    ).all() if item_ids else []

    inventory_ids = sorted({allocation.inventory_id for allocation in allocations})
    locked_inventory = db.query(Inventory).filter(
        Inventory.id.in_(inventory_ids)
    ).order_by(Inventory.id.asc()).with_for_update().all() if inventory_ids else []
    inventory_by_id = {inventory.id: inventory for inventory in locked_inventory}
    for allocation in allocations:
        inventory = inventory_by_id.get(allocation.inventory_id)
        if inventory:
            inventory.reserved_quantity = max(inventory.reserved_quantity - allocation.allocated_quantity, 0)
        allocation.status = "RELEASED"

    req.status = "REJECTED"
    db.commit(); db.refresh(req)
    return req

def fulfill_request(db, request_id):
    req = db.query(MaterialRequest).filter(MaterialRequest.id == request_id).first()
    if not req or req.status != "APPROVED":
        raise HTTPException(400, "Request must be APPROVED")

    item_ids = [i.id for i in db.query(RequestItem).filter(RequestItem.request_id == request_id).all()]
    allocations = db.query(StockAllocation).filter(
        StockAllocation.request_item_id.in_(item_ids),
        StockAllocation.status == "RESERVED"
    ).all() if item_ids else []

    inventory_ids = sorted({allocation.inventory_id for allocation in allocations})
    locked_inventory = db.query(Inventory).filter(
        Inventory.id.in_(inventory_ids)
    ).order_by(Inventory.id.asc()).with_for_update().all() if inventory_ids else []
    inventory_by_id = {inventory.id: inventory for inventory in locked_inventory}
    for a in allocations:
        inv = inventory_by_id.get(a.inventory_id)
        if not inv:
            raise HTTPException(409, "Inventory changed during fulfillment; retry")
        inv.available_quantity = max(inv.available_quantity - a.allocated_quantity, 0)
        inv.reserved_quantity = max(inv.reserved_quantity - a.allocated_quantity, 0)
        a.status = "ALLOCATED"

    req.status = "FULFILLED"
    db.commit(); db.refresh(req)
    return req
