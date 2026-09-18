from app.models.material import Material
from app.models.national_material import NationalMaterial
from app.models.procurement_record import ProcurementRecord
from app.services.approval_service import approve_match
from app.services.price_intelligence_service import material_price_intelligence
from tests.test_remediation_flow import RemediationFlowTests


class PriceIntelligenceTests(RemediationFlowTests):
    def _national(self):
        first, second, match_id, reviewer = self.ids
        approve_match(self.db, match_id, reviewer, "verified")
        return self.db.query(NationalMaterial).one(), self.db.get(Material, first), self.db.get(Material, second)

    def test_quantity_weighted_monthly_price_and_movement(self):
        national, first, second = self._national()
        self.db.add_all([
            ProcurementRecord(cpse_id=first.cpse_id, material_id=first.id, order_number="P1", line_number="1", supplier="A", period="2026-01", quantity=1000, uom="EA", unit_price=80, currency="INR"),
            ProcurementRecord(cpse_id=second.cpse_id, material_id=second.id, order_number="P2", line_number="1", supplier="B", period="2026-01", quantity=2000, uom="EA", unit_price=75, currency="INR"),
            ProcurementRecord(cpse_id=first.cpse_id, material_id=first.id, order_number="P3", line_number="1", supplier="A", period="2026-02", quantity=500, uom="EA", unit_price=90, currency="INR"),
        ])
        self.db.commit()
        result = material_price_intelligence(self.db, national.id)
        self.assertEqual(result["series"][0]["weighted_avg_unit_price"], 76.6667)
        self.assertEqual(result["latest_weighted_avg"], 90.0)
        self.assertEqual(result["direction"], "UP")
        self.assertEqual(result["participating_cpse_count"], 2)

    def test_uom_and_currency_conflicts_are_not_combined(self):
        national, first, second = self._national()
        self.db.add_all([
            ProcurementRecord(cpse_id=first.cpse_id, material_id=first.id, order_number="P1", line_number="1", supplier="A", period="2026-01", quantity=10, uom="EA", unit_price=20, currency="INR"),
            ProcurementRecord(cpse_id=second.cpse_id, material_id=second.id, order_number="P2", line_number="1", supplier="B", period="2026-01", quantity=10, uom="KG", unit_price=5, currency="USD"),
        ])
        self.db.commit()
        result = material_price_intelligence(self.db, national.id)
        self.assertTrue(result["data_quality"]["uom_conflict"])
        self.assertTrue(result["data_quality"]["currency_conflict"])
        self.assertIsNone(result["latest_weighted_avg"])
        inr = material_price_intelligence(self.db, national.id, uom="EA", currency="INR")
        self.assertEqual(inr["latest_weighted_avg"], 20.0)
