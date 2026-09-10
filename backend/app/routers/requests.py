from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.models.user import User
from app.models.material_request import MaterialRequest
from app.models.request_item import RequestItem
from app.models.material import Material
from app.models.material_mapping import MaterialMapping
from app.models.cpse import CPSE
from app.models.stock_allocation import StockAllocation
from app.schemas.request import RequestCreate, RequestItemCreate, DirectMaterialRequestCreate
from app.services.request_service import create_request, add_item, submit_request, approve_request, reject_request, fulfill_request
from app.services.allocation_service import preview_allocation
from app.services.audit_service import write_audit
from app.utils.rbac import has_permission, is_system_admin, require_permission, ensure_cpse_access

router = APIRouter(prefix="/api/requests", tags=["Material Requests"])

@router.post("")
def create(
    payload: RequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("request.create")),
):
    ensure_cpse_access(current_user, payload.requesting_cpse_id)
    if not db.query(CPSE).filter(CPSE.id == payload.requesting_cpse_id).first():
        raise HTTPException(404, "Requesting CPSE not found")
    request = create_request(db, payload.requesting_cpse_id, current_user.id)
    write_audit(db, "REQUEST_CREATED", "MaterialRequest", request.id, current_user.id)
    db.refresh(request)
    return request


@router.post("/direct-material")
def create_direct_material_request(
    payload: DirectMaterialRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("request.create")),
):
    """Create a draft containing one mapped product and the requested quantity."""
    ensure_cpse_access(current_user, payload.requesting_cpse_id)
    if not db.query(CPSE).filter(CPSE.id == payload.requesting_cpse_id).first():
        raise HTTPException(404, "Requesting CPSE not found")
    material = db.query(Material).filter(Material.id == payload.material_id).first()
    if not material:
        raise HTTPException(404, "Material not found")
    mapping = db.query(MaterialMapping).filter(
        MaterialMapping.material_id == material.id,
        MaterialMapping.approved_by.isnot(None),
    ).order_by(MaterialMapping.id).first()
    if not mapping:
        raise HTTPException(
            409,
            "This material has no approved National Material mapping. Submit it for review before requesting inventory.",
        )

    request = create_request(db, payload.requesting_cpse_id, current_user.id)
    item = add_item(db, request.id, RequestItemCreate(
        national_material_id=mapping.national_material_id,
        requested_quantity=payload.requested_quantity,
        uom=(payload.uom or material.unit or "EA").upper(),
    ))
    write_audit(db, "DIRECT_MATERIAL_REQUEST_CREATED", "MaterialRequest", request.id, current_user.id)
    return {"request": request, "item": item, "material_id": material.id}

@router.get("")
def list_all(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("request.read", "request.read_all")),
):
    query = db.query(MaterialRequest)
    if not has_permission(current_user, "request.read_all"):
        query = query.filter(
            (MaterialRequest.requested_by == current_user.id) |
            (MaterialRequest.requesting_cpse_id == current_user.cpse_id)
        )
    return query.order_by(MaterialRequest.id.desc()).all()


def _request_or_404(db: Session, request_id: int) -> MaterialRequest:
    request = db.query(MaterialRequest).filter(MaterialRequest.id == request_id).first()
    if not request:
        raise HTTPException(404, "Request not found")
    return request


def _ensure_can_view(user: User, request: MaterialRequest) -> None:
    if has_permission(user, "request.read_all") or is_system_admin(user):
        return
    if request.requested_by != user.id and request.requesting_cpse_id != user.cpse_id:
        raise HTTPException(403, "You cannot access this material request")


def _ensure_can_edit(user: User, request: MaterialRequest) -> None:
    if is_system_admin(user):
        return
    if request.requested_by != user.id:
        raise HTTPException(403, "Only the request creator can modify or submit this request")

@router.get("/{request_id}")
def get_one(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("request.read", "request.read_all")),
):
    req = _request_or_404(db, request_id)
    _ensure_can_view(current_user, req)
    items = db.query(RequestItem).filter(RequestItem.request_id == request_id).all()
    ids = [i.id for i in items]
    allocations = db.query(StockAllocation).filter(StockAllocation.request_item_id.in_(ids)).all() if ids else []
    return {"request": req, "items": items, "allocations": allocations}

@router.post("/{request_id}/items")
def add(
    request_id: int,
    payload: RequestItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("request.edit")),
):
    _ensure_can_edit(current_user, _request_or_404(db, request_id))
    return add_item(db, request_id, payload)

@router.delete("/{request_id}/items/{item_id}")
def delete_item(
    request_id: int,
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("request.edit")),
):
    req = _request_or_404(db, request_id)
    _ensure_can_edit(current_user, req)
    if not req or req.status != "DRAFT":
        raise HTTPException(400, "Only DRAFT requests can be modified")
    item = db.query(RequestItem).filter(RequestItem.id == item_id, RequestItem.request_id == request_id).first()
    if not item:
        raise HTTPException(404, "Item not found")
    db.delete(item); db.commit()
    return {"message": "Request item removed"}

@router.post("/{request_id}/preview-allocation")
def preview(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("request.read", "request.read_all")),
):
    _ensure_can_view(current_user, _request_or_404(db, request_id))
    return preview_allocation(db, request_id)

@router.post("/{request_id}/submit")
def submit(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("request.submit")),
):
    _ensure_can_edit(current_user, _request_or_404(db, request_id))
    request = submit_request(db, request_id)
    write_audit(db, "REQUEST_SUBMITTED", "MaterialRequest", request.id, current_user.id)
    db.refresh(request)
    return request

@router.post("/{request_id}/approve")
def approve(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("request.approve")),
):
    request = _request_or_404(db, request_id)
    if request.requested_by == current_user.id:
        raise HTTPException(403, "Maker-checker rule: you cannot approve your own request")
    request = approve_request(db, request_id, current_user.id)
    write_audit(db, "REQUEST_APPROVED", "MaterialRequest", request.id, current_user.id)
    db.refresh(request)
    return request

@router.post("/{request_id}/reject")
def reject(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("request.approve")),
):
    request = _request_or_404(db, request_id)
    if request.requested_by == current_user.id:
        raise HTTPException(403, "Maker-checker rule: you cannot reject your own request")
    request = reject_request(db, request_id)
    write_audit(db, "REQUEST_REJECTED", "MaterialRequest", request.id, current_user.id)
    db.refresh(request)
    return request

@router.post("/{request_id}/fulfill")
def fulfill(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("request.fulfill")),
):
    request = fulfill_request(db, request_id)
    write_audit(db, "REQUEST_FULFILLED", "MaterialRequest", request.id, current_user.id)
    db.refresh(request)
    return request
