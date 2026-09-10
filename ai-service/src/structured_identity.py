"""Structured evidence is checked independently of description similarity."""
import re

ALIASES = {"grade": "material_grade", "uom": "unit", "model": "part_number", "rated_voltage": "voltage"}
UNITS = {"KV": (1000, "V"), "V": (1, "V"), "KW": (1000, "W"), "W": (1, "W"),
         "MM": (1, "MM"), "CM": (10, "MM"), "IN": (25.4, "MM"),
         "BAR": (1, "BAR"), "MPA": (10, "BAR"), "KPA": (.01, "BAR")}
CRITICAL = {"material_grade", "part_number", "voltage", "power", "pressure", "pressure_class",
            "pressure_rating", "diameter", "length", "size", "nominal_size", "nominal_diameter",
            "capacity", "unit", "material_type", "phase", "frequency", "rpm", "frame",
            "bearing_designation", "bore", "outer_diameter", "width", "flow", "head", "schedule"}


def value_key(value):
    text = re.sub(r"\s+", " ", str(value).strip().upper())
    text = re.sub(r"\bSS\s*(\d{3})\b", r"STAINLESS STEEL \1", text)
    if text in {"PCS", "PC", "NOS", "EACH", "PIECE", "PIECES"}:
        return "EA"
    match = re.fullmatch(r"(\d+(?:\.\d+)?)\s*([A-Z]+)", text)
    if match and match[2] in UNITS:
        factor, unit = UNITS[match[2]]
        return f"{float(match[1]) * factor:.6f} {unit}"
    return text


def attributes(material):
    result = {}
    specs = material.get("specifications") or {}
    if isinstance(specs, dict):
        for name, value in specs.items():
            key = re.sub(r"[^a-z0-9]+", "_", str(name).lower()).strip("_")
            if value is not None and str(value).strip():
                result[ALIASES.get(key, key)] = value_key(value)
    for field, key in (("unit", "unit"), ("model", "part_number")):
        if material.get(field):
            result.setdefault(key, value_key(material[field]))
    return result


def matching_text(material):
    description = material.get("cleaned_description") or material.get("description") or ""
    return description + " " + " ".join(f"{key.replace('_', ' ')} {value}" for key, value in sorted(attributes(material).items()))


def enforce_structured_evidence(result, left, right):
    a, b = attributes(left), attributes(right)
    conflicts = [key for key in sorted(a.keys() & b.keys() & CRITICAL) if a[key] != b[key]]
    result = dict(result)
    result["attributes_a"] = {**(result.get("attributes_a") or {}), **a}
    result["attributes_b"] = {**(result.get("attributes_b") or {}), **b}
    if conflicts:
        result.update(label="No-Match", match_score=min(float(result.get("match_score", 0)), .59),
                      explanation="Conflicting structured attributes: " + "; ".join(f"{key}: {a[key]} vs {b[key]}" for key in conflicts))
    elif (a.keys() ^ b.keys()) & CRITICAL and result.get("label") == "Exact":
        result.update(label="Near-Duplicate", match_score=min(float(result["match_score"]), .94),
                      explanation="Missing structured evidence on one record; manual review required. " + result.get("explanation", ""))
    return result
