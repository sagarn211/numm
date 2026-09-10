from dataclasses import asdict, dataclass
import re


CRITICAL_FIELDS = {"material_grade", "grade", "pressure", "rating", "voltage", "size", "diameter", "length", "width", "height", "nominal_size", "pressure_class", "power", "capacity", "part_number", "material_type"}
RECOGNIZED_STANDARDS = ("ISO", "BIS", "IS ", "ASTM", "API")
LENGTH_FACTORS_MM = {"MM": 1.0, "CM": 10.0, "M": 1000.0, "IN": 25.4, "INCH": 25.4, "INCHES": 25.4}
PRESSURE_FACTORS_BAR = {"BAR": 1.0, "KPA": 0.01, "MPA": 10.0, "PSI": 0.0689476}
FIELD_ALIASES = {"grade": "material_grade", "rated_voltage": "voltage", "model_number": "part_number"}


def canonical_specs(material):
    result = {}
    for field, value in (material.specifications or {}).items():
        key = re.sub(r"[^a-z0-9]+", "_", str(field).strip().lower()).strip("_")
        key = FIELD_ALIASES.get(key, key)
        if key in result and _normalized_engineering_value(key, result[key]) != _normalized_engineering_value(key, value):
            # Retain contradictory source aliases so they cannot silently overwrite evidence.
            result[key] = f"CONFLICT: {result[key]} / {value}"
        else:
            result[key] = value
    if getattr(material, "model", None):
        result.setdefault("part_number", material.model)
    # Extract only explicit text evidence; never invent missing ratings or grades.
    description = str(getattr(material, "description", "") or "").upper()
    patterns = {
        "material_grade": r"\b(?:SS\s*|STAINLESS STEEL\s*)(30[4-9]|31[0-9])\b",
        "diameter": r"\b(M\d{1,3})\s*(?:X|\b)",
        "length": r"\bM\d{1,3}\s*X\s*(\d+(?:\.\d+)?)\s*(?:MM)?\b",
        "voltage": r"\b(\d+(?:\.\d+)?\s*K?V)\b",
        "power": r"\b(\d+(?:\.\d+)?\s*K?W)\b",
    }
    for key, pattern in patterns.items():
        match = re.search(pattern, description)
        if match:
            value = match[1]
            if key == "material_grade": value = "SS" + value
            if key == "length": value += " MM"
            if key in result and _normalized_engineering_value(key, result[key]) != _normalized_engineering_value(key, value):
                result[key] = f"CONFLICT: {result[key]} / {value}"
            else:
                result.setdefault(key, value)
    return result


@dataclass(frozen=True)
class CanonicalConflict:
    field: str
    values: list
    requires_review: bool


def _meaningful(value):
    return value is not None and str(value).strip() != ""


def _standard_score(material):
    text = " ".join([
        material.description or "",
        material.cleaned_description or "",
        " ".join(str(value) for value in (material.specifications or {}).values()),
    ]).upper()
    return sum(token in text for token in RECOGNIZED_STANDARDS)


def _normalized_engineering_value(field, value):
    text = re.sub(r"\s+", " ", str(value).strip().upper())
    text = re.sub(r"\bSS\s*(\d{3})\b", r"STAINLESS STEEL \1", text)
    electrical = re.fullmatch(r"(\d+(?:\.\d+)?)\s*(KV|V|KW|W)", text)
    if electrical and field.lower() in {"voltage", "power"}:
        factor = 1000 if electrical[2].startswith("K") else 1
        return f"{float(electrical[1]) * factor:.6f} {electrical[2][-1]}"
    match = re.fullmatch(r"(-?\d+(?:\.\d+)?)\s*(MM|CM|M|IN|INCH|INCHES|BAR|KPA|MPA|PSI)", text)
    if not match:
        return text
    number, unit = float(match.group(1)), match.group(2)
    if field.lower() in {"size", "diameter", "length", "width", "height"} and unit in LENGTH_FACTORS_MM:
        return f"{number * LENGTH_FACTORS_MM[unit]:.6f} MM"
    if field.lower() in {"pressure", "rating"} and unit in PRESSURE_FACTORS_BAR:
        return f"{number * PRESSURE_FACTORS_BAR[unit]:.6f} BAR"
    return text


def _source_record(material):
    return {
        "material_id": material.id,
        "cpse_id": getattr(material, "cpse_id", None),
        "material_code": getattr(material, "material_code", None),
        "description": material.description,
        "category": material.category,
        "subcategory": getattr(material, "subcategory", None),
        "unit": material.unit,
        "specifications": material.specifications or {},
    }


def propose_canonical(materials, resolutions: dict | None = None):
    resolutions = {
        FIELD_ALIASES.get(str(key).lower(), str(key).lower()): value for key, value in (resolutions or {}).items()
    }
    if not materials:
        return {
            "description": "",
            "category": None,
            "subcategory": None,
            "unit": None,
            "specifications": {},
            "conflicts": [],
            "source_material_ids": [],
            "source_records": [],
        }

    ranked = sorted(
        materials,
        key=lambda item: (
            _standard_score(item),
            len(item.specifications or {}),
            bool(item.category),
            len(item.cleaned_description or item.description or ""),
        ),
        reverse=True,
    )
    source = ranked[0]
    fields = set().union(*(set(canonical_specs(item)) for item in materials))
    specs = {}
    conflicts = []
    for field in sorted(fields):
        values = []
        normalized_values = set()
        for item in materials:
            value = canonical_specs(item).get(field)
            normalized = _normalized_engineering_value(field, value) if _meaningful(value) else None
            if _meaningful(value) and normalized not in normalized_values:
                values.append(value)
                normalized_values.add(normalized)
        if field.lower() in resolutions:
            specs[field] = resolutions[field.lower()]
        elif values:
            specs[field] = values[0]
        if len(values) > 1:
            conflicts.append(asdict(CanonicalConflict(field, values, field.lower() in CRITICAL_FIELDS)))

    return {
        "description": resolutions.get("description") or source.cleaned_description or source.description,
        "category": resolutions.get("category") or source.category,
        "subcategory": resolutions.get("subcategory") or getattr(source, "subcategory", None),
        "unit": resolutions.get("unit") or source.unit,
        "specifications": specs,
        "conflicts": conflicts,
        "source_material_ids": [item.id for item in materials],
        "source_records": [_source_record(item) for item in materials],
    }


def unresolved_critical_conflicts(proposal, resolutions: dict | None = None):
    resolved = {FIELD_ALIASES.get(str(key).lower(), str(key).lower()) for key, value in (resolutions or {}).items() if _meaningful(value)}
    return [
        item for item in proposal.get("conflicts", [])
        if item["requires_review"] and item["field"].lower() not in resolved
    ]
