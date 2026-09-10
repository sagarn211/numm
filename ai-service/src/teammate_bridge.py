"""Adapter from NUMM material payloads to the teammate AI implementation."""

from __future__ import annotations

from collections import defaultdict
from src.structured_identity import matching_text, enforce_structured_evidence
import logging
from pathlib import Path
import sys

from app.config import MATCHER_VERSION, MAX_CANDIDATES_PER_MATERIAL, MODEL_NAME, MODEL_PATH, MODEL_VERSION, TEAMMATE_AI_SRC

# Reuse Uvicorn's configured stderr handler so runtime engine state is visible
# through `docker compose logs ai-service`.
logger = logging.getLogger("uvicorn.error")

_pipeline = None
_load_error: Exception | None = None
_faiss_vectors_indexed = 0
_last_faiss_top_k: list[dict] = []
_faiss_verified = False

LABEL_MAP = {
    "Exact": "EXACT",
    "Near-Duplicate": "NEAR_DUPLICATE",
    "Functional-Equivalent": "FUNCTIONAL_EQUIVALENT",
    "No-Match": "NO_MATCH",
}


def _description(material: dict) -> str:
    return matching_text(material)


def _load_pipeline():
    """Load real teammate modules once, including their model singleton."""
    global _pipeline, _load_error, _faiss_verified
    if _pipeline is not None:
        return _pipeline
    if _load_error is not None:
        raise RuntimeError("Teammate AI previously failed to initialize") from _load_error

    source = Path(TEAMMATE_AI_SRC)
    if not source.is_dir():
        _load_error = FileNotFoundError(f"Teammate AI source directory not found: {source}")
        logger.error("AI engine: TEAMMATE_REAL initialization failed: %s", _load_error)
        raise _load_error

    try:
        source_text = str(source)
        if source_text not in sys.path:
            sys.path.insert(0, source_text)

        # Import the teammate's real modules without rewriting them.
        from normalize import normalize
        from embed_and_retrieve import build_faiss_index, embed_texts, find_top_k_matches, get_model
        from scorer import match_materials
        import faiss

        model = get_model()
        probe = embed_texts(["NUMM HEALTH PROBE"])
        probe_index = faiss.IndexFlatIP(probe.shape[1])
        probe_index.add(probe.astype("float32"))
        probe_scores, probe_ids = probe_index.search(probe.astype("float32"), 1)
        _faiss_verified = int(probe_ids[0][0]) == 0 and float(probe_scores[0][0]) > 0.99
        if not _faiss_verified:
            raise RuntimeError("FAISS runtime probe failed")
        _pipeline = {
            "normalize": normalize,
            "embed_texts": embed_texts,
            "build_faiss_index": build_faiss_index,
            "find_top_k_matches": find_top_k_matches,
            "match_materials": match_materials,
            "model": model,
        }
        logger.info("AI engine: TEAMMATE_REAL - SentenceTransformer loaded: %s", MODEL_NAME)
        return _pipeline
    except Exception as exc:
        _load_error = exc
        logger.exception("AI engine: TEAMMATE_REAL initialization failed: %s", exc)
        raise


def initialize() -> bool:
    try:
        _load_pipeline()
        return True
    except Exception:
        return False


def engine_health() -> dict:
    if _pipeline is None and not initialize():
        return {
            "status": "degraded",
            "engine": "FALLBACK",
            "model_loaded": False,
            "model": None,
            "model_version": MODEL_VERSION,
            "embedding_dimension": None,
            "faiss": False,
            "fallback_reason": str(_load_error) if _load_error else "Unknown initialization failure",
        }
    return {
        "status": "ok",
        "engine": "TEAMMATE_REAL",
        "model_loaded": True,
        "model": MODEL_NAME,
        "model_version": MODEL_VERSION,
        "faiss": _faiss_verified,
        "matcher_version": MATCHER_VERSION,
        "model_path": MODEL_PATH,
        "embedding_dimension": _pipeline["model"].get_sentence_embedding_dimension(),
        "fallback_reason": None,
    }


def runtime_evidence() -> dict:
    return {
        "embedding_dimension": (
            _pipeline["model"].get_sentence_embedding_dimension() if _pipeline else None
        ),
        "faiss_vectors_indexed": _faiss_vectors_indexed,
        "last_faiss_top_k": list(_last_faiss_top_k),
    }


def _bounded(value) -> float:
    try:
        return round(min(1.0, max(0.0, float(value))), 4)
    except (TypeError, ValueError):
        return 0.0


def _score_pair(material_a: dict, material_b: dict) -> dict:
    pipeline = _load_pipeline()
    result = pipeline["match_materials"](_description(material_a), _description(material_b))
    result = enforce_structured_evidence(result, material_a, material_b)
    components = result.get("components") or {}
    semantic = _bounded(components.get("semantic"))
    attribute = _bounded(components.get("attribute"))
    fuzzy = _bounded(components.get("fuzzy"))
    final = _bounded(result.get("match_score"))
    label = LABEL_MAP.get(result.get("label"), "NO_MATCH")
    return {
        "material_a_id": material_a["id"],
        "material_b_id": material_b["id"],
        "match_score": final,
        "final_score": final,
        "label": label,
        "classification": label,
        "components": {"semantic": semantic, "attribute": attribute, "fuzzy": fuzzy},
        "semantic_score": semantic,
        "attribute_score": attribute,
        "fuzzy_score": fuzzy,
        "attributes_a": result.get("attributes_a") or {},
        "attributes_b": result.get("attributes_b") or {},
        "explanation": result.get("explanation") or "",
        "model": MODEL_NAME,
        "model_name": MODEL_NAME,
        "matcher_version": MATCHER_VERSION,
    }


def match_pair(material_a: dict, material_b: dict) -> dict | None:
    try:
        return _score_pair(material_a, material_b)
    except Exception as exc:
        logger.exception("AI engine: TEAMMATE_REAL pair matching failed: %s", exc)
        return None


def match_batch(materials: list[dict], focus_material_ids=None) -> list[dict] | None:
    """Use teammate FAISS retrieval before its hybrid scorer for each pair."""
    global _faiss_vectors_indexed, _last_faiss_top_k
    if len(materials) < 2:
        return []
    try:
        pipeline = _load_pipeline()
        normalized = [pipeline["normalize"](_description(material)) for material in materials]
        embeddings = pipeline["embed_texts"](normalized)
        index = pipeline["build_faiss_index"](embeddings)
        _faiss_vectors_indexed = int(index.ntotal)

        seen_pairs: set[tuple[int, int]] = set()
        degree = defaultdict(int)
        scored: list[dict] = []
        _last_faiss_top_k = []
        focus = set(focus_material_ids or ())
        positions = [
            position for position, material in enumerate(materials)
            if not focus or int(material["id"]) in focus
        ]
        for position in positions:
            material_a = materials[position]
            # Search the one batch index instead of rebuilding and re-embedding a
            # candidate index for every material.
            requested = min(MAX_CANDIDATES_PER_MATERIAL + 1, len(materials))
            scores, indexes = index.search(embeddings[position:position + 1], requested)
            retrieved = [
                (int(candidate_position), float(score))
                for candidate_position, score in zip(indexes[0], scores[0])
                if int(candidate_position) != position
            ][:MAX_CANDIDATES_PER_MATERIAL]
            _last_faiss_top_k.append({
                "material_id": material_a["id"],
                "candidates": [
                    {"material_id": materials[idx]["id"], "score": round(score, 4)}
                    for idx, score in retrieved
                ],
            })
            for retrieved_index, _score in retrieved:
                material_b = materials[retrieved_index]
                left_id, right_id = sorted((int(material_a["id"]), int(material_b["id"])))
                if (left_id, right_id) in seen_pairs:
                    continue
                degree_ids = [value for value in (left_id, right_id) if value in focus] if focus else [left_id, right_id]
                if any(degree[value] >= MAX_CANDIDATES_PER_MATERIAL for value in degree_ids):
                    continue
                seen_pairs.add((left_id, right_id))
                left = material_a if int(material_a["id"]) == left_id else material_b
                right = material_b if int(material_b["id"]) == right_id else material_a
                result = _score_pair(left, right)
                if result["label"] != "NO_MATCH":
                    scored.append(result)
                    for value in degree_ids:
                        degree[value] += 1

        logger.info(
            "AI engine: TEAMMATE_REAL - FAISS HNSW inner-product index contains %d vectors; scored %d candidate pairs",
            _faiss_vectors_indexed, len(scored),
        )
        if _last_faiss_top_k:
            logger.info(
                "AI engine: TEAMMATE_REAL - FAISS top-%d result: %s",
                MAX_CANDIDATES_PER_MATERIAL,
                _last_faiss_top_k[0],
            )
        return sorted(scored, key=lambda item: item["match_score"], reverse=True)
    except Exception as exc:
        logger.exception("AI engine: TEAMMATE_REAL batch matching failed: %s", exc)
        return None
