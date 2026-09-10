from app.models.request_item import RequestItem
from app.models.material_mapping import MaterialMapping
from app.models.inventory import Inventory
from app.services.cleaning_service import normalize_uom

def preview_allocation(db, request_id):
    items = db.query(RequestItem).filter(RequestItem.request_id == request_id).all()
    output = []
    consumed = {}
    for item in items:
        ids = [
            m.material_id for m in db.query(MaterialMapping).filter(
                MaterialMapping.national_material_id == item.national_material_id
            ).all()
        ]
        inventories = db.query(Inventory).filter(Inventory.material_id.in_(ids)).all() if ids else []
        inventories.sort(key=lambda x: max(x.available_quantity - x.reserved_quantity, 0), reverse=True)

        remaining = item.requested_quantity
        allocations = []
        for inv in inventories:
            if normalize_uom(inv.uom) != normalize_uom(item.uom):
                continue
            effective = max(
                inv.available_quantity
                - inv.reserved_quantity
                - consumed.get(inv.id, 0),
                0,
            )
            if remaining <= 0:
                break
            qty = min(effective, remaining)
            if qty > 0:
                consumed[inv.id] = consumed.get(inv.id, 0) + qty
                allocations.append({
                    "inventory_id": inv.id,
                    "source_cpse_id": inv.cpse_id,
                    "allocated_quantity": qty,
                    "status": "PROPOSED",
                })
                remaining -= qty

        output.append({
            "request_item_id": item.id,
            "national_material_id": item.national_material_id,
            "requested_quantity": item.requested_quantity,
            "allocated_quantity": item.requested_quantity - remaining,
            "unallocated_quantity": remaining,
            "allocations": allocations,
        })
    return output
