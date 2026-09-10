"""
tests/eval_against_ground_truth.py
------------------------------------
Runs match_materials() against every labelled pair in
data/ground_truth_pairs.csv and reports precision / recall / F1 --
turning "the AI seems to work" into an actual measured number, which is
exactly what the SIH blueprint asks for (see "Definition of Done" and
"synthetic dataset" sections).

Ground truth labels (from make_dataset.py):
    1 = same material           (expect label "Exact" or "Near-Duplicate")
    2 = functional equivalent   (expect label "Functional-Equivalent")
    0 = different material      (expect label "No-Match")

Since match_materials() returns 4 possible labels but ground truth only
has 3 categories, we bucket "Exact" and "Near-Duplicate" together as
"same material" for scoring purposes -- both mean "these should be
merged/mapped to the same national code", which is what matters for
accuracy. The full 4-way label breakdown is still shown for inspection.

Run from the project root:
    python tests/eval_against_ground_truth.py
"""

import csv
import argparse
import hashlib
import json
import os
import sys
from collections import Counter
from datetime import datetime, timezone

# Allow importing from src/ when running this script directly
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from scorer import (  # noqa: E402
    THRESHOLD_EXACT,
    THRESHOLD_FUNCTIONAL_EQUIVALENT,
    THRESHOLD_NEAR_DUPLICATE,
    WEIGHT_ATTRIBUTE,
    WEIGHT_FUZZY,
    WEIGHT_SEMANTIC,
    match_materials,
)


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MATERIALS_PATH = os.path.join(PROJECT_ROOT, "data", "synthetic_materials.csv")
GROUND_TRUTH_PATH = os.path.join(PROJECT_ROOT, "data", "ground_truth_pairs.csv")
CHALLENGE_PATH = os.path.join(PROJECT_ROOT, "data", "challenge_pairs.csv")


def load_materials():
    """Load materials into a dict keyed by material_id for quick lookup."""
    with open(MATERIALS_PATH, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return {int(r["material_id"]): r for r in rows}


def load_ground_truth():
    with open(GROUND_TRUTH_PATH, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return [
        (int(r["material_id_a"]), int(r["material_id_b"]), int(r["label"]))
        for r in rows
    ]


def load_challenges():
    with open(CHALLENGE_PATH, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        required = {
            "description_a", "description_b", "label", "scenario",
            "family", "cpse_a", "cpse_b",
        }
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(
                "Challenge dataset is missing columns: " + ", ".join(sorted(missing))
            )
        return list(reader)


def bucket_label(predicted_label: str) -> str:
    """
    Collapse the 4-way predicted label down to match ground truth's 3
    categories, for accuracy scoring purposes.
    """
    if predicted_label in ("Exact", "Near-Duplicate"):
        return "same"
    elif predicted_label == "Functional-Equivalent":
        return "functional_equivalent"
    else:
        return "different"


def bucket_ground_truth(gt_label: int) -> str:
    return {1: "same", 2: "functional_equivalent", 0: "different"}[gt_label]


def compute_prf(true_labels: list[str], pred_labels: list[str], target_class: str):
    """
    Manual precision/recall/F1 for one class (avoids requiring scikit-learn
    just for this -- easy to swap for sklearn.metrics.precision_recall_fscore_support
    later if you want the multi-class report format).
    """
    tp = sum(1 for t, p in zip(true_labels, pred_labels) if t == target_class and p == target_class)
    fp = sum(1 for t, p in zip(true_labels, pred_labels) if t != target_class and p == target_class)
    fn = sum(1 for t, p in zip(true_labels, pred_labels) if t == target_class and p != target_class)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    return {"precision": precision, "recall": recall, "f1": f1, "support": tp + fn}


def _sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()

def main(output_path=None):
    if not all(os.path.exists(path) for path in (
        MATERIALS_PATH, GROUND_TRUTH_PATH, CHALLENGE_PATH,
    )):
        print("Evaluation dataset missing -- restore the material, ground-truth, and challenge CSV files.")
        return

    materials = load_materials()
    ground_truth = load_ground_truth()
    challenges = load_challenges()

    print(f"Loaded {len(materials)} materials, {len(ground_truth)} ground-truth pairs.")
    print("Running matcher on every pair (this calls the embedding model each time,")
    print("so it may take a little while for 100+ pairs)...\n")

    true_labels = []
    pred_labels = []
    detailed_results = []

    for i, (id_a, id_b, gt_label) in enumerate(ground_truth, start=1):
        mat_a = materials[id_a]
        mat_b = materials[id_b]

        result = match_materials(mat_a["original_description"], mat_b["original_description"])

        true_bucket = bucket_ground_truth(gt_label)
        pred_bucket = bucket_label(result["label"])

        true_labels.append(true_bucket)
        pred_labels.append(pred_bucket)

        detailed_results.append({
            "a": mat_a["original_description"],
            "b": mat_b["original_description"],
            "true": true_bucket,
            "predicted": pred_bucket,
            "predicted_4way": result["label"],
            "score": result["match_score"],
            "correct": true_bucket == pred_bucket,
            "source": "synthetic_ground_truth",
            "scenario": "standard",
            "partition": "tuning" if int(hashlib.sha256(f"{id_a}:{id_b}".encode()).hexdigest(), 16) % 5 == 0 else "test",
        })
        if i % 20 == 0:
            print(f"  ...processed {i}/{len(ground_truth)} pairs")

    for challenge in challenges:
        result = match_materials(challenge["description_a"], challenge["description_b"])
        true_bucket = bucket_ground_truth(int(challenge["label"]))
        pred_bucket = bucket_label(result["label"])
        true_labels.append(true_bucket)
        pred_labels.append(pred_bucket)
        detailed_results.append({
            "a": challenge["description_a"], "b": challenge["description_b"],
            "true": true_bucket, "predicted": pred_bucket,
            "predicted_4way": result["label"], "score": result["match_score"],
            "correct": true_bucket == pred_bucket, "source": "held_out_challenge",
            "scenario": challenge["scenario"], "partition": "test",
            "cpse_a": challenge["cpse_a"], "cpse_b": challenge["cpse_b"],
        })

    total_pairs = len(ground_truth) + len(challenges)
    print(f"  ...processed {total_pairs}/{total_pairs} pairs\n")

    # ------------------------------------------------------------------
    # Overall accuracy
    # ------------------------------------------------------------------
    correct = sum(1 for r in detailed_results if r["correct"])
    accuracy = correct / len(detailed_results)
    print("=" * 60)
    print(f"OVERALL ACCURACY: {accuracy:.1%}  ({correct}/{len(detailed_results)} correct)")
    print("=" * 60 + "\n")

    # ------------------------------------------------------------------
    # Per-class precision / recall / F1
    # ------------------------------------------------------------------
    print("Per-class metrics:\n")
    print(f"  {'Class':<22} {'Precision':>10} {'Recall':>10} {'F1':>10} {'Support':>10}")
    for cls in ["same", "functional_equivalent", "different"]:
        m = compute_prf(true_labels, pred_labels, cls)
        print(f"  {cls:<22} {m['precision']:>10.1%} {m['recall']:>10.1%} {m['f1']:>10.1%} {m['support']:>10}")

    classes = ["same", "functional_equivalent", "different"]
    per_class = {cls: compute_prf(true_labels, pred_labels, cls) for cls in classes}
    confusion_matrix = {
        true_cls: {pred_cls: sum(1 for true, pred in zip(true_labels, pred_labels) if true == true_cls and pred == pred_cls) for pred_cls in classes}
        for true_cls in classes
    }
    identity_tp = sum(t == "same" and p == "same" for t, p in zip(true_labels, pred_labels))
    identity_fp = sum(t != "same" and p == "same" for t, p in zip(true_labels, pred_labels))
    identity_fn = sum(t == "same" and p != "same" for t, p in zip(true_labels, pred_labels))
    identity_tn = sum(t != "same" and p != "same" for t, p in zip(true_labels, pred_labels))

    # ------------------------------------------------------------------
    # Misclassified examples -- the most useful part for debugging/tuning
    # ------------------------------------------------------------------
    misclassified = [r for r in detailed_results if not r["correct"]]
    print(f"\n{len(misclassified)} misclassified pairs (showing up to 15):\n")
    for r in misclassified[:15]:
        print(f"  TRUE={r['true']:<22} PRED={r['predicted']:<22} (4-way: {r['predicted_4way']}, score={r['score']:.3f})")
        print(f"    A: {r['a']}")
        print(f"    B: {r['b']}\n")

    print("\nNext steps if accuracy is lower than you'd like:")
    print("  - Look at the misclassified pairs above for patterns")
    print("  - Adjust WEIGHT_SEMANTIC / WEIGHT_ATTRIBUTE / WEIGHT_FUZZY in src/scorer.py")
    print("  - Adjust THRESHOLD_EXACT / THRESHOLD_NEAR_DUPLICATE / THRESHOLD_FUNCTIONAL_EQUIVALENT")
    print("  - Re-run this script after each change to see if accuracy improves")

    family_distribution = Counter(row.get("category_hint") or "Unknown" for row in materials.values())
    challenge_family_distribution = Counter(challenge["family"] for challenge in challenges)
    partition_distribution = Counter(item["partition"] for item in detailed_results)
    scenario_results = {
        scenario: {
            "cases": sum(item["scenario"] == scenario for item in detailed_results),
            "correct": sum(item["scenario"] == scenario and item["correct"] for item in detailed_results),
        }
        for scenario in sorted({item["scenario"] for item in detailed_results})
    }
    partition_metrics = {}
    for partition in sorted(partition_distribution):
        rows = [item for item in detailed_results if item["partition"] == partition]
        partition_metrics[partition] = {
            "accuracy": sum(item["correct"] for item in rows) / len(rows),
            "per_class": {
                cls: compute_prf(
                    [item["true"] for item in rows],
                    [item["predicted"] for item in rows],
                    cls,
                )
                for cls in classes
            },
        }
    report = {
        "evaluation_timestamp": datetime.now(timezone.utc).isoformat(),
        "claim_scope": f"Performance on {len(ground_truth)} labelled synthetic pairs plus {len(challenges)} held-out challenge pairs only",
        "materials": len(materials),
        "ground_truth_pairs": len(ground_truth),
        "held_out_challenge_pairs": len(challenges),
        "family_distribution": dict(sorted(family_distribution.items())),
        "challenge_family_distribution": dict(sorted(challenge_family_distribution.items())),
        "partition_policy": "No project training split: MiniLM is pretrained. Threshold tuning uses deterministic 20% tuning pairs; all challenge pairs and remaining pairs are held-out test data.",
        "partition_distribution": dict(partition_distribution),
        "partition_metrics": partition_metrics,
        "accuracy": accuracy,
        "correct": correct,
        "per_class": per_class,
        "confusion_matrix": confusion_matrix,
        "identity_merge_error_rates": {
            "false_positive_rate": identity_fp / (identity_fp + identity_tn) if identity_fp + identity_tn else 0,
            "false_negative_rate": identity_fn / (identity_fn + identity_tp) if identity_fn + identity_tp else 0,
            "definition": "Positive means safe same-identity (Exact or Near-Duplicate); Functional-Equivalent is not a positive merge decision.",
        },
        "dataset_sha256": _sha256(MATERIALS_PATH),
        "ground_truth_sha256": _sha256(GROUND_TRUTH_PATH),
        "challenge_sha256": _sha256(CHALLENGE_PATH),
        "model": {
            "name": os.getenv("MODEL_NAME", "all-MiniLM-L6-v2"),
            "version": os.getenv("MODEL_VERSION", "unversioned-development-model"),
            "matcher_version": os.getenv("MATCHER_VERSION", "1.0.0"),
        },
        "weights": {"semantic": WEIGHT_SEMANTIC, "attribute": WEIGHT_ATTRIBUTE, "fuzzy": WEIGHT_FUZZY},
        "thresholds": {
            "exact": THRESHOLD_EXACT,
            "near_duplicate": THRESHOLD_NEAR_DUPLICATE,
            "functional_equivalent": THRESHOLD_FUNCTIONAL_EQUIVALENT,
        },
        "scenario_results": scenario_results,
        "misclassified": [item for item in detailed_results if not item["correct"]],
    }
    if output_path:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2)
        print(f"\nSaved reproducible evaluation artifact to {output_path}")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", help="Write a versioned JSON evaluation artifact")
    args = parser.parse_args()
    main(args.output)
