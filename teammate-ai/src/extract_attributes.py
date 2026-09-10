"""
src/extract_attributes.py
---------------------------
Turns a normalized text description into STRUCTURED data.

    "HEXAGONAL HEAD BOLT M16 X 50 MM STAINLESS STEEL 304"
        -> {
             "material_type": "bolt",
             "head_shape": "hexagonal",
             "diameter": "M16",
             "length": "50MM",
             "material_grade": "STAINLESS STEEL 304",
           }

Why this matters: comparing raw text is fuzzy and error-prone. Comparing
structured attributes is precise -- "is the diameter the same?" is a much
more reliable question than "does this text look similar?". Per the SIH
blueprint, this attribute-match score is 40% of the final hybrid score
(same weight as semantic similarity).

This is regex + dictionary based on purpose (not ML) -- it's explainable,
fast, deterministic, and good enough for a well-scoped domain like
fasteners. Run this file directly to see it applied to your dataset:

    python src/extract_attributes.py

IMPORTANT: always run this on NORMALIZED text (see normalize.py), not raw
text -- extraction patterns below assume normalized spacing/wording.
"""

import re

# normalize.py lives in the same src/ folder
from normalize import normalize
from family_extractors import extract_family_attributes


# ---------------------------------------------------------------------------
# Domain dictionaries for the fasteners category.
# Extend these as you add more material families (valves, cables, etc.)
# ---------------------------------------------------------------------------

# material_type: which keyword in the text implies which base item type.
# Order matters -- more specific terms should be checked before generic ones.
MATERIAL_TYPE_KEYWORDS = [
    ("CARRIAGE BOLT", "carriage_bolt"),
    ("HEXAGONAL HEAD BOLT", "bolt"),
    ("HEXAGONAL BOLT", "bolt"),
    ("BOLT", "bolt"),
    ("HEXAGONAL NUT", "nut"),
    ("NUT", "nut"),
    ("FLAT WASHER", "washer"),
    ("WASHER", "washer"),
    ("SCREW", "screw"),
    ("GATE VALVE", "gate_valve"),
    ("BALL VALVE", "ball_valve"),
    ("VALVE", "valve"),
    ("PIPE", "pipe"),
    ("BEARING", "bearing"),
    ("CENTRIFUGAL PUMP", "centrifugal_pump"),
    ("PUMP", "pump"),
    ("ELECTRIC MOTOR", "electric_motor"),
    ("MOTOR", "motor"),
    ("TRANSFORMER", "transformer"),
]

TYPE_FAMILY = {
    "gate_valve": "valve",
    "ball_valve": "valve",
    "centrifugal_pump": "pump",
    "electric_motor": "motor",
}

HEAD_SHAPE_KEYWORDS = [
    ("HEXAGONAL", "hexagonal"),
    ("ROUND", "round"),
    ("SQUARE", "square"),
    ("FLAT", "flat"),
]

# material_grade: pattern -> normalized grade label.
# Checked with regex since grade numbers vary (SS304, SS316, MS, CS...).
MATERIAL_GRADE_PATTERNS = [
    (re.compile(r"STAINLESS STEEL\s*(\d{3})"), lambda m: f"STAINLESS STEEL {m.group(1)}"),
    (re.compile(r"\bMILD STEEL\b"), lambda m: "MILD STEEL"),
    (re.compile(r"\bCARBON STEEL\b"), lambda m: "CARBON STEEL"),
    (re.compile(r"\bGALVANIZED IRON\b"), lambda m: "GALVANIZED IRON"),
    (re.compile(r"\bSTAINLESS(?: STEEL)?\s*(\d{3})\b"), lambda m: f"STAINLESS STEEL {m.group(1)}"),
]

# diameter: metric thread notation, e.g. M16, M20, M12
DIAMETER_PATTERN = re.compile(r"\bM(\d{1,3})\b")

# length: a number immediately followed by MM, after the diameter's "X" separator
# e.g. "M16 X 50 MM" -> length = "50MM"
LENGTH_PATTERN = re.compile(r"\bX\s*(\d{1,4}(?:\.\d+)?)\s*MM\b")
# fallback 1: "X 50" with no MM unit at all -- common when the unit was dropped
# during normalization. Assume MM since that's the dominant unit in this domain.
LENGTH_FALLBACK_NO_UNIT_PATTERN = re.compile(r"\bX\s*(\d{1,4})\b(?!\s*MM)")
# fallback 2: a bare number followed by MM anywhere (in case "X" separator missing)
LENGTH_FALLBACK_PATTERN = re.compile(r"\b(\d{1,4}(?:\.\d+)?)\s*MM\b")

NOMINAL_SIZE_PATTERN = re.compile(r"\b(?:NB|DN|OD)\s*(\d+(?:\.\d+)?)\s*MM\b")
PRESSURE_CLASS_PATTERN = re.compile(r"\bCLASS\s*(\d+)\b")
VOLTAGE_PATTERN = re.compile(r"\b(\d+(?:\.\d+)?)\s*KV\b")
POWER_PATTERN = re.compile(r"\b(\d+(?:\.\d+)?)\s*(KW|HP)\b")
CAPACITY_PATTERN = re.compile(r"\b(\d+(?:\.\d+)?)\s*KVA\b")
PART_NUMBER_PATTERN = re.compile(
    r"\bPART\s+(?:(?:NO\.?|NUMBER)\s+)?([A-Z0-9_-]+(?:\s+[A-Z0-9_-]+)*)$"
)


def _first_match(patterns, text):
    """Return the mapped value for the first keyword found in text, else None."""
    for keyword, value in patterns:
        if keyword in text:
            return value
    return None


def extract_attributes(normalized_text: str) -> dict:
    """
    Extract structured attributes from an ALREADY-NORMALIZED description.
    Always call normalize() on raw text first -- see the __main__ block
    below for the correct usage pattern.

    Returns a dict with keys: material_type, head_shape, diameter, length,
    material_grade. Any attribute not found in the text is None -- we do
    NOT guess, per the SIH blueprint's guidance to validate before merging.
    """
    text = normalized_text.upper()

    material_type = _first_match(MATERIAL_TYPE_KEYWORDS, text)
    head_shape = _first_match(HEAD_SHAPE_KEYWORDS, text)

    material_grade = None
    for pattern, formatter in MATERIAL_GRADE_PATTERNS:
        m = pattern.search(text)
        if m:
            material_grade = formatter(m)
            break

    diameter = None
    m = DIAMETER_PATTERN.search(text)
    if m:
        diameter = f"M{m.group(1)}"

    length = None
    m = LENGTH_PATTERN.search(text)
    if m:
        length = f"{float(m.group(1)):g}MM"
    else:
        m = LENGTH_FALLBACK_PATTERN.search(text)
        if m:
            length = f"{float(m.group(1)):g}MM"
        else:
            m = LENGTH_FALLBACK_NO_UNIT_PATTERN.search(text)
            if m:
                length = f"{float(m.group(1)):g}MM"

    nominal_size = None
    m = NOMINAL_SIZE_PATTERN.search(text)
    if m:
        nominal_size = f"{float(m.group(1)):g}MM"

    pressure_class = None
    m = PRESSURE_CLASS_PATTERN.search(text)
    if m:
        pressure_class = f"CLASS {m.group(1)}"

    voltage = None
    m = VOLTAGE_PATTERN.search(text)
    if m:
        voltage = f"{float(m.group(1)):g}KV"

    power = None
    m = POWER_PATTERN.search(text)
    if m:
        value = float(m.group(1))
        if m.group(2) == "HP":
            value *= 0.7457
        power = f"{value:.3f}".rstrip("0").rstrip(".") + "KW"

    capacity = None
    m = CAPACITY_PATTERN.search(text)
    if m:
        capacity = f"{float(m.group(1)):g}KVA"

    part_number = None
    m = PART_NUMBER_PATTERN.search(text)
    if m:
        part_number = re.sub(r"\s+", "", m.group(1))

    attributes = {
        "material_type": material_type,
        "head_shape": head_shape,
        "diameter": diameter,
        "length": length,
        "material_grade": material_grade,
        "nominal_size": nominal_size,
        "pressure_class": pressure_class,
        "voltage": voltage,
        "power": power,
        "capacity": capacity,
        "part_number": part_number,
    }
    attributes.update(extract_family_attributes(text))
    return attributes


def attribute_match_score(attrs_a: dict, attrs_b: dict) -> float:
    """
    Compare two attribute dicts field by field.
    Returns a score from 0.0 to 1.0 = (# matching fields) / (# comparable fields).

    "Comparable" means both sides have a non-None value for that field --
    fields that are None on either side are skipped, not counted as a
    mismatch (we don't penalize missing data, only contradicting data).
    """
    comparable = 0
    matches = 0
    for key in attrs_a:
        a_val = attrs_a.get(key)
        b_val = attrs_b.get(key)
        if a_val is None or b_val is None:
            continue
        comparable += 1
        if a_val == b_val:
            matches += 1

    if comparable == 0:
        return 0.0  # nothing to compare -- treat as no evidence of a match
    return matches / comparable


# ---------------------------------------------------------------------------
# Standalone test -- run this file directly to see extraction in action
# on the synthetic dataset generated by data/make_dataset.py
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import csv
    import os

    print("=== extract_attributes() demo on hardcoded examples ===\n")
    examples = [
        "HEX BOLT M16 X 50 MM SS304",
        "Hexagonal Bolt M16*50 Stainless Steel 304",
        "SS 304 HEX HEAD BOLT M16 X 50",
        "CARRIAGE BOLT M16 X 50 MM SS304",
    ]
    parsed = []
    for raw in examples:
        norm = normalize(raw)
        attrs = extract_attributes(norm)
        parsed.append(attrs)
        print(f"  RAW:   {raw}")
        print(f"  NORM:  {norm}")
        print(f"  ATTRS: {attrs}\n")

    print("=== attribute_match_score() between example 0 and example 1 ===")
    print(f"  (should be high -- same bolt, different wording)")
    print(f"  score = {attribute_match_score(parsed[0], parsed[1]):.2f}\n")

    print("=== attribute_match_score() between example 0 and example 3 ===")
    print(f"  (should be lower -- carriage bolt has different type, same dims/material)")
    print(f"  score = {attribute_match_score(parsed[0], parsed[3]):.2f}\n")

    # Apply to the real dataset if it exists
    data_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data",
        "synthetic_materials.csv",
    )
    if os.path.exists(data_path):
        print("=== extract_attributes() applied to your synthetic dataset ===\n")
        with open(data_path, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        for r in rows[:10]:
            norm = normalize(r["original_description"])
            attrs = extract_attributes(norm)
            print(f"  [{r['cpse']}] {r['original_description']}")
            print(f"       -> {attrs}\n")
        print(f"(showing first 10 of {len(rows)} rows)")
    else:
        print(f"No dataset found at {data_path} -- run data/make_dataset.py first.")
