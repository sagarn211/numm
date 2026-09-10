"""
src/scorer.py
---------------
The final piece: combines all three signals into one confidence score,
a label, and a plain-English explanation.

    final_score = 0.4 * semantic_similarity
                + 0.4 * attribute_match
                + 0.2 * fuzzy_similarity

This is what your teammate's FastAPI endpoint will call. Given two raw
material descriptions, match_materials() returns everything the frontend
needs to show a judge/officer: the score, the label, WHY it got that
score, and the extracted structured attributes for both records.

Run this file directly to see it applied to your dataset:
    python src/scorer.py
"""

import re

from normalize import normalize
from extract_attributes import TYPE_FAMILY, extract_attributes, attribute_match_score
from fuzzy_score import fuzzy_score
from embed_and_retrieve import semantic_similarity


# ---------------------------------------------------------------------------
# Scoring weights -- per the SIH blueprint's suggested starting point.
# TUNE THESE against ground_truth_pairs.csv once you have real eval numbers
# (see tests/eval_against_ground_truth.py, built next).
# ---------------------------------------------------------------------------
# Scoring weights -- ADJUSTED after running eval_against_ground_truth.py.
# Original blueprint suggestion was 0.4/0.4/0.2, but evaluation showed
# semantic similarity is too forgiving of real engineering differences
# (e.g. SS304 vs MS, M16 vs M20 scored ~0.9+ semantically despite being
# genuinely different materials). Attribute matching proved more reliable,
# so it now carries more weight. Keep tuning these against eval results.
WEIGHT_SEMANTIC = 0.25
WEIGHT_ATTRIBUTE = 0.55
WEIGHT_FUZZY = 0.20

# Label thresholds -- also starting points, tune against real eval data.
THRESHOLD_EXACT = 0.95
THRESHOLD_NEAR_DUPLICATE = 0.80
THRESHOLD_FUNCTIONAL_EQUIVALENT = 0.60


def label_from_score(score: float) -> str:
    """Map a final confidence score to one of the 4 SIH-required labels."""
    if score >= THRESHOLD_EXACT:
        return "Exact"
    elif score >= THRESHOLD_NEAR_DUPLICATE:
        return "Near-Duplicate"
    elif score >= THRESHOLD_FUNCTIONAL_EQUIVALENT:
        return "Functional-Equivalent"
    else:
        return "No-Match"


def build_explanation(attrs_a: dict, attrs_b: dict, components: dict) -> str:
    """
    Build a short, human-readable explanation of WHY the materials scored
    the way they did -- this is the "explainability" requirement from the
    blueprint. Officers approving/rejecting need to see the reasoning,
    not just a bare number.
    """
    matched_fields = []
    differing_fields = []
    for key in attrs_a:
        a_val = attrs_a.get(key)
        b_val = attrs_b.get(key)
        if a_val is None or b_val is None:
            continue
        label = key.replace("_", " ")
        if a_val == b_val:
            matched_fields.append(label)
        else:
            differing_fields.append(f"{label} ({a_val} vs {b_val})")

    parts = []
    if matched_fields:
        parts.append(f"Matched on {', '.join(matched_fields)}")
    if differing_fields:
        parts.append(f"differs on {', '.join(differing_fields)}")

    attribute_note = "; ".join(parts) if parts else "insufficient attribute data to compare"

    return (
        f"{attribute_note}. "
        f"Semantic similarity {components['semantic']:.0%}, "
        f"attribute match {components['attribute']:.0%}, "
        f"fuzzy similarity {components['fuzzy']:.0%}."
    )


def match_materials(description_a: str, description_b: str) -> dict:
    """
    Compare two RAW (not yet normalized) material descriptions end-to-end.
    This is the single function your teammate's API endpoint should call.

    Returns:
        {
          "match_score": float,       # 0.0-1.0 final confidence
          "label": str,                # Exact / Near-Duplicate / Functional-Equivalent / No-Match
          "components": {...},         # individual signal scores, for transparency
          "attributes_a": {...},
          "attributes_b": {...},
          "explanation": str,
        }
    """
    norm_a = normalize(description_a)
    norm_b = normalize(description_b)

    attrs_a = extract_attributes(norm_a)
    attrs_b = extract_attributes(norm_b)

    semantic = semantic_similarity(norm_a, norm_b)
    attribute = attribute_match_score(attrs_a, attrs_b)
    fuzzy = fuzzy_score(norm_a, norm_b)

    components = {"semantic": semantic, "attribute": attribute, "fuzzy": fuzzy}

    # HARD VETO: material_type is a categorical attribute -- a nut is never
    # "similar to" a bolt no matter how close the wording/embedding scores
    # are. If both sides have a known type and they disagree, this is
    # always a No-Match, skipping the weighted formula entirely. This
    # fixes the specific failure mode found in eval_against_ground_truth.py
    # where e.g. "Hexagonal Nut M16 SS304" vs "Hexagonal Bolt M20*75 SS304"
    # scored high enough to be mislabeled Functional-Equivalent.
    type_a = attrs_a.get("material_type")
    type_b = attrs_b.get("material_type")
    family_a = TYPE_FAMILY.get(type_a, type_a)
    family_b = TYPE_FAMILY.get(type_b, type_b)
    if family_a is not None and family_b is not None and family_a != family_b:
        final_score = min(
            (WEIGHT_SEMANTIC * semantic + WEIGHT_ATTRIBUTE * attribute + WEIGHT_FUZZY * fuzzy),
            THRESHOLD_FUNCTIONAL_EQUIVALENT - 0.01,  # force below the No-Match line
        )
        label = "No-Match"
        explanation = (
            f"Different material type ({type_a} vs {type_b}) -- these are fundamentally "
            f"different items regardless of wording similarity."
        )
        return {
            "match_score": round(final_score, 4),
            "label": label,
            "components": {k: round(v, 4) for k, v in components.items()},
            "attributes_a": attrs_a,
            "attributes_b": attrs_b,
            "explanation": explanation,
        }

    # Critical engineering conflicts are hard vetoes. Similar wording cannot
    # establish interchangeability when pressure, voltage, rating, part
    # number, or physical dimensions explicitly disagree.
    diameter_a, diameter_b = attrs_a.get("diameter"), attrs_b.get("diameter")
    length_a, length_b = attrs_a.get("length"), attrs_b.get("length")
    grade_a, grade_b = attrs_a.get("material_grade"), attrs_b.get("material_grade")

    diameter_matches = diameter_a is None or diameter_b is None or diameter_a == diameter_b
    length_matches = length_a is None or length_b is None or length_a == length_b
    grade_differs = grade_a is not None and grade_b is not None and grade_a != grade_b
    critical_fields = (
        "nominal_size", "pressure_class", "voltage",
        "power", "capacity", "part_number", "nominal_diameter",
        "pressure_rating", "phase", "frequency", "rpm", "frame",
        "bearing_designation", "bore", "outer_diameter", "width",
        "flow", "head", "schedule",
    )
    def critical_values_equal(key, left, right):
        if key not in {"nominal_size", "voltage", "power", "capacity"}:
            return left == right
        left_number = re.search(r"[-+]?\d+(?:\.\d+)?", str(left))
        right_number = re.search(r"[-+]?\d+(?:\.\d+)?", str(right))
        if not left_number or not right_number:
            return left == right
        left_value = float(left_number.group())
        right_value = float(right_number.group())
        tolerance = max(abs(left_value), abs(right_value)) * 0.01
        return abs(left_value - right_value) <= max(tolerance, 0.01)

    conflicts = [
        key for key in critical_fields
        if attrs_a.get(key) is not None
        and attrs_b.get(key) is not None
        and not critical_values_equal(key, attrs_a[key], attrs_b[key])
    ]

    if conflicts:
        final_score = min(
            (WEIGHT_SEMANTIC * semantic + WEIGHT_ATTRIBUTE * attribute + WEIGHT_FUZZY * fuzzy),
            THRESHOLD_FUNCTIONAL_EQUIVALENT - 0.01,
        )
        details = ", ".join(
            f"{key.replace('_', ' ')} ({attrs_a[key]} vs {attrs_b[key]})"
            for key in conflicts
        )
        return {
            "match_score": round(final_score, 4),
            "label": "No-Match",
            "components": {k: round(v, 4) for k, v in components.items()},
            "attributes_a": attrs_a,
            "attributes_b": attrs_b,
            "explanation": f"Conflicting critical engineering attributes: {details}.",
        }

    # THIRD RULE: a genuine PHYSICAL SIZE mismatch (diameter and/or length
    # both present and different) means the parts are not interchangeable,
    # regardless of matching type or material grade -- a bolt of the wrong
    # diameter cannot be swapped in, full stop. This takes priority over
    # the weighted similarity score.
    size_differs = (not diameter_matches) or (not length_matches)
    if family_a is not None and family_a == family_b and size_differs:
        final_score = min(
            (WEIGHT_SEMANTIC * semantic + WEIGHT_ATTRIBUTE * attribute + WEIGHT_FUZZY * fuzzy),
            THRESHOLD_FUNCTIONAL_EQUIVALENT - 0.01,
        )
        label = "No-Match"
        explanation = (
            f"Different physical size (diameter {diameter_a} vs {diameter_b}, "
            f"length {length_a} vs {length_b}) -- not interchangeable regardless of "
            f"matching type or material."
        )
        return {
            "match_score": round(final_score, 4),
            "label": label,
            "components": {k: round(v, 4) for k, v in components.items()},
            "attributes_a": attrs_a,
            "attributes_b": attrs_b,
            "explanation": explanation,
        }

    # A same-type, same-size item in another grade is only a functional-
    # equivalent candidate. It cannot be merged until an officer explicitly
    # acknowledges that classification in the approval workflow.
    if (
        family_a is not None and family_a == family_b
        and diameter_matches and length_matches
        and grade_differs
    ):
        final_score = max(
            (WEIGHT_SEMANTIC * semantic + WEIGHT_ATTRIBUTE * attribute + WEIGHT_FUZZY * fuzzy),
            THRESHOLD_FUNCTIONAL_EQUIVALENT,
        )
        final_score = min(final_score, THRESHOLD_NEAR_DUPLICATE - 0.01)
        return {
            "match_score": round(final_score, 4),
            "label": "Functional-Equivalent",
            "components": {k: round(v, 4) for k, v in components.items()},
            "attributes_a": attrs_a,
            "attributes_b": attrs_b,
            "explanation": (
                f"Same type and size but different material grade ({grade_a} vs {grade_b}); "
                "human engineering review and explicit acknowledgement are required."
            ),
        }

    engineering_family_a = attrs_a.get("family") or (str(family_a).upper() if family_a else None)
    engineering_family_b = attrs_b.get("family") or (str(family_b).upper() if family_b else None)
    required_by_family = {
        "FASTENER": ("diameter", "length", "material_grade"),
        "VALVE": ("nominal_diameter", "pressure_rating", "body_material"),
        "MOTOR": ("power", "voltage", "phase"),
        "BEARING": ("bearing_designation",),
        "PUMP": ("flow", "head", "power"),
        "PIPE": ("nominal_diameter", "schedule", "body_material"),
        "FLANGE": ("nominal_diameter", "pressure_rating", "body_material"),
    }
    if engineering_family_a and engineering_family_a == engineering_family_b:
        missing_evidence = [
            key for key in required_by_family.get(engineering_family_a, ())
            if (attrs_a.get(key) is None) != (attrs_b.get(key) is None)
        ]
        if missing_evidence:
            final_score = min(max(
                WEIGHT_SEMANTIC * semantic + WEIGHT_ATTRIBUTE * attribute + WEIGHT_FUZZY * fuzzy,
                THRESHOLD_FUNCTIONAL_EQUIVALENT,
            ), THRESHOLD_NEAR_DUPLICATE - 0.01)
            return {
                "match_score": round(final_score, 4),
                "label": "Functional-Equivalent",
                "components": {k: round(v, 4) for k, v in components.items()},
                "attributes_a": attrs_a,
                "attributes_b": attrs_b,
                "explanation": (
                    "Identity-critical evidence is present on only one record "
                    f"({', '.join(missing_evidence)}); engineering review is required."
                ),
            }

    final_score = (
        WEIGHT_SEMANTIC * semantic
        + WEIGHT_ATTRIBUTE * attribute
        + WEIGHT_FUZZY * fuzzy
    )

    label = label_from_score(final_score)

    comparable = sum(
        attrs_a.get(key) is not None and attrs_b.get(key) is not None
        for key in attrs_a
    )
    one_description_contains_the_other = norm_a != norm_b and (
        norm_a in norm_b or norm_b in norm_a
    )
    if (
        family_a is not None and family_a == family_b
        and comparable == 1
        and one_description_contains_the_other
    ):
        final_score = min(
            max(final_score, THRESHOLD_FUNCTIONAL_EQUIVALENT),
            THRESHOLD_NEAR_DUPLICATE - 0.01,
        )
        label = "Functional-Equivalent"
    explanation = build_explanation(attrs_a, attrs_b, components)

    return {
        "match_score": round(final_score, 4),
        "label": label,
        "components": {k: round(v, 4) for k, v in components.items()},
        "attributes_a": attrs_a,
        "attributes_b": attrs_b,
        "explanation": explanation,
    }


# ---------------------------------------------------------------------------
# Standalone test -- run this file directly to see the full pipeline
# working end-to-end on real examples + your synthetic dataset.
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import csv
    import json
    import os

    print("Loading model (first run may take a moment)...\n")

    print("=== match_materials() on the classic 4-CPSE bolt example ===\n")
    test_pairs = [
        # (description_a, description_b, expected_label_hint)
        ("HEX BOLT M16 X 50 MM SS304", "Hexagonal Bolt M16*50 Stainless Steel 304", "Exact"),
        ("HEX BOLT M16 X 50 MM SS304", "SS 304 HEX HEAD BOLT M16 X 50", "Exact"),
        ("HEX BOLT M16 X 50 MM SS304", "HEX BOLT M20 X 75 MM SS304", "No-Match (different size)"),
        ("HEX BOLT M16 X 50 MM SS304", "CARRIAGE BOLT M16 X 50 MM SS304", "Functional-Equivalent (different bolt type)"),
    ]

    for a, b, hint in test_pairs:
        result = match_materials(a, b)
        print(f"  A: {a}")
        print(f"  B: {b}")
        print(f"  Expected: {hint}")
        print(f"  -> score={result['match_score']:.4f}  label={result['label']}")
        print(f"  -> {result['explanation']}\n")

    # Full pipeline demo on the real dataset
    data_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data",
        "synthetic_materials.csv",
    )
    if os.path.exists(data_path):
        print("=== match_materials() applied to your synthetic dataset ===\n")
        with open(data_path, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))

        query_row = rows[0]
        print(f"Query: [{query_row['cpse']}] {query_row['original_description']}\n")

        results = []
        for r in rows[1:]:
            res = match_materials(query_row["original_description"], r["original_description"])
            results.append((res["match_score"], r, res))

        results.sort(key=lambda x: x[0], reverse=True)
        for score, r, res in results[:6]:
            print(f"  {score:.4f}  [{res['label']:>22}]  [{r['cpse']}] {r['original_description']}")
        print(f"\n(showing top 6 of {len(results)} comparisons)\n")

        # Show a full detailed result for the top match as a sample of the
        # JSON your teammate's API would return
        print("=== Sample full JSON output (top match) ===")
        top_score, top_row, top_res = results[0]
        print(json.dumps(top_res, indent=2))
    else:
        print(f"No dataset found at {data_path} -- run data/make_dataset.py first.")
