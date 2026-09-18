import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.config.database import Base
from app.models.cpse import CPSE
from app.models.material import Material
from app.models.material_match import MaterialMatch
from app.services.cluster_governance_service import generate_proposed_clusters


class ClusterGenerationIntegrityTests(unittest.TestCase):
    def setUp(self):
        engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(engine)
        self.db = sessionmaker(bind=engine)()
        cpse = CPSE(name="Alpha", code="ALPHA", sector="Power")
        self.db.add(cpse)
        self.db.flush()
        self.materials = [
            Material(cpse_id=cpse.id, material_code=f"M-{index}", description=f"Bolt {index}",
                     cleaned_description=f"BOLT {index}", category="FASTENERS", subcategory="BOLTS",
                     unit="EA", specifications={"grade": "SS304"})
            for index in range(1, 4)
        ]
        self.db.add_all(self.materials)
        self.db.flush()

    def tearDown(self):
        self.db.close()

    def _match(self, left, right):
        self.db.add(MaterialMatch(material_a_id=left.id, material_b_id=right.id, semantic_score=.96,
                    attribute_score=.96, fuzzy_score=.96, final_score=.96,
                    classification="EXACT", status="PENDING"))
        self.db.commit()

    def test_new_evidence_does_not_create_an_overlapping_identity_cluster(self):
        first, second, third = self.materials
        self._match(first, second)
        self.assertEqual(len(generate_proposed_clusters(self.db)), 1)

        # Subsequent evidence expands the AI component, but the existing active
        # governance unit remains authoritative until a reviewer resolves it.
        self._match(second, third)
        self.assertEqual(generate_proposed_clusters(self.db), [])


if __name__ == "__main__":
    unittest.main()
