# NUMM MVP implementation and verification report — 11 September 2026

This is an evidence-based report for a hackathon MVP/V1. It is not a production-readiness or industrial-accuracy claim.

## Outcome

The existing React → FastAPI → PostgreSQL/AI/SAP-connector architecture was preserved. The project now demonstrates the full governed path from CPSE source data through real teammate-AI recommendations, human approval, National Material identity and legacy mapping, inventory reuse, request fulfillment, procurement intelligence, SAP boundary testing, and tamper-evident audit lineage.

No PostgreSQL volume was deleted and no existing business records were cleared. After the final backend/frontend restart and successful E2E run, the database contained 501 materials, 75 National Materials, 222 mappings, 4 inventory records, 6 requests, and 607 audit events. E2E runs add uniquely identified test evidence rather than overwriting existing records.

## Requirement coverage

| Major area | Status | Implemented and verified scope |
|---|---|---|
| Real teammate AI | PASS | `engine_adapter` calls `teammate_bridge`, which loads the teammate modules. Runtime health reported `TEAMMATE_REAL`; fallback was not active. |
| SentenceTransformer | PASS | Pinned `all-MiniLM-L6-v2` revision loads once from the Docker image; runtime embedding dimension is 384. |
| FAISS candidate retrieval | PASS | L2-normalized embeddings and real FAISS retrieval are exercised. Focused imports query only imported records against the full catalogue instead of rescoring all pairs. |
| Hybrid scoring and explainability | PASS | 25% semantic, 55% structured attribute, 20% fuzzy components plus engineering guardrails and persisted explanations. |
| Exact / near / functional / no-match separation | PASS | Stable enums, score validation, canonical pair ordering, reversed-pair protection, type/dimension/grade guards. Functional equivalents remain separate substitution advice. |
| Industrial attribute extraction | PARTIAL | Modular support exists for fasteners, valves, motors, bearings, pumps, pipes and flanges. This is deliberately bounded representative-family coverage, not all industrial materials. |
| Standard descriptions | PASS (supported families) | Original evidence is preserved; cleaned, normalized, recommended and approved standard descriptions are separate. Templates do not invent missing attributes. |
| Intelligent classification | PARTIAL | Deterministic taxonomy plus extracted-attribute validation, confidence/evidence and manual preservation are implemented. A learned taxonomy-embedding classifier calibrated on real CPSE data is not. |
| Duplicate/equivalence clusters | PASS | Cluster API and UI show safe identity components, exact/near counts, conflicts, canonical recommendation and functional-equivalent edges separately. No automatic cluster merge. |
| National code generation | PASS | Governed deterministic code/check-digit generation, collision safety and canonical identity reuse are persisted. Runtime default keeps human final approval. |
| Legacy code mapping | PASS | Existing CPSE codes map to the National Material while retaining source identity and traceability. |
| Migration lifecycle | PARTIAL | Bulk preview/apply, expected-current checks, mapping history and guarded restore exist. Full graph-wide merge/split, retirement/supersession and real ERP cutover orchestration remain outside the MVP. |
| National Material 360 and lineage | PASS | Database-backed identity, mappings, stock, demand, procurement, suppliers, AI history, approvals, audit, SAP status, lineage and opportunity data are aggregated and displayed. |
| Inventory and stock import | PASS | Direct stock entry plus material/inventory import on one page, preview, validation, explicit conflict policy, idempotency, locking and reservation safeguards. “Not stocked” truthfully means no inventory row exists. |
| Demand aggregation | PASS | Period- and UOM-aware persisted demand with ownership validation and national aggregation. |
| Reuse before buy | PASS | Own stock, other-CPSE stock, remaining fresh need, other demand, suppliers and human decision options are returned without executing a transfer or purchase. |
| Material requests | PASS | Draft, item, preview, submit/reserve, separate approval/rejection, release and fulfillment are persisted with transition checks and row locking. |
| Procurement history | PASS (CSV MVP) | Validated/idempotent CSV purchase-line import and identity/month/UOM/currency-aware analytics. XLSX and live ERP purchase-history feeds are not implemented. |
| Procurement opportunities | PASS | Uses actual National Materials, stock, demand and purchase records; exposes a transparent 100-point score and recommendations. Monetary savings are omitted unless price evidence exists. |
| Data quality | PASS (schema scope) | Completeness/readiness metrics and technical issues use persisted source data and the supported category schemas. |
| Harmonization Index | PASS | Equal-weight, disclosed calculation from mapping coverage, duplicate rationalization, technical completeness, classification completeness, approval completion and data quality. |
| Model evaluation dashboard | PASS | API/UI publish dataset hashes, partitions, confusion matrix, per-class precision/recall/F1 and merge FPR/FNR. The scope statement explicitly limits the result to 147 controlled pairs. |
| Maker-checker governance | PASS | Recommendation submitters cannot approve/reject their own match; request creators cannot approve/reject their own request; rejection requires a reason. |
| Tamper-evident governance ledger | PASS (database boundary) | New events form a PostgreSQL-serialized SHA-256 chain with payload checksums and verification API/UI. The 533 pre-existing events are explicitly reported as legacy-unhashed; they were not rewritten. External WORM retention is not included. |
| Authentication and RBAC | PASS | Backend-issued JWT, `/login`, `/me`, backend-owned permissions, CPSE scoping and forbidden-action tests. No frontend auth fallback. |
| SAP/ERP integration | PARTIAL | Mock SAP is a legitimate integration test boundary; generic OData configuration, origin-safe continuation, sync/update, history, test/reconcile/error visibility and safe failure audit exist. Real CPSE SAP contracts and credentials require external onboarding. |
| Executive dashboard | PASS | All cards use API/database values, including the disclosed harmonization components, inventory/demand/opportunities, sync status and governance activity. |
| Frontend/API integration | PASS | Required pages/routes are connected and failures render as failures. Page-level code splitting reduced the initial production JS chunk from 502.90 kB to 314.30 kB. |
| Docker runtime | PASS | Frontend, backend, import worker, AI, mock SAP, PostgreSQL and Redis run together. |
| Database persistence | PASS | Counts remained after container rebuild/restart; migrations are at `20260911_07 (head)`. |
| End-to-end API workflow | PASS | 17 scenarios pass, including import, real AI comparison/persistence, separate review, National mapping, 360, reuse preview, stock reservation, approval, fulfillment, SAP success/failure, audit, RBAC and asynchronous focused matching. Browser automation is not included. |

## AI evidence

- Active engine: `TEAMMATE_REAL`
- Loaded model: `all-MiniLM-L6-v2`
- Model revision: `c9745ed1d9f207416be6d2e6f8de32d1f16199bf`
- Embedding dimension: 384
- Runtime FAISS state: true; 498 catalogue vectors indexed during the final live check
- Fallback during successful checks: not used; `fallback_reason` was `null`
- Evaluation: 147/147 correct on 139 labelled synthetic pairs plus 8 held-out challenge pairs; per-class precision/recall/F1 1.0 and identity merge FPR/FNR 0.0 on this controlled dataset only
- Evaluation families/scenarios include fasteners plus held-out bearing, electrical, pipe, pump and valve conflicts, OCR spelling, multilingual text, units, missing evidence and unseen-CPSE labels
- Live controlled cases also produced the expected decisions for exact bolt wording, bolt-vs-nut, M16-vs-M20, SS304-vs-mild-steel, equivalent DN50 valve wording and DN50-vs-DN100

The evaluation result must not be quoted as industrial or real-CPSE accuracy. A larger independently labelled CPSE benchmark is still required.

## Automated verification executed

| Check | Result |
|---|---|
| AI unit/integration tests | 10 passed, 0 failed |
| Backend focused service/workflow tests | 38 passed, 0 failed |
| Live end-to-end API scenarios | 17 passed, 0 failed |
| Total automated test cases in final run set | 65 passed, 0 failed |
| Frontend ESLint | PASS |
| Frontend production build | PASS; no chunk-size warning after route splitting |
| `git diff --check` | PASS |
| Backend health | HTTP 200, `status=ok` |
| AI health | HTTP 200, real model loaded and FAISS true |
| Mock SAP health | HTTP 200 during E2E |
| Frontend health | HTTP 200 after rebuild |
| Audit verification | `VALID`; 74 hashed records checked after the final E2E run, 0 errors |
| Persistence after restart | PASS; records and mappings retained |
| CodeRabbit external review | NOT EXECUTED: CLI 0.7.6 is installed but `coderabbit auth status` reports signed out |

Some backend test classes intentionally inherit shared safety scenarios, so the 38 count is executed test cases, not 38 unique functions. The 147 evaluation pairs are evaluation observations and are not added to the 65 automated-test count.

## Migrations created

1. `backend/alembic/versions/20260908_00_initial_schema.py`
2. `backend/alembic/versions/20260908_01_close_remediation_gaps.py`
3. `backend/alembic/versions/20260909_02_complete_remaining_risks.py`
4. `backend/alembic/versions/20260909_03_inventory_import.py`
5. `backend/alembic/versions/20260910_04_procurement_history.py`
6. `backend/alembic/versions/20260910_05_tamper_evident_audit.py`
7. `backend/alembic/versions/20260911_06_standard_descriptions.py`
8. `backend/alembic/versions/20260911_07_match_maker_checker.py`

The migrations are additive/forward-safe for this MVP. Historic audit events were not fabricated or backfilled with invented hashes.

## Direct implementation file manifest

The repository already contained a large dirty working tree. To avoid falsely attributing unrelated user work, this manifest lists the files directly introduced or materially changed for the completed capability set.

### Backend

- Modified: `backend/app/config/settings.py`, `backend/app/main.py`, `backend/app/models/__init__.py`, `backend/app/models/audit_log.py`, `backend/app/models/material.py`, `backend/app/models/material_match.py`, `backend/app/routers/approvals.py`, `backend/app/routers/audit.py`, `backend/app/routers/dashboard.py`, `backend/app/routers/imports.py`, `backend/app/routers/matching.py`, `backend/app/routers/materials.py`, `backend/app/routers/national_materials.py`, `backend/app/schemas/material.py`, `backend/app/services/ai_service.py`, `backend/app/services/approval_service.py`, `backend/app/services/audit_service.py`, `backend/app/services/data_quality_service.py`, `backend/app/services/import_service.py`, `backend/app/services/national_code_service.py`, `backend/tests/test_e2e_integration.py`, `backend/tests/test_identity_safety.py`
- Added: `backend/app/models/procurement_record.py`, `backend/app/routers/procurement.py`, `backend/app/services/duplicate_cluster_service.py`, `backend/app/services/material_schema_service.py`, `backend/app/services/national_material_360_service.py`, `backend/app/services/procurement_intelligence_service.py`, and the eight Alembic revisions listed above

### AI and teammate modules

- Modified: `ai-service/Dockerfile`, `ai-service/app/engine_adapter.py`, `ai-service/app/main.py`, `ai-service/app/routers/health.py`, `ai-service/app/routers/matching.py`, `ai-service/app/schemas.py`, `ai-service/src/structured_identity.py`, `ai-service/src/teammate_bridge.py`, `ai-service/tests/test_teammate_bridge.py`, `teammate-ai/src/extract_attributes.py`, `teammate-ai/src/scorer.py`, `teammate-ai/tests/eval_against_ground_truth.py`
- Added: `ai-service/app/routers/evaluation.py`, `teammate-ai/src/family_extractors.py`, `teammate-ai/tests/test_industrial_attributes.py`

### Frontend and documentation

- Modified: `frontend/src/App.jsx`, `frontend/src/components/layout/Sidebar.jsx`, `frontend/src/pages/AuditTrail.jsx`, `frontend/src/pages/Dashboard.jsx`, `frontend/src/pages/ImportMaterials.jsx`, `frontend/src/pages/NationalMaterials.jsx`, `frontend/src/services/matchingApi.js`, `frontend/src/services/nationalMaterialApi.js`
- Added: `frontend/src/pages/DuplicateClusters.jsx`, `frontend/src/pages/ModelEvaluation.jsx`, `frontend/src/pages/NationalMaterial360.jsx`, `frontend/src/pages/ProcurementHistory.jsx`, `frontend/src/pages/ProcurementOpportunities.jsx`, `docs/IMPLEMENTATION_STATUS_2026-09-11.md`

Supporting models, services, routers, UI pages, tests, Docker files, datasets and documentation already present in the dirty tree were preserved rather than reset or deleted.

## Dependencies actually used

- AI: `sentence-transformers`, CPU `torch`, `faiss-cpu`, `RapidFuzz`, `numpy`, FastAPI/Uvicorn
- Backend: FastAPI, SQLAlchemy, PostgreSQL driver, Alembic, Pydantic, Celery/Redis, HTTPX, Pandas/OpenPyXL, JWT/passlib/bcrypt
- Frontend: React 19, React Router, Axios, Lucide, Tailwind/Vite

All runtime packages are represented in `backend/requirements.lock`, `ai-service/requirements.lock`, and `frontend/package-lock.json`. The model revision is pinned and baked into the AI image.

## Bugs and risks fixed

- National codes were not assigned because failed/pending AI results and an empty National registry were being conflated; mapping now occurs only after a valid human approval and canonical identity creation/reuse.
- Functional equivalents could be treated like identities; they now remain conditional substitution recommendations and cannot auto-merge.
- Match submitters could approve their own recommendation; maker-checker is enforced in the service layer.
- The per-card blue Add Stock control did not populate the actual form; it now selects the card’s CPSE/material and moves focus to stock entry.
- Material import and inventory import were disconnected; the same Import page now selects material vs stock workflow with truthful validation/status.
- Batch matching risked catalogue-wide pair scoring; focused imports now query imported records through FAISS against the full catalogue.
- Reversed duplicate candidate pairs and malformed AI output are rejected/canonicalized.
- Critical size/type/grade evidence could be overwhelmed by text similarity; family guardrails now override generic similarity.
- Empty Data Quality results omitted response fields expected by the UI.
- Audit rows had no tamper detection; new writes are chained and verifiable without rewriting history.
- National-code approval auditing could claim creation when a canonical identity was reused; event types now reflect the actual action.
- E2E fixtures reused fixed codes/keys and violated maker-checker; fixtures are unique and use separate submitter/reviewer identities.
- The frontend loaded every page in one 503 kB initial chunk; route-level lazy loading reduced it to 314 kB.

## Preserved behavior

- Existing source descriptions/codes and reviewed decisions are retained.
- Existing National Material codes and mappings are not regenerated.
- Mock SAP remains the intended ERP integration-test service.
- The fallback matcher remains available only as clearly reported resilience behavior.
- Existing ports, services, routes and visual language remain intact.
- No `docker compose down -v`, destructive reset, seed reset or bulk record deletion was used.

## Remaining limitations

1. Industrial family and critical-attribute schemas are representative and require domain-engineer validation per CPSE/sector.
2. Classification is not a learned, taxonomy-embedding model and has not been calibrated on real CPSE labels.
3. FAISS retrieval is real but the index is rebuilt for a batch/service lifecycle; a persistent incremental national-scale vector index and load benchmark remain future work.
4. Full identity merge/split, national-record version/supersession governance, ERP cutover and rollback are broader than current mapping migration/restore.
5. The SHA-256 database chain detects modification in the configured boundary, but privileged database administrators could rewrite both records and hashes; production governance needs external signed/WORM retention.
6. Generic OData and mock SAP do not prove compatibility with each CPSE’s actual SAP version, schema, authentication, deletion semantics or controls.
7. Historical procurement import is CSV-only; currency conversion, forecasting, supplier selection and procurement execution are intentionally absent.
8. Inventory is current-balance oriented; a full stock-movement accounting ledger and transfer/shipping workflow are not included.
9. Evaluation data are small and controlled. Independent, held-out, real multi-sector CPSE labels and safety review are required.
10. The E2E suite is API-level, not browser automation. Accessibility, concurrency/load, disaster recovery and penetration testing remain outside this hackathon validation.
11. External CodeRabbit review remains blocked until a user completes `coderabbit auth login`.

## Start commands

From the repository root:

```powershell
docker compose config
docker compose up -d --build
docker compose ps
```

Open `http://localhost:5173`. API documentation is at `http://localhost:8000/docs`; AI health is at `http://localhost:8001/health`; mock SAP is at `http://localhost:8002/health`.

Useful verification commands:

```powershell
docker compose exec -T ai-service python -m unittest discover -s tests -v
docker compose exec -T backend python -m unittest tests.test_remediation_services tests.test_remediation_flow tests.test_identity_safety tests.test_inventory_import tests.test_operational_controls -v
cd backend
..\.venv\Scripts\python.exe -m unittest tests.test_e2e_integration -v
cd ..\frontend
npm run lint
npm run build
```

## Demo accounts

- System administrator: `officer@numm.gov.in` / `officer123`
- CPSE data manager: `r.kumar@numm.gov.in` / `admin123`
- Procurement reviewer: `a.sen@numm.gov.in` / `officer123`

These are local demo credentials only. Change/remove them before any shared or externally reachable deployment.

## Recommended demonstration flow

1. Log in and show AI health/model evaluation with the controlled-data disclaimer.
2. Import three differently worded M16×50 SS304 bolt records from distinct CPSE datasets; show validation and focused AI progress.
3. Open explainable recommendations and the duplicate cluster; contrast an exact/near duplicate with grade and dimension conflicts.
4. Submit as the data manager and approve as the separate reviewer; show one governed National Material Code with all legacy codes retained.
5. Open National Material 360 and show mappings, lineage, audit, inventory, demand, procurement and SAP status.
6. Add/import stock, create demand, and show reuse-before-buy before submitting the material request.
7. Approve and fulfill the request with the reviewer account; show reservation/allocation and retained audit evidence.
8. Open Procurement Opportunities and the executive dashboard to show aggregate need, surplus reuse and remaining consolidated demand without claiming unproven monetary savings.
9. Run mock SAP synchronization/reconciliation and finish on the valid tamper-evident ledger.

The defensible value proposition is: one governed National Material identity, cross-CPSE inventory intelligence, collaborative procurement decision support, human-governed AI, and full traceability within the MVP boundary.
