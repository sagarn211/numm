import unittest

from app.engine_adapter import run_batch, select_candidate_pairs
from src.fallback_matcher import compare


def material(material_id, description, category):
    return {
        "id": material_id,
        "description": description,
        "cleaned_description": description,
        "category": category,
        "specifications": {},
    }


class CandidateSelectionTests(unittest.TestCase):
    def test_selects_similar_materials_and_rejects_different_types(self):
        materials = [
            material(1, "SS316 BALL VALVE DN50 PN16 FLANGED", "Valves"),
            material(2, "BALL VALVE SS 316 DN50 PN16 FLANGE", "Valves"),
            material(3, "ELECTRIC MOTOR 45 KW 1450 RPM", "Motors"),
        ]

        pairs = select_candidate_pairs(materials)
        pair_ids = {(left["id"], right["id"]) for left, right in pairs}

        self.assertEqual(pair_ids, {(1, 2)})

    def test_caps_candidates_and_never_returns_reversed_duplicates(self):
        materials = [
            material(i, f"COPPER CABLE 3C X 16 SQ MM MODEL {i}", "Cable")
            for i in range(1, 8)
        ]

        pairs = select_candidate_pairs(materials, max_candidates=2)
        pair_ids = [(left["id"], right["id"]) for left, right in pairs]
        degree = {material["id"]: 0 for material in materials}
        for left, right in pair_ids:
            self.assertLess(left, right)
            degree[left] += 1
            degree[right] += 1

        self.assertEqual(len(pair_ids), len(set(pair_ids)))
        self.assertTrue(all(count <= 2 for count in degree.values()))

    def test_batch_does_not_return_no_match_candidates(self):
        materials = [
            material(1, "BALL VALVE SS316 DN50 PN16", "Valves"),
            material(2, "BALL VALVE SS316 DN50 PN16", "Valves"),
            material(3, "BALL VALVE SS316 DN100 PN40", "Valves"),
        ]

        matches = run_batch(materials)

        self.assertTrue(matches)
        self.assertTrue(all(match["label"] != "NO_MATCH" for match in matches))

    def test_fallback_distinguishes_fractional_metric_pitch(self):
        left = material(10, "HEX BOLT M16 X 1.5 SS304", "Fasteners")
        right = material(11, "HEX BOLT M16 X 1.25 SS304", "Fasteners")
        self.assertEqual(compare(left, right)["label"], "NO_MATCH")


if __name__ == "__main__":
    unittest.main()
