import asyncio
from unittest.mock import patch, AsyncMock
from types import SimpleNamespace
from tests.test_inventory_import import InventoryImportTests
from app.models.inventory import Inventory
from app.models.material import Material
from app.services.import_service import preview_inventory_import, confirm_inventory_import
from app.services.sap_service import sync_from_sap
from app.services.stock_analytics_service import stock_analytics
from app.models.demand_record import DemandRecord


class OperationalControlsTests(InventoryImportTests):
    def test_completed_stock_import_is_idempotent(self):
        preview = preview_inventory_import(self.db, self.upload("material_code,warehouse,available_quantity\nA-1,MAIN,25\n"), self.cpse_id)
        batch = confirm_inventory_import(self.db, preview["batch_id"])
        self.db.query(Inventory).one().available_quantity = 20
        self.db.commit()
        confirm_inventory_import(self.db, batch.id)
        self.assertEqual(self.db.query(Inventory).one().available_quantity, 20)

    def test_sap_refreshes_existing_material(self):
        connector = SimpleNamespace(name="MOCK", fetch_materials=AsyncMock(return_value=([
            {"material_code": "A-1", "description": "Updated hex bolt", "unit": "EA"}], None)))
        with patch("app.services.sap_service.connector_for", return_value=connector):
            result = asyncio.run(sync_from_sap(self.db, self.cpse_id))
        self.assertEqual(result.records_updated, 1)
        self.assertEqual(self.db.query(Material).one().description, "Updated hex bolt")

    def test_stock_demand_is_month_specific(self):
        material = self.db.query(Material).one()
        self.db.add(Inventory(material_id=material.id, cpse_id=self.cpse_id, warehouse="MAIN", available_quantity=10, reserved_quantity=0, uom="EA"))
        self.db.add(DemandRecord(cpse_id=self.cpse_id, material_id=material.id, period="2026-08", required_quantity=100, uom="EA"))
        self.db.commit()
        result = stock_analytics(self.db, "2026-09")
        self.assertEqual(result["by_unit"][0]["surplus"], 10)
