import re
from rapidfuzz.fuzz import ratio

TYPE_WORDS = {
    "BOLT", "NUT", "WASHER", "SCREW", "VALVE", "BEARING",
    "PIPE", "FLANGE", "CABLE", "MOTOR", "PUMP", "TRANSFORMER"
}

# Deterministic primary-family priority. Connection terms such as FLANGED must
# not override the actual equipment family (for example, BALL VALVE).
TYPE_PRIORITY = (
    "VALVE", "PUMP", "MOTOR", "TRANSFORMER", "BEARING", "CABLE",
    "PIPE", "BOLT", "NUT", "WASHER", "SCREW", "FLANGE",
)

MATERIAL_GRADES = [
    "SS304", "SS 304", "STAINLESS STEEL 304",
    "SS316", "SS 316", "STAINLESS STEEL 316",
    "MS", "MILD STEEL", "CS", "CARBON STEEL",
]

ABBREVIATIONS = {
    "HEX": "HEXAGONAL",
    "SS": "STAINLESS STEEL",
    "MS": "MILD STEEL",
    "CS": "CARBON STEEL",
    "GI": "GALVANIZED IRON",
    "DIA": "DIAMETER",
}

def normalize(text: str) -> str:
    text = (text or "").upper().strip()
    text = text.replace("*", " X ")
    text = re.sub(r"(?<=\d)MM\b", " MM", text)
    # Treat X as a dimension separator only when at least one adjacent
    # component is numeric; do not split words such as HEX or EXPANSION.
    text = re.sub(r"(?<=\d)\s*[Xx]\s*(?=\d)", " X ", text)
    text = re.sub(r"(?<=\d)\s*[Xx]\s+", " X ", text)
    text = re.sub(r"\s+[Xx]\s*(?=\d)", " X ", text)
    text = re.sub(r"\s+", " ", text)

    words = text.split()
    expanded = []
    for word in words:
        expanded.extend(ABBREVIATIONS.get(word, word).split())
    return " ".join(expanded)

def extract_type(text: str):
    tokens = set(normalize(text).split())
    for t in TYPE_PRIORITY:
        if t in tokens:
            return t
    return None

def extract_dimension(text: str):
    n = normalize(text)
    m = re.search(r"\bM\s*(\d+(?:\.\d+)?)\s*X\s*(\d+(?:\.\d+)?)", n)
    if m:
        return f"M{m.group(1)}X{m.group(2)}"
    return None

def extract_grade(text: str):
    n = normalize(text)
    if "STAINLESS STEEL 304" in n or "SS304" in n or "SS 304" in n:
        return "STAINLESS STEEL 304"
    if "STAINLESS STEEL 316" in n or "SS316" in n or "SS 316" in n:
        return "STAINLESS STEEL 316"
    if "MILD STEEL" in n:
        return "MILD STEEL"
    if "CARBON STEEL" in n:
        return "CARBON STEEL"
    return None

def attributes(text: str):
    return {
        "material_type": extract_type(text),
        "dimension": extract_dimension(text),
        "material_grade": extract_grade(text),
    }

def compare(a: dict, b: dict):
    ta = a.get("cleaned_description") or a.get("description") or ""
    tb = b.get("cleaned_description") or b.get("description") or ""

    na, nb = normalize(ta), normalize(tb)
    fuzzy = ratio(na, nb) / 100.0

    aa, ab = attributes(ta), attributes(tb)

    attr_parts = []
    for key in ("material_type", "dimension", "material_grade"):
        va, vb = aa.get(key), ab.get(key)
        if va and vb:
            attr_parts.append(1.0 if va == vb else 0.0)
    attribute = sum(attr_parts) / len(attr_parts) if attr_parts else fuzzy

    semantic = fuzzy
    final = 0.25 * semantic + 0.55 * attribute + 0.20 * fuzzy

    # Engineering guardrails for fallback integration matcher.
    if aa["material_type"] and ab["material_type"] and aa["material_type"] != ab["material_type"]:
        label = "NO_MATCH"
        final = min(final, 0.25)
        explanation = "Different material types detected."
    elif aa["dimension"] and ab["dimension"] and aa["dimension"] != ab["dimension"]:
        label = "NO_MATCH"
        final = min(final, 0.35)
        explanation = "Physical dimensions differ."
    elif (
        aa["material_type"]
        and aa["material_type"] == ab["material_type"]
        and aa["dimension"]
        and aa["dimension"] == ab["dimension"]
        and aa["material_grade"]
        and ab["material_grade"]
        and aa["material_grade"] != ab["material_grade"]
    ):
        label = "FUNCTIONAL_EQUIVALENT"
        final = max(final, 0.70)
        explanation = "Geometrically compatible but materially different; requires engineering review."
    elif final >= 0.95:
        label = "EXACT"
        explanation = "Descriptions and extracted attributes strongly agree."
    elif final >= 0.75:
        label = "NEAR_DUPLICATE"
        explanation = "High similarity with matching engineering attributes."
    else:
        label = "NO_MATCH"
        explanation = "Similarity is below the matching threshold."

    return {
        "material_a_id": a["id"],
        "material_b_id": b["id"],
        "match_score": round(float(final), 4),
        "label": label,
        "components": {
            "semantic": round(float(semantic), 4),
            "attribute": round(float(attribute), 4),
            "fuzzy": round(float(fuzzy), 4),
        },
        "attributes_a": aa,
        "attributes_b": ab,
        "explanation": explanation,
    }
