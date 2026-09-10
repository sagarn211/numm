import re
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class ClassificationResult:
    category: str
    subcategory: str
    confidence: float
    source: str = "RULE_ENGINE"
    rule_version: str = "2026.09"

    def to_dict(self):
        return asdict(self)


TAXONOMY = (
    ("ELECTRICAL EQUIPMENT", "LIGHTING", (r"\bLAMP\b", r"\bLIGHT\b", r"\bLUMINAIRE\b")),
    ("ELECTRICAL EQUIPMENT", "SWITCHGEAR", (r"\bMCB\b", r"\bMCCB\b", r"\bCONTACTOR\b", r"\bBREAKER\b")),
    ("ELECTRICAL EQUIPMENT", "CABLE ACCESSORIES", (r"\bCABLE\s+GLAND\b", r"\bCABLE\s+LUG\b")),
    ("BEARINGS & POWER TRANSMISSION", "TRANSMISSION", (r"\bGEARBOX\b", r"\bSPROCKET\b", r"\bPULLEY\b")),
    ("PIPES & FITTINGS", "SEALS", (r"\bGASKET\b", r"\bSEAL\b", r"\bO[ -]?RING\b")),
    ("FASTENERS", "BOLTS", (r"\bBOLT\b", r"\bSTUD\b")),
    ("FASTENERS", "NUTS", (r"\bNUT\b",)),
    ("FASTENERS", "WASHERS", (r"\bWASHER\b",)),
    ("VALVES & ACTUATORS", "BALL VALVES", (r"\bBALL\s+VALVE\b",)),
    ("VALVES & ACTUATORS", "GATE VALVES", (r"\bGATE\s+VALVE\b",)),
    ("VALVES & ACTUATORS", "GENERAL VALVES", (r"\bVALVE\b", r"\bACTUATOR\b")),
    ("PUMPS & COMPRESSORS", "PUMPS", (r"\bPUMP\b",)),
    ("PUMPS & COMPRESSORS", "COMPRESSORS", (r"\bCOMPRESSOR\b",)),
    ("PIPES & FITTINGS", "PIPES", (r"\bPIPE\b", r"\bTUBE\b")),
    ("PIPES & FITTINGS", "FLANGES", (r"\bFLANGE\b",)),
    ("PIPES & FITTINGS", "FITTINGS", (r"\bELBOW\b", r"\bTEE\b", r"\bCOUPLING\b")),
    ("ELECTRICAL EQUIPMENT", "TRANSFORMERS", (r"\bTRANSFORMER\b",)),
    ("ELECTRICAL EQUIPMENT", "MOTORS", (r"\bMOTOR\b",)),
    ("ELECTRICAL EQUIPMENT", "CABLES", (r"\bCABLE\b", r"\bWIRE\b")),
    ("BEARINGS & POWER TRANSMISSION", "BEARINGS", (r"\bBEARING\b",)),
)


def _attribute_text(attributes: dict | None) -> str:
    if not isinstance(attributes, dict):
        return ""
    return " ".join(
        f"{key} {value}" for key, value in attributes.items()
        if value is not None and str(value).strip()
    )


def classify_material(
    description: str | None,
    supplied_category: str | None = None,
    attributes: dict | None = None,
    prefer_supplied: bool = False,
) -> ClassificationResult:
    supplied = (supplied_category or "").strip().upper()
    text = re.sub(
        r"\s+", " ", f"{description or ''} {_attribute_text(attributes)}".upper()
    ).strip()
    if prefer_supplied and supplied:
        subcategory = "UNSPECIFIED"
        for category, candidate_subcategory, patterns in TAXONOMY:
            if category == supplied and any(re.search(pattern, text) for pattern in patterns):
                subcategory = candidate_subcategory
                break
        return ClassificationResult(supplied, subcategory, 1.0, "MANUAL_REVIEW")
    for category, subcategory, patterns in TAXONOMY:
        if any(re.search(pattern, text) for pattern in patterns):
            hits = sum(bool(re.search(pattern, text)) for pattern in patterns)
            confidence = min(0.99, 0.88 + (hits - 1) * 0.04)
            return ClassificationResult(category, subcategory, confidence)
    if supplied:
        return ClassificationResult(supplied, "UNSPECIFIED", 0.65, "SUPPLIED")
    return ClassificationResult("UNCLASSIFIED", "UNCLASSIFIED", 0.0)


def backfill_classifications(db, cpse_id=None, actor_id=None):
    from app.models.material import Material
    from app.services.audit_service import write_audit
    query = db.query(Material)
    if cpse_id is not None:
        query = query.filter(Material.cpse_id == cpse_id)
    updated = 0
    for material in query.all():
        before = {
            "category": material.category,
            "subcategory": material.subcategory,
            "classification_confidence": material.classification_confidence,
            "classification_source": material.classification_source,
        }
        result = classify_material(material.cleaned_description or material.description, material.category)
        material.category = result.category
        material.subcategory = result.subcategory
        material.classification_confidence = result.confidence
        material.classification_source = result.source
        material.classification_version = result.rule_version
        after = {
            "category": material.category,
            "subcategory": material.subcategory,
            "classification_confidence": material.classification_confidence,
            "classification_source": material.classification_source,
        }
        if before != after:
            write_audit(db, "MATERIAL_CATEGORY_RECLASSIFIED", "Material", material.id, actor_id, {
                "before": before, "after": after,
            }, commit=False)
            updated += 1
    return updated
