# Graph Report - numm  (2026-09-11)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 1016 nodes · 3329 edges · 68 communities (27 shown, 8 thin omitted)
- Extraction: 89% EXTRACTED · 11% INFERRED · 0% AMBIGUOUS · INFERRED: 353 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `b79f379e`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- write_audit
- FastAPI
- family_extractors.py
- import_service.py
- User
- backend/app/routers/matching.py
- package.json
- integrations.py
- App.jsx
- rbac.py
- database.py
- TestNUMMEndToEndIntegration
- backend/app/routers/materials.py
- Material
- test_identity_safety.py
- national_code_service.py
- Materials.jsx
- lucide-react
- api.js
- mappings.py
- MaterialMapping
- approve_match
- ImportMaterials.jsx
- routers/inventory.py
- Inventory.jsx
- NationalMaterials.jsx
- NationalMaterial360.jsx
- make_dataset.py
- _UnionFind
- DashboardStats
- ImportResponse
- MatchingResult
- normalization_service.py
- SAPMaterial
- test_setup.py

## God Nodes (most connected - your core abstractions)
1. `User` - 117 edges
2. `Material` - 79 edges
3. `write_audit()` - 67 edges
4. `MaterialMapping` - 56 edges
5. `CPSE` - 48 edges
6. `Inventory` - 43 edges
7. `NationalMaterial` - 41 edges
8. `ensure_cpse_access()` - 36 edges
9. `lucide-react` - 35 edges
10. `MaterialMatch` - 34 edges

## Surprising Connections (you probably didn't know these)
- `_load_pipeline()` --indirect_call--> `build_faiss_index()`  [INFERRED]
  ai-service/src/teammate_bridge.py → teammate-ai/src/embed_and_retrieve.py
- `_load_pipeline()` --indirect_call--> `embed_texts()`  [INFERRED]
  ai-service/src/teammate_bridge.py → teammate-ai/src/embed_and_retrieve.py
- `_load_pipeline()` --indirect_call--> `find_top_k_matches()`  [INFERRED]
  ai-service/src/teammate_bridge.py → teammate-ai/src/embed_and_retrieve.py
- `_load_pipeline()` --calls--> `get_model()`  [INFERRED]
  ai-service/src/teammate_bridge.py → teammate-ai/src/embed_and_retrieve.py
- `_load_pipeline()` --indirect_call--> `match_materials()`  [INFERRED]
  ai-service/src/teammate_bridge.py → teammate-ai/src/scorer.py

## Import Cycles
- None detected.

## Communities (68 total, 8 thin omitted)

### Community 0 - "write_audit"
Cohesion: 0.05
Nodes (68): get_db(), health(), get, root(), error_middleware(), logging_middleware(), AuditLog, Base (+60 more)

### Community 1 - "FastAPI"
Cohesion: 0.06
Nodes (55): _category(), _decorate(), _description(), engine_health(), _fallback_tokens(), log_engine_startup(), Return a bounded set of plausible, unique material pairs. Blocking by…, run_batch() (+47 more)

### Community 2 - "family_extractors.py"
Cohesion: 0.05
Nodes (61): ndarray, build_faiss_index(), embed_texts(), find_top_k_matches(), get_model(), _index_fingerprint(), src/embed_and_retrieve.py --------------------------- Wraps sentence-…, Given one normalized query description and a list of normalized candidate… (+53 more)

### Community 3 - "import_service.py"
Cohesion: 0.08
Nodes (45): Settings, ImportBatch, Base, ImportRowError, Base, cancel(), confirm(), dead_letters() (+37 more)

### Community 4 - "User"
Cohesion: 0.09
Nodes (57): MaterialRequest, Base, Base, RequestItem, Base, StockAllocation, Base, User (+49 more)

### Community 5 - "backend/app/routers/matching.py"
Cohesion: 0.07
Nodes (54): approve(), list_approvals(), list_approvals_paginated(), get, post, put, Session, reject() (+46 more)

### Community 6 - "package.json"
Cohesion: 0.05
Nodes (40): dependencies, axios, lucide-react, react, react-dom, react-router-dom, tailwindcss, @tailwindcss/vite (+32 more)

### Community 7 - "integrations.py"
Cohesion: 0.10
Nodes (19): ABC, connector_health(), history(), push_mappings(), get, post, Session, reconcile() (+11 more)

### Community 8 - "App.jsx"
Cohesion: 0.17
Nodes (23): App(), PermissionRoute(), ProtectedRoute(), PublicRoute(), Layout(), Navbar(), Sidebar(), AuthContext (+15 more)

### Community 9 - "rbac.py"
Cohesion: 0.13
Nodes (30): login(), login_json(), me(), normalize_role(), get, post, Session, register() (+22 more)

### Community 10 - "database.py"
Cohesion: 0.18
Nodes (15): seed_database(), ApprovalAction, Base, DemandRecord, Base, ImportDeadLetter, Base, IntegrationSync (+7 more)

### Community 11 - "TestNUMMEndToEndIntegration"
Cohesion: 0.06
Nodes (13): Test file preview, validation, confirmation, and DB insertion using real CSV…, Test backend calling AI Service for clustering and duplicate candidate detection, Test human approval action, national material creation, and legacy code mapping, Test National Material listing, creation, and detail with mappings, Test inventory record creation and querying, Verify health checks of Backend, AI service, and Mock SAP, Test creating draft request, adding item, submitting, and checking status, Test Backend pulling catalog materials from Mock SAP service (+5 more)

### Community 12 - "backend/app/routers/materials.py"
Cohesion: 0.20
Nodes (22): delete(), delete, put, update(), snapshot_model(), _attribute_text(), ClassificationResult, classify_material() (+14 more)

### Community 13 - "Material"
Cohesion: 0.21
Nodes (17): CPSE, Base, MaterialMatch, Base, Material, Base, analytics(), get (+9 more)

### Community 14 - "test_identity_safety.py"
Cohesion: 0.18
Nodes (21): ProcurementRecord, Base, analytics(), import_history(), opportunities(), prepare_lines(), preview_reuse(), PurchaseLine (+13 more)

### Community 15 - "national_code_service.py"
Cohesion: 0.17
Nodes (16): Base, TaxonomyCode, canonical_specs(), CanonicalConflict, _meaningful(), _normalized_engineering_value(), propose_canonical(), _source_record() (+8 more)

### Community 16 - "Materials.jsx"
Cohesion: 0.20
Nodes (12): EmptyState(), Modal(), MatchCard(), MatchScore(), MaterialCard(), MaterialFilters(), MaterialTable(), Approvals() (+4 more)

### Community 17 - "lucide-react"
Cohesion: 0.16
Nodes (16): Loading(), RecentActivity(), SECTOR_ICONS, SectorCard(), StatCard(), Dashboard(), DuplicateClusters(), ModelEvaluation() (+8 more)

### Community 18 - "api.js"
Cohesion: 0.14
Nodes (13): CPSEManagement(), needsCpse(), ROLES, DataQuality(), Integrations(), api, API_BASE_URL, cpseApi (+5 more)

### Community 19 - "mappings.py"
Cohesion: 0.14
Nodes (16): field_validator, health(), get, root(), _evict_idempotency_entries(), list_mappings(), MappingPayload, MappingRecord (+8 more)

### Community 20 - "MaterialMapping"
Cohesion: 0.29
Nodes (10): MaterialMapping, Base, NationalMaterial, Base, add_mapping(), remove_mapping(), Conservative engineering identity checks shared by every mapping entry point., validate_members() (+2 more)

### Community 21 - "approve_match"
Cohesion: 0.20
Nodes (3): approve_match(), IdentitySafetyTests, RemediationFlowTests

### Community 22 - "ImportMaterials.jsx"
Cohesion: 0.19
Nodes (6): FileUploader(), ImportPreview(), ImportStatus(), ImportMaterials(), TERMINAL, importApi

### Community 23 - "routers/inventory.py"
Cohesion: 0.26
Nodes (11): create(), list_all(), get, post, put, Session, update(), InventoryCreate (+3 more)

### Community 24 - "Inventory.jsx"
Cohesion: 0.23
Nodes (9): blankForm(), Inventory(), number(), inventoryApi, firstDefined(), materialApi, normalizeMaterial(), specsText() (+1 more)

### Community 25 - "NationalMaterials.jsx"
Cohesion: 0.40
Nodes (4): Button(), ComparisonPanel(), MappingHistory(), MaterialComparison()

### Community 27 - "make_dataset.py"
Cohesion: 0.36
Nodes (7): build_ground_truth(), build_material_rows(), main(), data/make_dataset.py --------------------- Generates a synthetic CPSE material…, Assign each variant to a CPSE and produce material master rows., For every pair of rows, label: 1 = same material (same family_id) 2 =…, write_csv()

## Knowledge Gaps
- **34 isolated node(s):** `Settings`, `SECTOR_ICONS`, `ROLES`, `API_BASE_URL`, `TERMINAL` (+29 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 227 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **8 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `User` connect `User` to `write_audit`, `import_service.py`, `backend/app/routers/matching.py`, `integrations.py`, `rbac.py`, `database.py`, `backend/app/routers/materials.py`, `Material`, `MaterialMapping`, `approve_match`, `routers/inventory.py`?**
  _High betweenness centrality (0.097) - this node is a cross-community bridge._
- **Why does `write_audit()` connect `write_audit` to `import_service.py`, `User`, `backend/app/routers/matching.py`, `integrations.py`, `rbac.py`, `backend/app/routers/materials.py`, `Material`, `test_identity_safety.py`, `national_code_service.py`, `MaterialMapping`, `approve_match`, `routers/inventory.py`?**
  _High betweenness centrality (0.031) - this node is a cross-community bridge._
- **Why does `Material` connect `Material` to `write_audit`, `import_service.py`, `User`, `backend/app/routers/matching.py`, `integrations.py`, `database.py`, `backend/app/routers/materials.py`, `test_identity_safety.py`, `MaterialMapping`, `approve_match`, `routers/inventory.py`?**
  _High betweenness centrality (0.025) - this node is a cross-community bridge._
- **Are the 91 inferred relationships involving `User` (e.g. with `approve()` and `list_approvals()`) actually correct?**
  _`User` has 91 INFERRED edges - model-reasoned connections that need verification._
- **Are the 39 inferred relationships involving `Material` (e.g. with `list_approvals_paginated()` and `stats()`) actually correct?**
  _`Material` has 39 INFERRED edges - model-reasoned connections that need verification._
- **Are the 28 inferred relationships involving `MaterialMapping` (e.g. with `stats()` and `migrate()`) actually correct?**
  _`MaterialMapping` has 28 INFERRED edges - model-reasoned connections that need verification._
- **Are the 21 inferred relationships involving `CPSE` (e.g. with `list_approvals_paginated()` and `register()`) actually correct?**
  _`CPSE` has 21 INFERRED edges - model-reasoned connections that need verification._