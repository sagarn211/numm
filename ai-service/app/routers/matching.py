from fastapi import APIRouter
from app.schemas import MatchBatchRequest, PairMatchRequest, CandidateRequest
from app.engine_adapter import run_batch, run_pair

router = APIRouter(prefix="/api/v1", tags=["Matching"])

@router.post("/match-batch")
def match_batch(payload: MatchBatchRequest):
    materials = [m.model_dump() for m in payload.materials]
    return {"matches": run_batch(materials, set(payload.focus_material_ids))}

@router.post("/match")
def match_pair(payload: PairMatchRequest):
    return run_pair(payload.material_a.model_dump(), payload.material_b.model_dump())

@router.post("/candidates")
def candidates(payload: CandidateRequest):
    source = payload.material.model_dump()
    results = [
        run_pair(source, candidate.model_dump())
        for candidate in payload.candidates
    ]
    results = [result for result in results if result["label"] != "NO_MATCH"]
    results.sort(key=lambda x: x["match_score"], reverse=True)
    return {"matches": results[:max(1, payload.top_k)]}
