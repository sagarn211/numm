import unittest
from types import SimpleNamespace

from app.services.classification_service import classify_material
from app.services.conflict_resolution_service import propose_canonical, unresolved_critical_conflicts
from app.services.national_code_service import _check_digit


class RemediationServiceTests(unittest.TestCase):
    def test_classification_assigns_category_and_subcategory(self):
        result = classify_material("Hex bolt M16 x 50 stainless steel 304")
        self.assertEqual(result.category, "FASTENERS")
        self.assertEqual(result.subcategory, "BOLTS")
        self.assertGreater(result.confidence, 0.8)

    def test_classification_uses_attributes_and_preserves_manual_correction(self):
        inferred = classify_material("Industrial component", attributes={"type": "gate valve"})
        self.assertEqual(inferred.subcategory, "GATE VALVES")
        corrected = classify_material("Hex bolt", "SPECIAL CONTROLLED CLASS", prefer_supplied=True)
        self.assertEqual(corrected.category, "SPECIAL CONTROLLED CLASS")
        self.assertEqual(corrected.source, "MANUAL_REVIEW")

    def test_critical_conflict_requires_resolution(self):
        materials = [
            SimpleNamespace(id=1, description="Bolt", cleaned_description="BOLT", category="FASTENERS", subcategory="BOLTS", unit="EA", specifications={"grade": "SS304"}),
            SimpleNamespace(id=2, description="Bolt", cleaned_description="BOLT", category="FASTENERS", subcategory="BOLTS", unit="EA", specifications={"grade": "SS316"}),
        ]
        proposal = propose_canonical(materials)
        self.assertEqual(len(unresolved_critical_conflicts(proposal)), 1)
        resolved = propose_canonical(materials, {"grade": "SS316"})
        self.assertEqual(unresolved_critical_conflicts(resolved, {"grade": "SS316"}), [])

    def test_equivalent_units_do_not_create_a_false_conflict(self):
        materials = [
            SimpleNamespace(id=1, description="ISO pipe", cleaned_description="PIPE", category="PIPES & FITTINGS", subcategory="PIPES", unit="EA", specifications={"diameter": "1 IN"}),
            SimpleNamespace(id=2, description="pipe", cleaned_description="PIPE", category="PIPES & FITTINGS", subcategory="PIPES", unit="EA", specifications={"diameter": "25.4 MM"}),
        ]
        self.assertEqual(propose_canonical(materials)["conflicts"], [])

    def test_national_code_check_digit_is_deterministic(self):
        body = "NMC-FST-BLT-000123"
        self.assertEqual(_check_digit(body), _check_digit(body))
        self.assertRegex(_check_digit(body), r"^[0-9]$")


if __name__ == "__main__":
    unittest.main()
