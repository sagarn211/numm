import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import and_, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.models.cpse import CPSE
from app.models.material import Material
from app.models.material_match import MaterialMatch
from app.services.matching_service import run_matching
from app.services.ai_service import ai_evaluation, ai_health, find_candidates, match_pair, AIServiceUnavailable
from app.utils.pagination import paginate
from app.models.user import User
from app.utils.rbac import require_permission
from app.services.audit_service import write_audit
from app.services.cluster_governance_service import generate_proposed_clusters, get_clusters

router = APIRouter(prefix="/api/matching", tags=["AI Matching"])
logger = logging.getLogger(__name__)


class PairComparisonRequest(BaseModel):
    material_a_id: int
    material_b_id: int

@router.post("/run")
async def run(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("matching.run")),
):
    try:
        matches = await run_matching(db)
        # Discovery writes only new PROPOSED clusters; reviewed clusters are immutable
        # to matching recomputation and remain the source of truth.
        generate_proposed_clusters(db, current_user.id)
        write_audit(db, "AI_MATCHING_RUN", "MaterialMatch", None, current_user.id, {"recommendations_created": len(matches)})
        return matches
    except AIServiceUnavailable as exc:
        logger.warning("AI service unavailable during matching run: %s", exc)
        raise HTTPException(503, "AI service unavailable")


@router.post("/compare")
async def compare_selected_materials(
    payload: PairComparisonRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("matching.search")),
):
    """Expose the real pair verdict for the side-by-side comparison screen."""
    if payload.material_a_id == payload.material_b_id:
        raise HTTPException(400, "Choose two different materials")
    material_a = db.query(Material).filter(Material.id == payload.material_a_id).first()
    material_b = db.query(Material).filter(Material.id == payload.material_b_id).first()
    if not material_a or not material_b:
        raise HTTPException(404, "Material not found")
    try:
        return await match_pair(
            {
                "id": material_a.id,
                "description": material_a.description,
                "cleaned_description": material_a.cleaned_description,
                "category": material_a.category,
                "specifications": material_a.specifications or {},
            },
            {
                "id": material_b.id,
                "description": material_b.description,
                "cleaned_description": material_b.cleaned_description,
                "category": material_b.category,
                "specifications": material_b.specifications or {},
            },
        )
    except AIServiceUnavailable as exc:
        logger.warning("AI service unavailable during pair comparison: %s", exc)
        raise HTTPException(503, "AI service unavailable")

@router.get("")
def list_matches(
    status: str | None = None,
    classification: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("approval.read")),
):
    q = db.query(MaterialMatch)
    if status:
        q = q.filter(MaterialMatch.status == status.upper())
    if classification:
        q = q.filter(MaterialMatch.classification == classification.upper())
    return q.order_by(MaterialMatch.final_score.desc()).all()

@router.get("/recommendations")
def list_recommendations(
    status: str | None = "PENDING",
    classification: str | None = None,
    confidence: str | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("approval.read")),
):
    q = db.query(MaterialMatch)
    if status:
        q = q.filter(MaterialMatch.status == status.upper())
    if classification:
        q = q.filter(MaterialMatch.classification == classification.upper())

    confidence_key = confidence.upper() if confidence else None
    if confidence_key == "HIGH":
        q = q.filter(MaterialMatch.final_score >= 0.90)
    elif confidence_key == "MEDIUM":
        q = q.filter(
            MaterialMatch.final_score >= 0.70,
            MaterialMatch.final_score < 0.90,
        )
    elif confidence_key == "NEEDS_REVIEW":
        q = q.filter(MaterialMatch.final_score < 0.70)
    elif confidence_key not in (None, "ALL"):
        raise HTTPException(400, "Invalid confidence filter")

    result = paginate(
        q.order_by(MaterialMatch.final_score.desc(), MaterialMatch.id.desc()),
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
    cpse_ids = {material.cpse_id for material in materials}
    cpses = db.query(CPSE).filter(CPSE.id.in_(cpse_ids)).all() if cpse_ids else []
    cpse_by_id = {cpse.id: cpse for cpse in cpses}

    def material_data(material_id: int):
        material = material_by_id.get(material_id)
        if not material:
            return None
        cpse = cpse_by_id.get(material.cpse_id)
        return {
            "id": material.id,
            "material_code": material.material_code,
            "description": material.description,
            "specifications": material.specifications or {},
            "unit": material.unit,
            "category": material.category,
            "manufacturer": material.manufacturer,
            "cpse_id": material.cpse_id,
            "cpse_code": cpse.code if cpse else f"CPSE-{material.cpse_id}",
        }

    result["items"] = [
        {
            "id": match.id,
            "material_a_id": match.material_a_id,
            "material_b_id": match.material_b_id,
            "semantic_score": match.semantic_score,
            "attribute_score": match.attribute_score,
            "fuzzy_score": match.fuzzy_score,
            "final_score": match.final_score,
            "classification": match.classification,
            "explanation": match.explanation,
            "status": match.status,
            "material_a": material_data(match.material_a_id),
            "material_b": material_data(match.material_b_id),
        }
        for match in matches
    ]
    return result

@router.get("/health")
async def health(
    current_user: User = Depends(require_permission("matching.search")),
):
    return await ai_health()


@router.get("/clusters")
def clusters(
    status: str | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("approval.read")),
):
    """Deprecated read alias which now exposes only persisted clusters."""
    normalized = status.upper() if status else None
    if normalized == "PENDING": normalized = "PROPOSED"
    return get_clusters(db, normalized, page, limit)

@router.post("/clusters")
def create_cluster(payload: dict, db: Session = Depends(get_db), current_user: User = Depends(require_permission("approval.review"))):
    raise HTTPException(410, "Manual cluster creation is retired; generate evidence-backed persisted clusters at /api/clusters/generate")


@router.get("/evaluation")
async def evaluation(
    current_user: User = Depends(require_permission("matching.search")),
):
    try:
        return await ai_evaluation()
    except AIServiceUnavailable as exc:
        raise HTTPException(503, f"Model evaluation unavailable: {exc}") from exc

@router.get("/similar/{material_id}")
async def similar_materials(
    material_id: int,
    limit: int = Query(10, ge=1, le=25),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("matching.search")),
):
    source = db.query(Material).filter(Material.id == material_id).first()
    if not source:
        raise HTTPException(404, "Material not found")

    candidate_query = db.query(Material).filter(
        Material.id != source.id,
        Material.status == "ACTIVE",
    )
    if source.category:
        candidate_query = candidate_query.filter(Material.category == source.category)
    candidates = candidate_query.limit(limit * 20).all()

    def ai_payload(material):
        return {
            "id": material.id,
            "cpse_id": material.cpse_id,
            "material_code": material.material_code,
            "description": material.description,
            "cleaned_description": material.cleaned_description,
            "category": material.category,
            "unit": material.unit,
            "manufacturer": material.manufacturer,
            "model": material.model,
            "specifications": material.specifications or {},
        }

    try:
        matches = await find_candidates(
            ai_payload(source),
            [ai_payload(candidate) for candidate in candidates],
            top_k=limit,
        )
    except AIServiceUnavailable as exc:
        logger.warning("AI service unavailable during similarity search: %s", exc)
        raise HTTPException(503, "AI service unavailable")

    candidate_by_id = {candidate.id: candidate for candidate in candidates}
    matched_candidates = [
        candidate_by_id.get(match.get("material_b_id")) for match in matches
    ]
    cpse_ids = {source.cpse_id} | {
        candidate.cpse_id for candidate in matched_candidates if candidate
    }
    cpse_by_id = {
        cpse.id: cpse
        for cpse in db.query(CPSE).filter(CPSE.id.in_(cpse_ids)).all()
    }

    def material_data(material):
        cpse = cpse_by_id.get(material.cpse_id)
        return {
            "id": material.id,
            "material_code": material.material_code,
            "description": material.description,
            "specifications": material.specifications or {},
            "unit": material.unit,
            "category": material.category,
            "manufacturer": material.manufacturer,
            "model": material.model,
            "cpse_id": material.cpse_id,
            "cpse_code": cpse.code if cpse else f"CPSE-{material.cpse_id}",
        }

    items = []
    for match in matches:
        candidate = candidate_by_id.get(match.get("material_b_id"))
        if not candidate or match.get("label") == "NO_MATCH":
            continue
        items.append({**match, "material": material_data(candidate)})

    return {"source": material_data(source), "items": items, "total": len(items)}

@router.post("/similar/{material_id}/submit/{candidate_id}")
async def submit_similar_material(
    material_id: int,
    candidate_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("matching.submit")),
):
    if material_id == candidate_id:
        raise HTTPException(400, "A material cannot be matched with itself")

    source = db.query(Material).filter(Material.id == material_id).first()
    candidate = db.query(Material).filter(Material.id == candidate_id).first()
    if not source or not candidate:
        raise HTTPException(404, "Source or candidate material not found")
    if source.category and candidate.category and source.category != candidate.category:
        raise HTTPException(400, "Materials belong to different product categories")

    existing = db.query(MaterialMatch).filter(or_(
        and_(
            MaterialMatch.material_a_id == source.id,
            MaterialMatch.material_b_id == candidate.id,
        ),
        and_(
            MaterialMatch.material_a_id == candidate.id,
            MaterialMatch.material_b_id == source.id,
        ),
    )).first()
    if existing:
        return {"created": False, "match_id": existing.id, "status": existing.status}

    def ai_payload(material):
        return {
            "id": material.id,
            "cpse_id": material.cpse_id,
            "material_code": material.material_code,
            "description": material.description,
            "cleaned_description": material.cleaned_description,
            "category": material.category,
            "unit": material.unit,
            "manufacturer": material.manufacturer,
            "model": material.model,
            "specifications": material.specifications or {},
        }

    try:
        matches = await find_candidates(
            ai_payload(source),
            [ai_payload(candidate)],
            top_k=1,
        )
    except AIServiceUnavailable as exc:
        logger.warning("AI service unavailable during match submission: %s", exc)
        raise HTTPException(503, "AI service unavailable")
    if not matches or matches[0].get("label") == "NO_MATCH":
        raise HTTPException(400, "AI did not identify this pair as a valid match")

    result = matches[0]
    components = result.get("components") or {}
    material_a_id, material_b_id = sorted((source.id, candidate.id))
    attributes_a = result.get("attributes_a")
    attributes_b = result.get("attributes_b")
    if material_a_id != source.id:
        attributes_a, attributes_b = attributes_b, attributes_a
    match = MaterialMatch(
        material_a_id=material_a_id,
        material_b_id=material_b_id,
        semantic_score=components.get("semantic"),
        attribute_score=components.get("attribute"),
        fuzzy_score=components.get("fuzzy"),
        final_score=float(result.get("match_score", 0) or 0),
        classification=str(result.get("label", "NEAR_DUPLICATE")).upper(),
        attributes_a=attributes_a,
        attributes_b=attributes_b,
        explanation=result.get("explanation"),
        model_name=result.get("model"),
        matcher_version=result.get("matcher_version"),
        status="PENDING",
        submitted_by=current_user.id,
    )
    db.add(match)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = db.query(MaterialMatch).filter(
            MaterialMatch.material_a_id == material_a_id,
            MaterialMatch.material_b_id == material_b_id,
        ).first()
        if existing:
            return {"created": False, "match_id": existing.id, "status": existing.status}
        raise
    db.refresh(match)
    write_audit(db, "MATCH_SUBMITTED_FOR_REVIEW", "MaterialMatch", match.id, current_user.id, {
        "material_a_id": material_a_id, "material_b_id": material_b_id,
        "classification": match.classification, "score": match.final_score,
    })
    db.refresh(match)
    return {"created": True, "match_id": match.id, "status": match.status}

@router.get("/{match_id}")
def get_one(
    match_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("approval.read", "matching.search")),
):
    obj = db.query(MaterialMatch).filter(MaterialMatch.id == match_id).first()
    if not obj:
        raise HTTPException(404, "Match not found")
    return obj
