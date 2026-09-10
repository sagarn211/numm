"""
data/make_dataset.py
---------------------
Generates a synthetic CPSE material dataset (fasteners domain: bolts, nuts,
washers) with realistic wording variation across fictional CPSEs, plus a
ground-truth pairs file for evaluating the matcher (precision/recall/F1).

Run from the project root:
    python data/make_dataset.py

Outputs (into data/):
    synthetic_materials.csv   -> one row per CPSE material record
    ground_truth_pairs.csv    -> labelled pairs: same=1, functional_equiv=2, different=0
"""

import csv
import itertools
import os
import random

random.seed(42)

OUT_DIR = os.path.dirname(os.path.abspath(__file__))

CPSES = ["NTPC", "SAIL", "IOC", "NM", "BHEL"]

# ---------------------------------------------------------------------------
# Material "families" — each family is a real-world identical/near-identical
# item described in different ways by different CPSEs.
# variants: list of description strings that all refer to the SAME material.
# ---------------------------------------------------------------------------
FAMILIES = [
    {
        "family_id": "F001",
        "canonical": "HEXAGONAL HEAD BOLT, M16 X 50 MM, STAINLESS STEEL 304",
        "category": "Fasteners > Bolts",
        "unit": "NOS",
        "variants": [
            "HEX BOLT M16 X 50 MM SS304",
            "Hexagonal Bolt M16*50 Stainless Steel 304",
            "SS 304 HEX HEAD BOLT M16 X 50",
            "HEX HEAD BOLT M16 50MM SS304",
            "Bolt Hex Head M16x50mm SS-304",
        ],
    },
    {
        "family_id": "F002",
        "canonical": "HEXAGONAL HEAD BOLT, M16 X 50 MM, MILD STEEL",
        "category": "Fasteners > Bolts",
        "unit": "NOS",
        "variants": [
            "HEX BOLT M16 X 50 MM MS",
            "Hexagonal Bolt M16*50 Mild Steel",
            "MS HEX HEAD BOLT M16 X 50",
        ],
        # functional equivalent to F001 (same size, different material grade)
        "functional_equiv_of": "F001",
    },
    {
        "family_id": "F003",
        "canonical": "HEXAGONAL NUT, M16, STAINLESS STEEL 304",
        "category": "Fasteners > Nuts",
        "unit": "NOS",
        "variants": [
            "HEX NUT M16 SS304",
            "Hexagonal Nut M16 Stainless Steel 304",
            "SS 304 HEX NUT M16",
            "Nut Hex M16 SS-304",
        ],
    },
    {
        "family_id": "F004",
        "canonical": "FLAT WASHER, M16, STAINLESS STEEL 304",
        "category": "Fasteners > Washers",
        "unit": "NOS",
        "variants": [
            "FLAT WASHER M16 SS304",
            "Washer Flat M16 Stainless Steel 304",
            "SS304 FLAT WASHER M16",
        ],
    },
    {
        "family_id": "F005",
        "canonical": "HEXAGONAL HEAD BOLT, M20 X 75 MM, STAINLESS STEEL 304",
        "category": "Fasteners > Bolts",
        "unit": "NOS",
        "variants": [
            "HEX BOLT M20 X 75 MM SS304",
            "Hexagonal Bolt M20*75 Stainless Steel 304",
            "SS 304 HEX HEAD BOLT M20 X 75",
        ],
    },
    {
        "family_id": "F006",
        "canonical": "CARRIAGE BOLT, M16 X 50 MM, STAINLESS STEEL 304",
        "category": "Fasteners > Bolts",
        "unit": "NOS",
        "variants": [
            "CARRIAGE BOLT M16 X 50 MM SS304",
            "Carriage Bolt M16*50 Stainless Steel 304",
            "SS 304 CARRIAGE BOLT M16 X 50",
        ],
        # NOT the same as F001 -- different head/body type, same dims/material
        # kept separate on purpose to give the matcher a genuine No-Match /
        # tricky Near-Duplicate case despite near-identical wording pattern
    },
    {
        "family_id": "F007",
        "canonical": "HEXAGONAL HEAD BOLT, M12 X 40 MM, STAINLESS STEEL 316",
        "category": "Fasteners > Bolts",
        "unit": "NOS",
        "variants": [
            "HEX BOLT M12 X 40 MM SS316",
            "Hexagonal Bolt M12*40 Stainless Steel 316",
            "SS 316 HEX HEAD BOLT M12 X 40",
        ],
    },
]


def build_material_rows():
    """Assign each variant to a CPSE and produce material master rows."""
    rows = []
    row_id = 1
    for fam in FAMILIES:
        variants = fam["variants"]
        cpses_for_family = random.sample(CPSES, k=min(len(variants), len(CPSES)))
        for cpse, desc in zip(cpses_for_family, variants):
            rows.append(
                {
                    "material_id": row_id,
                    "cpse": cpse,
                    "legacy_code": f"{cpse}-{random.randint(1000, 9999)}",
                    "original_description": desc,
                    "unit": fam["unit"],
                    "category_hint": fam["category"],
                    "family_id": fam["family_id"],  # kept for ground-truth generation only
                }
            )
            row_id += 1
    return rows


def build_ground_truth(rows):
    """
    For every pair of rows, label:
      1 = same material (same family_id)
      2 = functional equivalent (family marked functional_equiv_of the other)
      0 = different material
    Only a sample of the "different" pairs is kept (full O(n^2) is noisy/huge).
    """
    fam_lookup = {f["family_id"]: f for f in FAMILIES}
    pairs = []

    for a, b in itertools.combinations(rows, 2):
        fam_a, fam_b = a["family_id"], b["family_id"]
        if fam_a == fam_b:
            label = 1
        else:
            equiv_a = fam_lookup[fam_a].get("functional_equiv_of")
            equiv_b = fam_lookup[fam_b].get("functional_equiv_of")
            if equiv_a == fam_b or equiv_b == fam_a:
                label = 2
            else:
                label = 0
        pairs.append((a["material_id"], b["material_id"], label))

    same = [p for p in pairs if p[2] == 1]
    equiv = [p for p in pairs if p[2] == 2]
    diff = [p for p in pairs if p[2] == 0]

    # Downsample "different" pairs so the dataset isn't 95% negatives
    random.shuffle(diff)
    diff = diff[: max(len(same) * 3, 30)]

    all_pairs = same + equiv + diff
    random.shuffle(all_pairs)
    return all_pairs


def write_csv(path, fieldnames, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        # extrasaction="ignore": rows may carry internal-only keys (like
        # family_id, used only to build ground truth) that aren't part of
        # this particular output file's columns -- just drop those, don't error.
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for r in rows:
            writer.writerow(r)


def main():
    material_rows = build_material_rows()
    ground_truth_pairs = build_ground_truth(material_rows)

    materials_path = os.path.join(OUT_DIR, "synthetic_materials.csv")
    gt_path = os.path.join(OUT_DIR, "ground_truth_pairs.csv")

    # Public-facing materials file (drop the internal family_id — that's the
    # "answer key" and shouldn't be visible to the matcher itself)
    public_fieldnames = [
        "material_id", "cpse", "legacy_code",
        "original_description", "unit", "category_hint",
    ]
    write_csv(materials_path, public_fieldnames, material_rows)

    gt_rows = [
        {"material_id_a": a, "material_id_b": b, "label": label}
        for a, b, label in ground_truth_pairs
    ]
    write_csv(gt_path, ["material_id_a", "material_id_b", "label"], gt_rows)

    print(f"Wrote {len(material_rows)} material records -> {materials_path}")
    print(f"Wrote {len(gt_rows)} ground-truth pairs   -> {gt_path}")
    print("\nLabel legend: 1 = same material, 2 = functional equivalent, 0 = different")


if __name__ == "__main__":
    main()