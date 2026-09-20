import os
import time
import unittest
import httpx

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
AI_URL = os.getenv("AI_SERVICE_URL", "http://localhost:8001")
SAP_URL = os.getenv("MOCK_SAP_URL", "http://localhost:8002")

class TestNUMMEndToEndIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.run_suffix = str(time.time_ns())[-10:]
        cls.material_code_a = f"E2E-FST-A-{cls.run_suffix}"
        cls.material_code_b = f"E2E-FST-B-{cls.run_suffix}"
        cls.async_material_code = f"E2E-ASYNC-{cls.run_suffix}"
        cls.client = httpx.Client(base_url=BACKEND_URL, timeout=30.0)
        login = cls.client.post(
            "/api/auth/login",
            data={"username": "r.kumar@numm.gov.in", "password": "admin123"},
        )
        if login.status_code == 200:
            token = login.json().get("access_token") or login.json().get("token")
            cls.client.headers.update({"Authorization": f"Bearer {token}"})

    @classmethod
    def tearDownClass(cls):
        cls.client.close()

    def test_01_service_health(self):
        """Verify health checks of Backend, AI service, and Mock SAP"""
        r_backend = self.client.get("/health")
        self.assertEqual(r_backend.status_code, 200, f"Backend health failed: {r_backend.text}")
        self.assertEqual(r_backend.json().get("status"), "ok")

        with httpx.Client(timeout=10.0) as cl:
            r_ai = cl.get(f"{AI_URL}/health")
            self.assertEqual(r_ai.status_code, 200, f"AI health failed: {r_ai.text}")
            self.assertEqual(r_ai.json().get("status"), "ok")
            self.assertTrue(r_ai.json().get("model_loaded"))

            r_sap = cl.get(f"{SAP_URL}/health")
            self.assertEqual(r_sap.status_code, 200, f"Mock SAP health failed: {r_sap.text}")
            self.assertEqual(r_sap.json().get("status"), "ok")

    def test_02_authentication_flow(self):
        """Test valid login, invalid credentials, token generation, and /api/auth/me"""
        # Invalid password
        r_fail = self.client.post(
            "/api/auth/login",
            data={"username": "officer@numm.gov.in", "password": "wrongpassword"}
        )
        self.assertEqual(r_fail.status_code, 401)

        # Invalid username
        r_fail_user = self.client.post(
            "/api/auth/login",
            data={"username": "nonexistent@numm.gov.in", "password": "any"}
        )
        self.assertEqual(r_fail_user.status_code, 401)

        # Valid login
        r_login = self.client.post(
            "/api/auth/login",
            data={"username": "officer@numm.gov.in", "password": "officer123"}
        )
        self.assertEqual(r_login.status_code, 200)
        data = r_login.json()
        token = data.get("access_token") or data.get("token")
        self.assertIsNotNone(token)
        self.assertEqual(data["user"]["email"], "officer@numm.gov.in")

        # Test authenticated /me
        r_me = self.client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(r_me.status_code, 200)
        self.assertEqual(r_me.json()["email"], "officer@numm.gov.in")

    def test_03_cpse_management(self):
        """Verify CPSE listing and dynamic creation in database"""
        r_list = self.client.get("/api/cpses")
        self.assertEqual(r_list.status_code, 200)
        cpses = r_list.json()
        self.assertGreater(len(cpses), 0)
        codes = [c["code"] for c in cpses]
        self.assertIn("ONGC", codes)
        self.assertIn("NTPC", codes)

        # Create new CPSE
        test_code = "TEST_E2E_CPSE"
        if test_code not in codes:
            r_create = self.client.post("/api/cpses", json={
                "name": "E2E Testing Corporation",
                "code": test_code,
                "sector": "Power"
            })
            self.assertIn(r_create.status_code, [200, 201])
            self.assertEqual(r_create.json()["code"], test_code)

    def test_04_material_master_operations(self):
        """Verify listing materials, search query, category filter, and material detail"""
        r_all = self.client.get("/api/materials")
        self.assertEqual(r_all.status_code, 200)
        materials = r_all.json()
        self.assertGreater(len(materials), 0)

        # Search query
        r_search = self.client.get("/api/materials", params={"search": "Valve"})
        self.assertEqual(r_search.status_code, 200)
        valve_results = r_search.json()
        self.assertGreater(len(valve_results), 0)
        for v in valve_results:
            self.assertTrue("valve" in v["description"].lower() or "valv" in (v.get("category") or "").lower())

        # Detail of first material
        first_id = materials[0]["id"]
        r_detail = self.client.get(f"/api/materials/{first_id}")
        self.assertEqual(r_detail.status_code, 200)
        self.assertEqual(r_detail.json()["id"], first_id)

    def test_05_csv_import_workflow(self):
        """Test file preview, validation, confirmation, and DB insertion using real CSV content"""
        # Find ONGC CPSE ID
        cpses = self.client.get("/api/cpses").json()
        ongc_id = next(c["id"] for c in cpses if c["code"] == "ONGC")

        csv_content = (
            "material_code,description,category,unit,manufacturer\n"
            f"{self.material_code_a},HEX BOLT M16X50 SS304 HIGH TENSILE,FASTENER,NOS,PrecisionFast\n"
            f"{self.material_code_b},SS304 HEXAGONAL HEAD BOLT M16 X 50 MM,FASTENER,NOS,PrecisionFast\n"
        )
        files = {"file": ("e2e_test_materials.csv", csv_content.encode("utf-8"), "text/csv")}
        data = {"cpse_id": str(ongc_id)}

        # Preview & Validate
        r_prev = self.client.post("/api/imports/preview", files=files, data=data)
        self.assertEqual(r_prev.status_code, 200)
        prev_data = r_prev.json()
        batch_id = prev_data.get("batch_id")
        self.assertIsNotNone(batch_id)
        self.assertEqual(prev_data["valid_rows"], 2)

        # Confirm Import
        r_conf = self.client.post(f"/api/imports/{batch_id}/confirm")
        self.assertEqual(r_conf.status_code, 200)
        self.assertIn("COMPLETED", r_conf.json()["status"])

        # Verify materials appear in master list
        r_check = self.client.get("/api/materials", params={"search": self.material_code_a})
        self.assertEqual(r_check.status_code, 200)
        self.assertGreaterEqual(len(r_check.json()), 1)

    def test_06_ai_matching_service_integration(self):
        """Test backend calling real AI and persisting a focused candidate pair."""
        # Verify AI health through backend proxy
        r_health = self.client.get("/api/matching/health")
        self.assertEqual(r_health.status_code, 200)
        self.assertEqual(r_health.json()["status"], "ok")

        source_a = self.client.get("/api/materials", params={"search": self.material_code_a}).json()[0]
        source_b = self.client.get("/api/materials", params={"search": self.material_code_b}).json()[0]
        comparison = self.client.post("/api/matching/compare", json={
            "material_a_id": source_a["id"], "material_b_id": source_b["id"],
        })
        self.assertEqual(comparison.status_code, 200, comparison.text)
        self.assertIn(comparison.json()["classification"], {"EXACT", "NEAR_DUPLICATE"})
        submitted = self.client.post(f"/api/matching/similar/{source_a['id']}/submit/{source_b['id']}")
        self.assertEqual(submitted.status_code, 200, submitted.text)

        # List matches
        r_list = self.client.get("/api/matching")
        self.assertEqual(r_list.status_code, 200)
        all_matches = r_list.json()
        self.assertGreater(len(all_matches), 0)

        for m in all_matches:
            self.assertIn("final_score", m)
            self.assertIn("classification", m)
            self.assertIn("status", m)

    def test_07_approval_and_national_mapping_flow(self):
        """Approve a persisted identity cluster and create its national mapping."""
        source_a = self.client.get("/api/materials", params={"search": self.material_code_a}).json()[0]
        source_b = self.client.get("/api/materials", params={"search": self.material_code_b}).json()[0]
        generated = self.client.post("/api/clusters/generate")
        self.assertEqual(generated.status_code, 200, generated.text)
        clusters = generated.json()["clusters"]
        target_cluster = next(
            (
                cluster for cluster in clusters
                if {member["material_id"] for member in cluster["identity_members"]}
                == {source_a["id"], source_b["id"]}
            ),
            None,
        )
        self.assertIsNotNone(target_cluster, "AI run did not create the expected identity cluster")
        if target_cluster is not None:
            cluster_id = target_cluster["id"]
            if target_cluster["status"] == "PROPOSED":
                started = self.client.post(f"/api/clusters/{cluster_id}/start-review")
                self.assertEqual(started.status_code, 200, started.text)
                submitted = self.client.post(
                    f"/api/clusters/{cluster_id}/submit",
                    json={"comment": "E2E integration test submission"},
                )
                self.assertEqual(submitted.status_code, 200, submitted.text)

            reviewer_login = self.client.post(
                "/api/auth/login",
                data={"username": "a.sen@numm.gov.in", "password": "officer123"},
            )
            self.assertEqual(reviewer_login.status_code, 200, reviewer_login.text)
            reviewer_headers = {
                "Authorization": f"Bearer {reviewer_login.json()['access_token']}"
            }
            r_approve = self.client.post(
                f"/api/clusters/{cluster_id}/approve",
                json={"comment": "E2E integration test officer approval"},
                headers=reviewer_headers,
            )
            self.assertEqual(r_approve.status_code, 200, r_approve.text)
            self.assertEqual(r_approve.json()["status"], "APPROVED")

            material_codes = []
            for material_id in (source_a["id"], source_b["id"]):
                material = self.client.get(f"/api/materials/{material_id}")
                self.assertEqual(material.status_code, 200)
                self.assertTrue(material.json().get("national_code"))
                material_codes.append(material.json()["national_code"])
            self.assertEqual(material_codes[0], material_codes[1])

            audit = self.client.get("/api/audit").json()
            self.assertTrue(any(log["action"] == "CLUSTER_APPROVED" and log["entity_id"] == cluster_id for log in audit))
            dashboard = self.client.get("/api/dashboard/stats").json()
            self.assertGreaterEqual(dashboard["mapped_materials"], 2)
            exported = self.client.get("/api/exports/national-registry.csv")
            self.assertEqual(exported.status_code, 200)
            self.assertIn(material_codes[0], exported.text)

            detail = self.client.get(f"/api/clusters/detail/{cluster_id}")
            self.assertEqual(detail.status_code, 200, detail.text)
            self.assertEqual(detail.json()["status"], "APPROVED")

    def test_08_national_material_master_registry(self):
        """Test National Material listing, creation, and detail with mappings"""
        r_nats = self.client.get("/api/national-materials")
        self.assertEqual(r_nats.status_code, 200)
        nationals = r_nats.json()
        self.assertGreater(len(nationals), 0)

        first_nat = nationals[0]
        self.assertTrue(first_nat["national_code"].startswith(("NM-", "NMC-")))

        # Detail with mappings
        r_detail = self.client.get(f"/api/national-materials/{first_nat['id']}")
        self.assertEqual(r_detail.status_code, 200)
        data = r_detail.json()
        self.assertIn("material", data)
        self.assertIn("mappings", data)

        # Availability
        r_avail = self.client.get(f"/api/national-materials/{first_nat['id']}/availability")
        self.assertEqual(r_avail.status_code, 200)
        self.assertIn("total_available", r_avail.json())

    def test_09_cross_cpse_inventory(self):
        """Test inventory record creation and querying"""
        cpses = self.client.get("/api/cpses").json()
        materials = self.client.get("/api/materials").json()
        self.assertGreater(len(cpses), 0)
        self.assertGreater(len(materials), 0)

        mapped_material = next(
            material for material in materials if material.get("national_code")
        )
        mapped_national = next(
            national for national in self.client.get("/api/national-materials").json()
            if national["national_code"] == mapped_material["national_code"]
        )

        # Use a material-specific warehouse and reset it when this suite is retried.
        warehouse = f"E2E Testing Depot {mapped_material['id']}"
        existing = next(
            (item for item in self.client.get("/api/inventory", params={"material_id": mapped_material["id"]}).json()
             if item["warehouse"] == warehouse),
            None,
        )
        stock_payload = {
            "available_quantity": 50,
            "reserved_quantity": 0,
            "uom": mapped_material["unit"],
        }
        if existing:
            r_add = self.client.put(f"/api/inventory/{existing['id']}", json=stock_payload)
        else:
            r_add = self.client.post("/api/inventory", json={
                "cpse_id": mapped_material["cpse_id"],
                "material_id": mapped_material["id"],
                "warehouse": warehouse,
                **stock_payload,
            })
        self.assertEqual(r_add.status_code, 200)
        inv_record = r_add.json()
        self.assertEqual(inv_record["available_quantity"], 50)
        self.__class__.stocked_national_id = mapped_national["id"]
        self.__class__.stocked_cpse_id = mapped_material["cpse_id"]
        self.__class__.stocked_uom = mapped_material["unit"]

        # List inventory
        r_inv_list = self.client.get("/api/inventory")
        self.assertEqual(r_inv_list.status_code, 200)
        self.assertGreater(len(r_inv_list.json()), 0)

    def test_10_material_request_and_reservation(self):
        """Test reuse preview, reservation, maker-checker approval, and fulfillment."""
        cpses = self.client.get("/api/cpses").json()
        self.assertGreater(len(cpses), 0)
        self.assertTrue(hasattr(self.__class__, "stocked_national_id"))

        # Create draft request
        r_draft = self.client.post("/api/requests", json={
            "requesting_cpse_id": self.__class__.stocked_cpse_id,
            "notes": "E2E Material Reservation Request"
        })
        self.assertEqual(r_draft.status_code, 200)
        draft = r_draft.json()
        req_id = draft["id"]
        self.assertEqual(draft["status"], "DRAFT")

        # Add item to request
        r_item = self.client.post(f"/api/requests/{req_id}/items", json={
            "national_material_id": self.__class__.stocked_national_id,
            "requested_quantity": 5,
            "uom": self.__class__.stocked_uom,
        })
        self.assertEqual(r_item.status_code, 200)

        reuse = self.client.post("/api/procurement/reuse-preview", json={
            "national_material_id": self.__class__.stocked_national_id,
            "requesting_cpse_id": self.__class__.stocked_cpse_id,
            "requested_quantity": 5,
            "uom": self.__class__.stocked_uom,
        })
        self.assertEqual(reuse.status_code, 200, reuse.text)
        self.assertGreaterEqual(reuse.json()["own_available"], 5)
        self.assertEqual(reuse.json()["remaining_fresh_procurement"], 0)

        material_360 = self.client.get(
            f"/api/national-materials/{self.__class__.stocked_national_id}/360"
        )
        self.assertEqual(material_360.status_code, 200, material_360.text)
        self.assertTrue(any(
            row["available"] >= 5
            for row in material_360.json()["stock_summary"]
        ))

        # Submit request
        r_submit = self.client.post(f"/api/requests/{req_id}/submit")
        self.assertEqual(r_submit.status_code, 200)
        self.assertEqual(r_submit.json()["status"], "SUBMITTED")

        reviewer_login = self.client.post(
            "/api/auth/login",
            data={"username": "a.sen@numm.gov.in", "password": "officer123"},
        )
        self.assertEqual(reviewer_login.status_code, 200, reviewer_login.text)
        reviewer_headers = {
            "Authorization": f"Bearer {reviewer_login.json()['access_token']}"
        }
        approved = self.client.post(
            f"/api/requests/{req_id}/approve", headers=reviewer_headers,
        )
        self.assertEqual(approved.status_code, 200, approved.text)
        self.assertEqual(approved.json()["status"], "APPROVED")
        fulfilled = self.client.post(
            f"/api/requests/{req_id}/fulfill", headers=reviewer_headers,
        )
        self.assertEqual(fulfilled.status_code, 200, fulfilled.text)
        self.assertEqual(fulfilled.json()["status"], "FULFILLED")
        request_detail = self.client.get(f"/api/requests/{req_id}")
        self.assertEqual(request_detail.status_code, 200, request_detail.text)
        self.assertTrue(request_detail.json()["allocations"])
        self.assertTrue(all(
            allocation["status"] == "ALLOCATED"
            for allocation in request_detail.json()["allocations"]
        ))

    def test_11_mock_sap_sync_integration(self):
        """Test Backend pulling catalog materials from Mock SAP service"""
        cpses = self.client.get("/api/cpses").json()
        ongc_id = next(c["id"] for c in cpses if c["code"] == "ONGC")

        r_sync = self.client.post("/api/integrations/sap/sync", json={"cpse_id": ongc_id})
        self.assertEqual(r_sync.status_code, 200)
        sync_result = r_sync.json()
        self.assertIn(sync_result.get("status"), ["COMPLETED", "RUNNING"])

        # Check SAP history
        r_hist = self.client.get("/api/integrations/sap/history")
        self.assertEqual(r_hist.status_code, 200)
        self.assertGreater(len(r_hist.json()), 0)

    def test_12_dashboard_and_audit_trail(self):
        """Verify real dashboard aggregation and immutable audit logs"""
        r_dash = self.client.get("/api/dashboard/stats")
        self.assertEqual(r_dash.status_code, 200)
        d = r_dash.json()
        self.assertGreater(d["total_cpses"], 0)
        self.assertGreater(d["total_materials"], 0)
        self.assertGreater(d["total_national_materials"], 0)

        r_audit = self.client.get("/api/audit")
        self.assertEqual(r_audit.status_code, 200)
        logs = r_audit.json()
        self.assertGreater(len(logs), 0)
        for log in logs:
            self.assertIn("action", log)
            self.assertIn("created_at", log)

    def test_13_duplicate_import_is_rejected(self):
        cpses = self.client.get("/api/cpses").json()
        ongc_id = next(c["id"] for c in cpses if c["code"] == "ONGC")
        csv_content = (
            "material_code,description,unit\n"
            f"{self.material_code_a},Duplicate bolt,NOS\n"
        )
        response = self.client.post(
            "/api/imports/preview",
            files={"file": ("duplicate.csv", csv_content.encode(), "text/csv")},
            data={"cpse_id": str(ongc_id)},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["error_rows"], 1)

    def test_14_unauthorized_approval_is_forbidden(self):
        login = self.client.post(
            "/api/auth/login",
            data={"username": "requester@numm.gov.in", "password": "requester123"},
        )
        self.assertEqual(login.status_code, 200, login.text)
        token = login.json()["access_token"]
        requester_headers = {"Authorization": f"Bearer {token}"}
        response = self.client.post(
            "/api/clusters/generate",
            json={}, headers=requester_headers,
        )
        self.assertEqual(response.status_code, 403)

        requester = self.client.get("/api/auth/me", headers=requester_headers).json()
        scoped_materials = self.client.get(
            "/api/materials", headers=requester_headers,
        )
        self.assertEqual(scoped_materials.status_code, 200)
        self.assertTrue(all(
            item["cpse_id"] == requester["cpse_id"]
            for item in scoped_materials.json()
        ))
        foreign = next(
            item for item in self.client.get("/api/materials").json()
            if item["cpse_id"] != requester["cpse_id"]
        )
        forbidden_detail = self.client.get(
            f"/api/materials/{foreign['id']}", headers=requester_headers,
        )
        self.assertEqual(forbidden_detail.status_code, 403)

    def test_15_rejection_flow(self):
        pending = self.client.get("/api/approvals", params={"status": "PENDING"}).json()
        self.assertTrue(pending, "Expected at least one remaining candidate for rejection")
        response = self.client.post(
            f"/api/approvals/{pending[0]['id']}/reject",
            json={"comment": "E2E rejection coverage"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "REJECTED")

    def test_16_sap_failure_is_safe_and_audited(self):
        cpse_id = self.client.get("/api/cpses").json()[0]["id"]
        response = self.client.post(
            "/api/integrations/sap/sync",
            json={"cpse_id": cpse_id, "connector": "ODATA"},
        )
        self.assertEqual(response.status_code, 502)
        audit = self.client.get("/api/audit").json()
        self.assertTrue(any(item["action"] == "SAP_SYNC_FAILED" for item in audit))

    def test_17_async_import_worker_and_ai_stage(self):
        cpse_id = next(
            cpse["id"] for cpse in self.client.get("/api/cpses").json()
            if cpse["code"] == "ONGC"
        )
        csv_content = (
            "material_code,description,category,unit\n"
            f"{self.async_material_code},HEX BOLT M16 X 50 SS304,FASTENER,NOS\n"
        )
        preview = self.client.post(
            "/api/imports/preview",
            files={"file": ("async.csv", csv_content.encode(), "text/csv")},
            data={"cpse_id": str(cpse_id)},
        )
        self.assertEqual(preview.status_code, 200, preview.text)
        batch_id = preview.json()["batch_id"]
        queued = self.client.post(
            f"/api/imports/{batch_id}/queue",
            headers={"Idempotency-Key": f"e2e-async-import-{self.run_suffix}"},
        )
        self.assertEqual(queued.status_code, 200, queued.text)
        self.assertIn(queued.json()["status"], {"QUEUED", "PROCESSING", "COMPLETED"})

        status = "QUEUED"
        stage = "QUEUED"
        for _ in range(40):
            job = self.client.get(f"/api/imports/{batch_id}/status")
            self.assertEqual(job.status_code, 200, job.text)
            status = job.json()["status"]
            stage = job.json().get("current_stage")
            if stage in {"COMPLETED", "AI_CANDIDATES_FAILED", "FAILED"}:
                break
            time.sleep(0.25)
        self.assertIn(status, {"COMPLETED", "COMPLETED_WITH_ERRORS"})
        self.assertEqual(stage, "COMPLETED")
        imported = self.client.get(
            "/api/materials", params={"search": self.async_material_code}
        )
        self.assertEqual(imported.status_code, 200)
        self.assertEqual(len(imported.json()), 1)
        audit = self.client.get("/api/audit").json()
        self.assertTrue(any(
            item["action"] == "IMPORT_AI_CANDIDATES_GENERATED"
            and item["entity_id"] == batch_id
            for item in audit
        ))

if __name__ == "__main__":
    unittest.main()
