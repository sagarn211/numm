from types import SimpleNamespace
from fastapi import HTTPException
from tests.test_remediation_flow import RemediationFlowTests
from app.models.material import Material
from app.models.material_mapping import MaterialMapping
from app.models.material_match import MaterialMatch
from app.models.national_material import NationalMaterial
from app.services.approval_service import approve_match
from app.services.mapping_service import map_material
from app.services.national_code_service import create_national_material
from app.routers.procurement import prepare_lines
from app.models.audit_log import AuditLog
from app.services.audit_service import verify_audit_chain, write_audit
from app.models.demand_record import DemandRecord
from app.models.inventory import Inventory
from app.models.procurement_record import ProcurementRecord
from app.services.duplicate_cluster_service import duplicate_clusters
from app.services.national_material_360_service import national_material_360
from app.services.procurement_intelligence_service import procurement_opportunities, reuse_before_buy
from datetime import datetime


class IdentitySafetyTests(RemediationFlowTests):
    def test_duplicate_cluster_keeps_functional_edges_separate(self):
        clusters = duplicate_clusters(self.db)
        self.assertEqual(len(clusters), 1)
        self.assertEqual(clusters[0]["identity_components"], [[self.ids[0], self.ids[1]]])
        self.assertFalse(clusters[0]["automatic_cluster_merge_allowed"])

    def test_match_submitter_cannot_self_approve(self):
        match = self.db.get(MaterialMatch, self.ids[2])
        match.submitted_by = self.ids[3]
        self.db.commit()
        with self.assertRaises(HTTPException) as raised:
            approve_match(self.db, match.id, self.ids[3], "self approval")
        self.assertEqual(raised.exception.status_code, 403)

    def test_procurement_opportunity_and_material_360_use_persisted_records(self):
        first, second, match_id, reviewer = self.ids
        approve_match(self.db, match_id, reviewer, "verified")
        national = self.db.query(NationalMaterial).one()
        a, b = self.db.get(Material, first), self.db.get(Material, second)
        period = datetime.utcnow().strftime("%Y-%m")
        self.db.add_all([
            Inventory(cpse_id=b.cpse_id, material_id=b.id, warehouse="BETA-WH", available_quantity=10, reserved_quantity=0, uom="EA"),
            DemandRecord(cpse_id=a.cpse_id, material_id=a.id, period=period, required_quantity=5, uom="EA"),
            ProcurementRecord(cpse_id=a.cpse_id, material_id=a.id, order_number="PO-A", line_number="1", supplier="Supplier A", period=period, quantity=10, uom="EA", unit_price=20, currency="INR"),
            ProcurementRecord(cpse_id=b.cpse_id, material_id=b.id, order_number="PO-B", line_number="1", supplier="Supplier B", period=period, quantity=10, uom="EA", unit_price=25, currency="INR"),
        ])
        self.db.commit()
        opportunities = procurement_opportunities(self.db, period)
        self.assertEqual(opportunities[0]["cross_cpse_reuse_potential"], 5)
        preview = reuse_before_buy(self.db, national.id, a.cpse_id, 5, "EA", period)
        self.assertEqual(preview["remaining_fresh_procurement"], 0)
        record = national_material_360(self.db, national.id)
        self.assertEqual(len(record["legacy_mappings"]), 2)
        self.assertEqual(record["stock_summary"][0]["ready_to_use"], 10)

    def test_audit_hash_chain_detects_payload_tampering(self):
        write_audit(self.db, "TEST_EVENT", "Material", self.ids[0], self.ids[3], {"state": "original"})
        self.assertEqual(verify_audit_chain(self.db)["status"], "VALID")
        event = self.db.query(AuditLog).filter(AuditLog.action == "TEST_EVENT").one()
        event.details = {"state": "altered"}
        self.db.commit()
        result = verify_audit_chain(self.db)
        self.assertEqual(result["status"], "BROKEN")
        self.assertTrue(any(item["audit_id"] == event.id for item in result["errors"]))

    def test_acknowledgement_cannot_bypass_conflicts(self):
        first, second, match, reviewer = self.ids
        self.db.get(Material, second).specifications = {"grade": "SS316"}
        self.db.commit()
        with self.assertRaises(HTTPException):
            approve_match(self.db, match, reviewer, acknowledge_critical_conflicts=True)
        self.assertEqual(self.db.query(MaterialMapping).count(), 0)

    def test_substitution_does_not_merge_identity(self):
        _, _, match, reviewer = self.ids
        self.db.get(MaterialMatch, match).classification = "FUNCTIONAL_EQUIVALENT"
        self.db.commit()
        approve_match(self.db, match, reviewer, "Ambient service only; engineering review required before use", acknowledge_functional_equivalent=True)
        self.assertEqual(self.db.query(MaterialMapping).count(), 0)
        self.assertEqual(self.db.query(NationalMaterial).count(), 0)

    def test_manual_mapping_checks_existing_group(self):
        first, second, match, reviewer = self.ids
        approve_match(self.db, match, reviewer)
        self.db.get(Material, second).specifications = {"grade": "SS316"}
        self.db.commit()
        with self.assertRaises(HTTPException):
            map_material(self.db, second, self.db.query(NationalMaterial).one().id)

    def test_reuses_canonical_identity(self):
        first = create_national_material(self.db, "HEX BOLT M16", "FASTENERS", "EA", {"grade": "SS304"})
        second = create_national_material(self.db, "HEX BOLT M16", "FASTENERS", "NOS", {"grade": "SS304"})
        self.assertEqual(first.id, second.id)

    def test_procurement_rejects_unknown_material_and_mixed_unit(self):
        material = self.db.get(Material, self.ids[0])
        line = {"material_code": material.material_code, "order_number": "PO1", "line_number": "1", "supplier": "Supplier",
                "period": "2026-09", "quantity": "5", "uom": "KG", "unit_price": "20", "currency": "INR"}
        prepared, errors = prepare_lines(self.db, material.cpse_id, [line])
        self.assertEqual(len(errors), 1)
        line["uom"] = "EA"
        prepared, errors = prepare_lines(self.db, material.cpse_id, [line, line])
        self.assertEqual((len(prepared), len(errors)), (1, 1))
