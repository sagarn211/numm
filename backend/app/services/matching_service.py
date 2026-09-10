from app.models.material import Material
from app.models.material_match import MaterialMatch
from app.services.ai_service import match_batch
from app.config.settings import settings

ALLOWED_CLASSIFICATIONS = {
    "EXACT", "NEAR_DUPLICATE", "FUNCTIONAL_EQUIVALENT", "NO_MATCH",
}


def _score(value):
    try:
        score = float(value)
    except (TypeError, ValueError):
        return None
    return score if 0.0 <= score <= 1.0 else None


def _validated_match(item, material_ids):
    """Reject malformed or untrusted AI output before it reaches PostgreSQL."""
    a = item.get("material_a_id")
    b = item.get("material_b_id")
    if not isinstance(a, int) or not isinstance(b, int) or a == b:
        return None
    if a not in material_ids or b not in material_ids:
        return None
    components = item.get("components") or {}
    semantic = _score(components.get("semantic", item.get("semantic_score")))
    attribute = _score(components.get("attribute", item.get("attribute_score")))
    fuzzy = _score(components.get("fuzzy", item.get("fuzzy_score")))
    final = _score(item.get("match_score", item.get("final_score")))
    label = str(item.get("label", item.get("classification", "NO_MATCH"))).upper()
    if None in (semantic, attribute, fuzzy, final) or label not in ALLOWED_CLASSIFICATIONS:
        return None
    return min(a, b), max(a, b), semantic, attribute, fuzzy, final, label

def _payload(m):
    return {
        "id": m.id,
        "cpse_id": m.cpse_id,
        "material_code": m.material_code,
        "description": m.description,
        "cleaned_description": m.cleaned_description,
        "category": m.category,
        "unit": m.unit,
        "manufacturer": m.manufacturer,
        "model": m.model,
        "specifications": m.specifications or {},
    }

async def run_matching(db, focus_material_ids=None):
    materials = db.query(Material).filter(Material.status == "ACTIVE").all()
    if len(materials) < 2:
        return []
    focus = set(focus_material_ids or ())
    processing_materials = [material for material in materials if not focus or material.id in focus]
    for m in processing_materials:
        m.matching_status = "PROCESSING"
    db.commit()

    try:
        result = await match_batch([_payload(m) for m in materials], focus)
    except Exception:
        for m in processing_materials:
            m.matching_status = "FAILED"
        db.commit()
        raise

    created = []
    material_ids = {material.id for material in materials}
    seen_pairs = set()
    for item in result.get("matches", []):
        validated = _validated_match(item, material_ids)
        if not validated:
            continue
        a, b, semantic, attribute, fuzzy, final, label = validated
        if label == "NO_MATCH":
            continue
        if (a, b) in seen_pairs:
            continue
        seen_pairs.add((a, b))
        existing = db.query(MaterialMatch).filter(
            (
                ((MaterialMatch.material_a_id == a) & (MaterialMatch.material_b_id == b)) |
                ((MaterialMatch.material_a_id == b) & (MaterialMatch.material_b_id == a))
            ),
        ).first()
        if existing:
            # Rescore pending candidates after source corrections. Preserve reviewed
            # decisions and their original evidence for the audit trail.
            if existing.status == "PENDING":
                existing.semantic_score, existing.attribute_score = semantic, attribute
                existing.fuzzy_score, existing.final_score = fuzzy, final
                existing.classification = label
                existing.attributes_a = item.get("attributes_a")
                existing.attributes_b = item.get("attributes_b")
                existing.explanation = item.get("explanation")
                existing.model_name = item.get("model", item.get("model_name"))
                existing.matcher_version = item.get("matcher_version")
            continue
        obj = MaterialMatch(
            material_a_id=a,
            material_b_id=b,
            semantic_score=semantic,
            attribute_score=attribute,
            fuzzy_score=fuzzy,
            final_score=final,
            classification=label,
            attributes_a=item.get("attributes_a"),
            attributes_b=item.get("attributes_b"),
            explanation=item.get("explanation"),
            model_name=item.get("model", item.get("model_name")),
            matcher_version=item.get("matcher_version"),
        )
        db.add(obj); created.append(obj)

    for m in processing_materials:
        m.matching_status = "PROCESSED"
    db.commit()
    for obj in created:
        db.refresh(obj)
    if settings.AUTO_APPROVE_EXACT_MATCHES:
        from app.services.approval_service import auto_approve_exact_matches
        auto_approve_exact_matches(db, settings.AUTO_APPROVE_MIN_SCORE)
    return created
