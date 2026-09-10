from collections import defaultdict
from itertools import combinations
import logging

from rapidfuzz.fuzz import token_set_ratio

from app.config import (
    AI_ENGINE_REQUIRED,
    ALLOW_FALLBACK,
    CANDIDATE_MIN_SIMILARITY,
    MATCHER_VERSION,
    MAX_CANDIDATES_PER_MATERIAL,
    MODEL_NAME,
)
from src.fallback_matcher import attributes, compare, normalize
from src.teammate_bridge import (
    engine_health as teammate_engine_health,
    initialize as initialize_teammate_engine,
    match_batch as teammate_match_batch,
    match_pair as teammate_match_pair,
    runtime_evidence as teammate_runtime_evidence,
)

logger = logging.getLogger("uvicorn.error")

def engine_health():
    return {**teammate_engine_health(), **teammate_runtime_evidence()}


def log_engine_startup():
    if not initialize_teammate_engine():
        if AI_ENGINE_REQUIRED or not ALLOW_FALLBACK:
            raise RuntimeError("The real teammate AI engine is required but failed to initialize")
        logger.warning(
            "AI engine: FALLBACK - teammate AI is unavailable; "
            "using fallback lexical/attribute matcher"
        )

GENERIC_TOKENS = {
    "ASSEMBLY", "DUTY", "EQUIPMENT", "HEAVY", "INDUSTRIAL", "MATERIAL",
    "PART", "SPARE", "STANDARD", "STEEL", "TYPE",
}

def _decorate(item):
    item = dict(item)
    # The fallback matcher calls this value match_score; the stable NUMM
    # pair-match API also guarantees final_score to all backend consumers.
    if item.get("final_score") is None:
        item["final_score"] = item.get("match_score") or 0.0
    if item.get("classification") is None:
        item["classification"] = item.get("label") or "NO_MATCH"
    item.setdefault("model", MODEL_NAME)
    item.setdefault("matcher_version", MATCHER_VERSION)
    return item

def _category(material):
    return normalize(material.get("category") or "")

def _description(material):
    return normalize(
        material.get("cleaned_description") or material.get("description") or ""
    )

def _fallback_tokens(description):
    return {
        token for token in description.split()
        if len(token) >= 4 and token not in GENERIC_TOKENS and not token.isdigit()
    }

def select_candidate_pairs(
    materials,
    max_candidates=MAX_CANDIDATES_PER_MATERIAL,
    min_similarity=CANDIDATE_MIN_SIMILARITY,
):
    """Return a bounded set of plausible, unique material pairs.

    Blocking by engineering type/category prevents unrelated material families from
    reaching the full matcher. A lightweight lexical score then ranks candidates,
    while the per-material degree cap prevents quadratic recommendation growth.
    """
    if max_candidates < 1:
        return []

    descriptions = [_description(material) for material in materials]
    extracted = [attributes(description) for description in descriptions]
    categories = [_category(material) for material in materials]
    blocks = defaultdict(list)

    for index, description in enumerate(descriptions):
        material_type = extracted[index].get("material_type")
        category = categories[index]
        if material_type:
            blocks[("type", material_type)].append(index)
        if category:
            blocks[("category", category)].append(index)
        if not material_type and not category:
            for token in _fallback_tokens(description):
                blocks[("token", token)].append(index)

    possible_pairs = set()
    for indexes in blocks.values():
        possible_pairs.update(combinations(sorted(set(indexes)), 2))

    ranked = []
    for left, right in possible_pairs:
        left_type = extracted[left].get("material_type")
        right_type = extracted[right].get("material_type")
        if left_type and right_type and left_type != right_type:
            continue

        same_type = left_type and left_type == right_type
        if categories[left] and categories[right] and categories[left] != categories[right] and not same_type:
            continue

        similarity = token_set_ratio(descriptions[left], descriptions[right]) / 100.0
        if similarity < min_similarity:
            continue
        ranked.append((similarity, left, right))

    ranked.sort(
        key=lambda item: (
            -item[0],
            materials[item[1]].get("id", item[1]),
            materials[item[2]].get("id", item[2]),
        )
    )
    degree = defaultdict(int)
    selected = []
    for _, left, right in ranked:
        if degree[left] >= max_candidates or degree[right] >= max_candidates:
            continue
        selected.append((materials[left], materials[right]))
        degree[left] += 1
        degree[right] += 1
    return selected

def run_batch(materials, focus_material_ids=None):
    teammate_results = teammate_match_batch(materials, focus_material_ids)
    if teammate_results is not None:
        return [_decorate(x) for x in teammate_results]

    if not ALLOW_FALLBACK:
        raise RuntimeError("Real AI matching failed and fallback is disabled")

    logger.warning(
        "AI engine: FALLBACK - teammate_bridge.match_batch returned None; "
        "using fallback lexical/attribute matcher"
    )

    matches = []
    for material_a, material_b in select_candidate_pairs(materials):
        if focus_material_ids and material_a.get("id") not in focus_material_ids and material_b.get("id") not in focus_material_ids:
            continue
        result = compare(material_a, material_b)
        if result["label"] != "NO_MATCH":
            matches.append(_decorate(result))

    matches.sort(key=lambda x: x["match_score"], reverse=True)
    return matches

def run_pair(a, b):
    teammate_result = teammate_match_pair(a, b)
    if teammate_result is not None:
        return _decorate(teammate_result)
    if not ALLOW_FALLBACK:
        raise RuntimeError("Real AI pair matching failed and fallback is disabled")
    logger.warning("AI engine: FALLBACK - using fallback lexical/attribute matcher")
    return _decorate(compare(a, b))
