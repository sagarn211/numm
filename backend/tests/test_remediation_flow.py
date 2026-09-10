import unittest
from fastapi import HTTPException

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.config.database import Base
from app.models.audit_log import AuditLog
from app.models.cpse import CPSE
from app.models.import_batch import ImportBatch
from app.models.material import Material
from app.models.material_mapping import MaterialMapping
from app.models.material_match import MaterialMatch
from app.models.national_material import NationalMaterial
from app.models.user import User
from app.services.approval_service import approve_match, auto_approve_exact_matches
from app.services.dashboard_service import comprehensive_dashboard_metrics
from app.services.export_service import export_csv
from app.services.import_service import queue_import


class RemediationFlowTests(unittest.TestCase):
    def setUp(self):
        engine = create_engine(
            "sqlite://", connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(engine)
        self.db = sessionmaker(bind=engine)()
        cpse_a = CPSE(name="Alpha", code="ALPHA", sector="Power")
        cpse_b = CPSE(name="Beta", code="BETA", sector="Power")
        reviewer = User(name="Reviewer", email="reviewer@example.test", password_hash="test", role="REVIEWER")
        self.db.add_all([cpse_a, cpse_b, reviewer]); self.db.flush()
        first = Material(cpse_id=cpse_a.id, material_code="A-1", description="HEX BOLT M16X50 SS304", cleaned_description="HEX BOLT M16X50 SS304", category="FASTENERS", subcategory="BOLTS", unit="EA", specifications={"grade": "SS304"})
        second = Material(cpse_id=cpse_b.id, material_code="B-1", description="HEXAGONAL BOLT M16 X 50 SS304", cleaned_description="HEXAGONAL BOLT M16 X 50 SS304", category="FASTENERS", subcategory="BOLTS", unit="EA", specifications={"grade": "SS304"})
        self.db.add_all([first, second]); self.db.flush()
        match = MaterialMatch(material_a_id=first.id, material_b_id=second.id, semantic_score=0.96, attribute_score=1.0, fuzzy_score=0.92, final_score=0.97, classification="EXACT", status="PENDING")
        self.db.add(match); self.db.commit()
        self.ids = first.id, second.id, match.id, reviewer.id

    def tearDown(self):
        self.db.close()

    def test_approval_creates_code_mappings_audit_dashboard_and_export(self):
        first_id, second_id, match_id, reviewer_id = self.ids
        approved = approve_match(self.db, match_id, reviewer_id, "verified")
        self.assertEqual(approved.status, "APPROVED")
        national = self.db.query(NationalMaterial).one()
        self.assertRegex(national.national_code, r"^NMC-FST-BLT-\d{6}-\d$")
        mappings = self.db.query(MaterialMapping).all()
        self.assertEqual({item.material_id for item in mappings}, {first_id, second_id})
        self.assertTrue(self.db.query(AuditLog).filter(AuditLog.action == "MATCH_APPROVED").first())
        self.assertEqual(self.db.query(AuditLog).filter(AuditLog.action == "MAPPING_CREATED").count(), 2)
        metrics = comprehensive_dashboard_metrics(self.db)
        self.assertEqual(metrics["mapping_coverage_percent"], 100.0)
        self.assertIn(national.national_code, export_csv(self.db).decode())

    def test_functional_equivalent_requires_explicit_policy_acknowledgement(self):
        _first_id, _second_id, match_id, reviewer_id = self.ids
        match = self.db.query(MaterialMatch).filter(MaterialMatch.id == match_id).one()
        match.classification = "FUNCTIONAL_EQUIVALENT"
        self.db.commit()
        with self.assertRaises(HTTPException) as raised:
            approve_match(self.db, match_id, reviewer_id, "reviewed")
        self.assertEqual(raised.exception.status_code, 409)
        approved = approve_match(
            self.db, match_id, reviewer_id, "reviewed",
            acknowledge_functional_equivalent=True,
        )
        self.assertEqual(approved.status, "APPROVED")

    def test_high_confidence_exact_match_is_automatically_approved(self):
        result = auto_approve_exact_matches(self.db, min_score=0.95)
        self.assertEqual(result["approved_ids"], [self.ids[2]])
        match = self.db.query(MaterialMatch).filter(
            MaterialMatch.id == self.ids[2]
        ).one()
        self.assertEqual(match.status, "APPROVED")
        self.assertEqual(self.db.query(NationalMaterial).count(), 1)
        self.assertEqual(self.db.query(MaterialMapping).count(), 2)
        action = self.db.query(AuditLog).filter(
            AuditLog.action == "MATCH_AUTO_APPROVED"
        ).one()
        self.assertIsNone(action.user_id)

    def test_failed_ai_stage_can_be_requeued_without_reimporting_rows(self):
        cpse_id = self.db.query(CPSE.id).first()[0]
        reviewer_id = self.ids[3]
        batch = ImportBatch(
            filename="already-imported.csv",
            file_type="csv",
            cpse_id=cpse_id,
            total_rows=2,
            successful_rows=2,
            processed_rows=2,
            progress_percent=100,
            status="COMPLETED_WITH_AI_ERROR",
            current_stage="AI_CANDIDATES_FAILED",
            error_message="timed out",
        )
        self.db.add(batch)
        self.db.commit()

        queued, should_enqueue = queue_import(
            self.db,
            batch.id,
            "already-imported-ai-retry",
            reviewer_id,
        )

        self.assertEqual(queued.status, "AI_QUEUED")
        self.assertTrue(should_enqueue)
        self.assertEqual(queued.current_stage, "AI_QUEUED")
        self.assertEqual(queued.successful_rows, 2)
        self.assertEqual(queued.progress_percent, 100)
        self.assertIsNone(queued.error_message)
        self.assertTrue(
            self.db.query(AuditLog).filter(
                AuditLog.action == "IMPORT_AI_RETRY_QUEUED"
            ).first()
        )
        same_batch, should_enqueue_again = queue_import(
            self.db,
            batch.id,
            "already-imported-ai-retry-second-click",
            reviewer_id,
        )
        self.assertEqual(same_batch.id, batch.id)
        self.assertFalse(should_enqueue_again)


if __name__ == "__main__":
    unittest.main()
