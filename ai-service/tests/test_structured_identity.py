import unittest
from src.structured_identity import enforce_structured_evidence, matching_text


class StructuredIdentityTests(unittest.TestCase):
    def test_structured_conflict_overrides_identical_descriptions(self):
        left = {"description": "MOTOR", "specifications": {"voltage": "230V"}}
        right = {"description": "MOTOR", "specifications": {"voltage": "415V"}}
        result = enforce_structured_evidence({"label": "Exact", "match_score": 1}, left, right)
        self.assertEqual(result["label"], "No-Match")

    def test_convertible_voltage_is_not_conflicting(self):
        result = enforce_structured_evidence({"label": "Exact", "match_score": 1},
            {"specifications": {"voltage": "1KV"}}, {"specifications": {"voltage": "1000V"}})
        self.assertEqual(result["label"], "Exact")

    def test_missing_identity_evidence_requires_review(self):
        result = enforce_structured_evidence({"label": "Exact", "match_score": 1},
            {"specifications": {"grade": "SS304"}}, {"specifications": {}})
        self.assertEqual(result["label"], "Near-Duplicate")
