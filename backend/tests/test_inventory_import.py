from io import BytesIO
from tempfile import TemporaryDirectory
import unittest

from fastapi import UploadFile
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.config.database import Base
from app.config.settings import settings
from app.models.audit_log import AuditLog
from app.models.cpse import CPSE
from app.models.inventory import Inventory
from app.models.material import Material
from app.services.import_service import confirm_inventory_import, preview_inventory_import


class InventoryImportTests(unittest.TestCase):
    def setUp(self):
        engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(engine)
        self.db = sessionmaker(bind=engine)()
        cpse = CPSE(name="Alpha", code="ALPHA", sector="Power")
        self.db.add(cpse); self.db.flush()
        material = Material(cpse_id=cpse.id, material_code="A-1", description="Hex bolt", unit="EA")
        self.db.add(material); self.db.commit()
        self.cpse_id = cpse.id
        self.tempdir = TemporaryDirectory()
        self.old_upload_dir = settings.UPLOAD_DIR
        settings.UPLOAD_DIR = self.tempdir.name

    def tearDown(self):
        settings.UPLOAD_DIR = self.old_upload_dir
        self.tempdir.cleanup()
        self.db.close()

    @staticmethod
    def upload(content):
        return UploadFile(filename="stock.csv", file=BytesIO(content.encode()))

    def test_creates_inventory_and_audits_batch(self):
        preview = preview_inventory_import(
            self.db,
            self.upload("material_code,warehouse,available_quantity,reserved_quantity,uom,unit_cost\nA-1,MAIN,25,3,EA,12.5\n"),
            self.cpse_id,
        )
        self.assertEqual(preview["valid_rows"], 1)
        batch = confirm_inventory_import(self.db, preview["batch_id"])
        inventory = self.db.query(Inventory).one()
        self.assertEqual((inventory.warehouse, inventory.available_quantity, inventory.reserved_quantity), ("MAIN", 25, 3))
        self.assertEqual(batch.successful_rows, 1)
        self.assertTrue(self.db.query(AuditLog).filter(AuditLog.action == "INVENTORY_IMPORT_COMPLETED").first())

    def test_explicit_update_policy_updates_existing_stock(self):
        material = self.db.query(Material).one()
        self.db.add(Inventory(cpse_id=self.cpse_id, material_id=material.id, warehouse="MAIN", available_quantity=5, reserved_quantity=0, uom="EA"))
        self.db.commit()
        csv = "material_code,warehouse,available_quantity,reserved_quantity\nA-1,main,40,4\n"
        rejected = preview_inventory_import(self.db, self.upload(csv), self.cpse_id, "REJECT")
        self.assertEqual(rejected["error_rows"], 1)
        update = preview_inventory_import(self.db, self.upload(csv), self.cpse_id, "UPDATE")
        self.assertEqual((update["valid_rows"], update["warning_rows"]), (1, 1))
        confirm_inventory_import(self.db, update["batch_id"])
        inventory = self.db.query(Inventory).one()
        self.assertEqual((inventory.available_quantity, inventory.reserved_quantity), (40, 4))

    def test_invalid_quantities_are_skipped(self):
        preview = preview_inventory_import(
            self.db,
            self.upload("material_code,warehouse,available_quantity,reserved_quantity\nA-1,MAIN,2,3\n"),
            self.cpse_id,
        )
        self.assertEqual((preview["valid_rows"], preview["error_rows"]), (0, 1))


if __name__ == "__main__":
    unittest.main()
