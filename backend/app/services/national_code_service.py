from app.models.national_material import NationalMaterial
from app.models.taxonomy_code import TaxonomyCode

CATEGORY_CODES = {
    "FASTENERS": "FST", "VALVES & ACTUATORS": "VLV", "PUMPS & COMPRESSORS": "PMP",
    "PIPES & FITTINGS": "PIP", "ELECTRICAL EQUIPMENT": "ELC",
    "BEARINGS & POWER TRANSMISSION": "BRG", "UNCLASSIFIED": "GEN",
}
SUBCATEGORY_CODES = {
    "BOLTS": "BLT", "NUTS": "NUT", "WASHERS": "WSH", "BALL VALVES": "BLV",
    "GATE VALVES": "GTV", "PUMPS": "PMP", "TRANSFORMERS": "TRF", "MOTORS": "MTR",
    "CABLES": "CBL", "BEARINGS": "BRG", "PIPES": "PIP", "FLANGES": "FLG",
}
SUBCATEGORY_PARENTS = {
    "BOLTS": "FASTENERS", "NUTS": "FASTENERS", "WASHERS": "FASTENERS",
    "BALL VALVES": "VALVES & ACTUATORS", "GATE VALVES": "VALVES & ACTUATORS",
    "PUMPS": "PUMPS & COMPRESSORS", "TRANSFORMERS": "ELECTRICAL EQUIPMENT",
    "MOTORS": "ELECTRICAL EQUIPMENT", "CABLES": "ELECTRICAL EQUIPMENT",
    "BEARINGS": "BEARINGS & POWER TRANSMISSION", "PIPES": "PIPES & FITTINGS",
    "FLANGES": "PIPES & FITTINGS",
}

_DAMM_TABLE = (
    (0, 3, 1, 7, 5, 9, 8, 6, 4, 2),
    (7, 0, 9, 2, 1, 5, 4, 8, 6, 3),
    (4, 2, 0, 6, 8, 7, 1, 3, 5, 9),
    (1, 7, 5, 0, 9, 8, 3, 4, 2, 6),
    (6, 1, 2, 3, 0, 4, 5, 9, 7, 8),
    (3, 6, 7, 4, 2, 0, 9, 5, 8, 1),
    (5, 8, 6, 9, 7, 2, 0, 1, 3, 4),
    (8, 9, 4, 5, 3, 6, 2, 0, 1, 7),
    (9, 4, 3, 8, 6, 1, 7, 2, 0, 5),
    (2, 5, 8, 1, 4, 3, 6, 7, 9, 0),
)

def _check_digit(value):
    interim = 0
    for char in value:
        for digit in f"{ord(char):03d}":
            interim = _DAMM_TABLE[interim][int(digit)]
    return str(interim)


def _check_digit_v1(value):
    return str(sum((index + 1) * ord(char) for index, char in enumerate(value)) % 10)


def validate_national_code(db, code):
    material = db.query(NationalMaterial).filter(
        NationalMaterial.national_code == code
    ).first()
    if not material or not code or "-" not in code:
        return {"valid": False, "scheme_version": None}
    body, supplied_digit = code.rsplit("-", 1)
    scheme = str(material.code_scheme_version or "1")
    expected = _check_digit(body) if scheme == "2" else _check_digit_v1(body)
    return {
        "valid": supplied_digit == expected,
        "scheme_version": scheme,
        "national_material_id": material.id,
    }


def _taxonomy_code(db, level, name, fallback):
    row = db.query(TaxonomyCode).filter(
        TaxonomyCode.level == level,
        TaxonomyCode.name == (name or "").upper(),
        TaxonomyCode.active.is_(True),
    ).first()
    return row.code if row else fallback

def create_national_material(
    db, description, category=None, unit=None, specifications=None, subcategory=None,
    provenance=None, actor_id=None, commit=True, return_created=False,
):
    from app.services.classification_service import classify_material
    supplied_category = (category or "").strip().upper()
    recognized_category = db.query(TaxonomyCode).filter(
        TaxonomyCode.level == "CATEGORY",
        TaxonomyCode.name == supplied_category,
        TaxonomyCode.active.is_(True),
    ).first() if supplied_category else None
    recognized_category_name = (
        recognized_category.name if recognized_category
        else supplied_category if supplied_category in CATEGORY_CODES
        else None
    )
    classification = classify_material(
        description,
        recognized_category_name,
        prefer_supplied=recognized_category_name is not None,
    )
    category = recognized_category_name or classification.category

    supplied_subcategory = (subcategory or "").strip().upper()
    compatible_subcategory = db.query(TaxonomyCode).filter(
        TaxonomyCode.level == "SUBCATEGORY",
        TaxonomyCode.name == supplied_subcategory,
        TaxonomyCode.parent_name == category,
        TaxonomyCode.active.is_(True),
    ).first() if supplied_subcategory else None
    classified_subcategory = db.query(TaxonomyCode).filter(
        TaxonomyCode.level == "SUBCATEGORY",
        TaxonomyCode.name == classification.subcategory,
        TaxonomyCode.parent_name == category,
        TaxonomyCode.active.is_(True),
    ).first()
    compatible_fallback = (
        supplied_subcategory
        if SUBCATEGORY_PARENTS.get(supplied_subcategory) == category else None
    )
    classified_fallback = (
        classification.subcategory
        if SUBCATEGORY_PARENTS.get(classification.subcategory) == category else None
    )
    subcategory = (
        compatible_subcategory.name if compatible_subcategory
        else compatible_fallback if compatible_fallback
        else classified_subcategory.name if classified_subcategory
        else classified_fallback if classified_fallback
        else "UNSPECIFIED"
    )
    # Serialize canonical creation so concurrent approvals cannot create two codes
    # for the same canonical content. SQLite tests serialize their own session.
    from app.services.cleaning_service import standardize_description, normalize_uom
    from app.services.conflict_resolution_service import canonical_specs, _normalized_engineering_value
    from types import SimpleNamespace
    import json
    import hashlib
    from sqlalchemy import text
    description = standardize_description(description)
    unit = normalize_uom(unit)
    specs = canonical_specs(SimpleNamespace(specifications=specifications or {}, description=description))
    normalized_specs = {key: _normalized_engineering_value(key, value) for key, value in specs.items()}
    identity = json.dumps([description, category, subcategory, unit, normalized_specs], sort_keys=True)
    if db.get_bind().dialect.name == "postgresql":
        lock = int.from_bytes(hashlib.sha256(identity.encode()).digest()[:8], "big", signed=True)
        db.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": lock})
    candidates = db.query(NationalMaterial).filter(NationalMaterial.category == category, NationalMaterial.status == "ACTIVE").all()
    for candidate in candidates:
        candidate_specs = {key: _normalized_engineering_value(key, value) for key, value in canonical_specs(candidate).items()}
        if (standardize_description(candidate.description), normalize_uom(candidate.unit), candidate.subcategory, candidate_specs) == (description, unit, subcategory, normalized_specs):
            return (candidate, False) if return_created else candidate
    obj = NationalMaterial(
        national_code=None,
        description=description,
        category=category,
        subcategory=subcategory,
        unit=unit,
        specifications=specs,
        provenance=provenance or {},
        code_scheme_version="2",
    )
    db.add(obj); db.flush()
    category_name = (category or "UNCLASSIFIED").upper()
    subcategory_name = (subcategory or "UNSPECIFIED").upper()
    category_code = _taxonomy_code(
        db, "CATEGORY", category_name, CATEGORY_CODES.get(category_name, "GEN")
    )
    subcategory_code = _taxonomy_code(
        db, "SUBCATEGORY", subcategory_name, SUBCATEGORY_CODES.get(subcategory_name, "GEN")
    )
    body = f"NMC-{category_code}-{subcategory_code}-{obj.id:06d}"
    obj.national_code = f"{body}-{_check_digit(body)}"
    if actor_id is not None:
        from app.services.audit_service import snapshot_model, write_audit
        write_audit(
            db,
            "NATIONAL_MATERIAL_CREATED",
            "NationalMaterial",
            obj.id,
            actor_id,
            {"after": snapshot_model(obj)},
            commit=False,
        )
    if commit:
        db.commit(); db.refresh(obj)
    return (obj, True) if return_created else obj
