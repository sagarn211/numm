from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.models.cpse import CPSE
from app.models.material import Material
from app.models.material_match import MaterialMatch
from app.models.material_mapping import MaterialMapping
from app.schemas.approval import ApprovalRequest
from app.services.approval_service import approve_match, reject_match
from app.utils.pagination import paginate
from app.models.user import User
from app.utils.rbac import require_permission
from app.services.conflict_resolution_service import propose_canonical

router = APIRouter(prefix="/api/approvals", tags=["Approvals"])

@router.get("")
def list_approvals(
    status: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("approval.read")),
):
    q = db.query(MaterialMatch)
    if status:
        q = q.filter(MaterialMatch.status == status.upper())
    return q.order_by(MaterialMatch.final_score.desc()).all()

@router.get("/paginated")
def list_approvals_paginated(
    status: str = "PENDING",
    classification: str | None = Query(None),
    sort_by: str = Query("CONFIDENCE_DESC"),
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("approval.read")),
):
    status_key = status.upper()
    if status_key not in {"PENDING", "APPROVED", "REJECTED"}:
        raise HTTPException(400, "Invalid approval status")

    query = db.query(MaterialMatch).filter(MaterialMatch.status == status_key)
    classification_key = classification.upper() if classification else None
    allowed_classifications = {"EXACT", "NEAR_DUPLICATE", "FUNCTIONAL_EQUIVALENT"}
    if classification_key:
        if classification_key not in allowed_classifications:
            raise HTTPException(400, "Invalid match classification")
        query = query.filter(MaterialMatch.classification == classification_key)

    sort_key = sort_by.upper()
    orderings = {
        "CONFIDENCE_DESC": (MaterialMatch.final_score.desc(), MaterialMatch.id.desc()),
        "CONFIDENCE_ASC": (MaterialMatch.final_score.asc(), MaterialMatch.id.asc()),
        "NEWEST": (MaterialMatch.created_at.desc(), MaterialMatch.id.desc()),
        "OLDEST": (MaterialMatch.created_at.asc(), MaterialMatch.id.asc()),
    }
    if sort_key not in orderings:
        raise HTTPException(400, "Invalid approval sort")
    result = paginate(
        query.order_by(*orderings[sort_key]),
        page,
        limit,
    )
    matches = result["items"]
    material_ids = {
        material_id
        for match in matches
        for material_id in (match.material_a_id, match.material_b_id)
    }
    materials = (
        db.query(Material).filter(Material.id.in_(material_ids)).all()
        if material_ids else []
    )
    material_by_id = {material.id: material for material in materials}
    mapping_rows = db.query(MaterialMapping).filter(MaterialMapping.material_id.in_(material_ids)).all() if material_ids else []
    national_ids_by_material = {}
    for mapping in mapping_rows:
        national_ids_by_material.setdefault(mapping.material_id, set()).add(mapping.national_material_id)
    cpse_ids = {material.cpse_id for material in materials}
    cpse_by_id = {
        cpse.id: cpse
        for cpse in (
            db.query(CPSE).filter(CPSE.id.in_(cpse_ids)).all()
            if cpse_ids else []
        )
    }

    def material_data(material_id):
        material = material_by_id.get(material_id)
        if not material:
            return None
        cpse = cpse_by_id.get(material.cpse_id)
        return {
            "id": material.id,
            "material_code": material.material_code,
            "description": material.description,
            "category": material.category,
            "unit": material.unit,
            "specifications": material.specifications or {},
            "cpse_code": cpse.code if cpse else f"CPSE-{material.cpse_id}",
        }

    result["items"] = []
    for match in matches:
        mapped_national_ids = set().union(
            national_ids_by_material.get(match.material_a_id, set()),
            national_ids_by_material.get(match.material_b_id, set()),
        )
        mapping_state = (
            "CONFLICTING_MAPPINGS" if len(mapped_national_ids) > 1
            else "ALREADY_MAPPED" if mapped_national_ids else "UNMAPPED"
        )
        result["items"].append({
            "id": match.id,
            "final_score": match.final_score,
            "classification": match.classification,
            "semantic_score": match.semantic_score,
            "attribute_score": match.attribute_score,
            "fuzzy_score": match.fuzzy_score,
            "explanation": match.explanation,
            "status": match.status,
            "created_at": match.created_at,
            "material_a": material_data(match.material_a_id),
            "material_b": material_data(match.material_b_id),
            "canonical_proposal": propose_canonical([
                material_by_id[item_id] for item_id in (match.material_a_id, match.material_b_id)
                if item_id in material_by_id
            ]),
            "mapping_state": mapping_state,
            "approval_blocked": mapping_state != "UNMAPPED",
            "approval_block_reason": (
                "Source materials are already mapped to different National Material Codes"
                if mapping_state == "CONFLICTING_MAPPINGS"
                else "Source material is already mapped to a National Material Code"
                if mapping_state == "ALREADY_MAPPED" else None
            ),
        }
        )
    count_rows = db.query(
        MaterialMatch.status,
        func.count(MaterialMatch.id),
    ).group_by(MaterialMatch.status).all()
    counts = {"PENDING": 0, "APPROVED": 0, "REJECTED": 0}
    counts.update({row_status: count for row_status, count in count_rows})
    result["counts"] = counts
    classification_rows = db.query(
        MaterialMatch.classification,
        func.count(MaterialMatch.id),
    ).filter(
        MaterialMatch.status == status_key,
    ).group_by(MaterialMatch.classification).all()
    classification_counts = {key: 0 for key in allowed_classifications}
    classification_counts.update({key: count for key, count in classification_rows})
    result["classification_counts"] = classification_counts
    return result

@router.post("/{match_id}/approve")
@router.put("/{match_id}/approve")
def approve(
    match_id: int,
    payload: ApprovalRequest | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("approval.review")),
):
    match = db.get(MaterialMatch, match_id)
    if not match:
        raise HTTPException(404, "Match not found")
    if match.classification != "FUNCTIONAL_EQUIVALENT":
        # Identity decisions are deliberately cluster-only. Pair evidence remains
        # readable through recommendations and cluster detail, but cannot create
        # a National Material or legacy mapping from this legacy endpoint.
        raise HTTPException(410, "Pair identity approval is retired; review and approve the persisted cluster instead")
    return approve_match(
        db, match_id, reviewer_id=current_user.id,
        comment=payload.comment if payload else None,
        canonical_values=payload.canonical_values if payload else {},
        acknowledge_critical_conflicts=payload.acknowledge_critical_conflicts if payload else False,
        acknowledge_functional_equivalent=payload.acknowledge_functional_equivalent if payload else False,
    )

@router.post("/{match_id}/reject")
@router.put("/{match_id}/reject")
def reject(
    match_id: int,
    payload: ApprovalRequest | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("approval.review")),
):
    return reject_match(
        db, match_id, reviewer_id=current_user.id,
        comment=payload.comment if payload else None,
    )
