# NUMM Project Workflow

## Prerequisites

Recommended: Docker Desktop with Compose v2 and Git. For local component development, install Python 3.12+, Node.js 20+, PostgreSQL 16+, and Redis 7+.

## Quick start with Docker

1. Create local configuration.

   ```powershell
   Copy-Item .env.example .env
   ```

2. Generate a signing key and place it after `SECRET_KEY=` in `.env`.

   ```powershell
   python -c "import secrets; print(secrets.token_urlsafe(48))"
   ```

3. Start the platform and migrate the database.

   ```powershell
   docker compose up --build -d
   docker compose exec backend alembic upgrade head
   ```

4. Open the services.

   - Frontend: `http://localhost:5173`
   - Backend health: `http://localhost:8000/health`
   - API docs: `http://localhost:8000/docs`
   - AI health: `http://localhost:8001/health`
   - Mock SAP health: `http://localhost:8002/health`

5. Follow logs when troubleshooting.

   ```powershell
   docker compose logs -f backend import-worker ai-service frontend
   ```

Persistent Docker volumes are retained. To stop without deleting data, use `docker compose down` — never add `-v` unless you explicitly intend to remove local data.

## Local development setup

Start PostgreSQL and Redis first, then use separate terminals.

### Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
# Configure DATABASE_URL, REDIS_URL, SECRET_KEY, and service URLs in backend/.env.
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

### AI service

```powershell
cd ai-service
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```

The production configuration requires the configured matching engine and does not silently present a fallback matcher as the engineering model.

### Mock SAP

```powershell
cd mock-sap
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8002
```

### Frontend

```powershell
cd frontend
npm install
Copy-Item .env.example .env
npm run dev
```

Set `VITE_API_URL=http://localhost:8000` in `frontend/.env` for local use.



## 1. What this project is

NUMM (National Unified Material Master) is a procurement and material-governance platform for CPSEs. It takes material records from different organizations, cleans and compares them, lets an authorized officer review AI recommendations, and maps approved records to one national material identity.

The central business flow is:

```text
CPSE source data
    -> validate and clean
    -> find possible duplicates with AI
    -> persist proposed identity clusters
    -> reviewer corrects cluster membership and risk exceptions
    -> approver authorizes the reviewed cluster
    -> create or link a National Material Code
    -> use the unified identity for stock, demand, procurement, and reporting
```

AI proposes pair relationships as evidence; it never creates an identity mapping automatically. Persisted clusters, rather than individual pairs, are the governance unit. A human reviewer remains responsible for engineering exceptions and an authorized approver authorizes the resulting national identity.

## 2. The system in one picture

```text
Browser (React/Vite, port 5173)
              |
              v
Main API (FastAPI, port 8000)
       |          |          |
       v          v          v
 PostgreSQL    AI service   SAP connector
               (8001)      Mock SAP (8002 locally)
       ^
       |
 Redis + Celery import worker (Docker/queue mode)
```

### What each part does

- **Frontend**: authenticated React pages, navigation, forms, tables, dashboards, review dialogs, and API calls.
- **Main backend**: authentication, role-based permissions, CPSEs, materials, imports, matching orchestration, approvals, national mappings, inventory, requests, procurement analytics, integrations, exports, and audit records.
- **PostgreSQL**: persistent business data. SQLAlchemy models and Alembic migrations define and evolve the schema.
- **AI service**: normalizes descriptions, extracts attributes, retrieves candidates, calculates semantic/fuzzy/attribute scores, and returns an explanation plus model version.
- **Redis/Celery**: durable asynchronous import processing in Docker Compose. Local development can use in-process background jobs.
- **Mock SAP**: local ERP connector for demos and integration testing. A configured SAP OData connector can be used in a real environment.

## 3. Local setup for a new developer

### Option A: Docker Compose

1. Copy the root environment template if needed:

   ```powershell
   Copy-Item .env.example .env
   ```

2. Set a real `SECRET_KEY` in `.env`. The backend refuses to start with a placeholder secret.

3. Start the complete stack:

   ```powershell
   docker compose up --build
   ```

4. Open:

   - Frontend: `http://localhost:5173`
   - Backend health: `http://localhost:8000/health`
   - API documentation: `http://localhost:8000/docs`

Docker starts PostgreSQL, Redis, the API, the import worker, AI service, mock SAP, and frontend. It also runs the backend in Celery queue mode.

### Option B: Run services manually

Start PostgreSQL first, then prepare the backend:

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

In another terminal:

```powershell
cd frontend
npm install
npm run dev
```

Run the AI service and mock SAP when using matching or ERP-sync features. Their default ports are `8001` and `8002`. The frontend reads its API URL from `VITE_API_URL`; local development normally points it to `http://localhost:8000`.

### First login and access

Registration requires a CPSE assignment, but a newly registered account is intentionally created with the `PENDING_USER` role and no working permissions. A system administrator must verify the account, assign a role, and assign a CPSE where appropriate before the user can use protected pages.

The main roles are:

- **System Administrator**: unrestricted administration.
- **CPSE Data Manager**: manages a CPSE's material and inventory data and imports.
- **Requesting Officer**: creates and submits material requests.
- **Procurement Officer**: reviews AI mappings, approves requests, and fulfills approved requests.
- **Auditor**: read-only governance, data, and audit visibility.
- **CPSE Officer**: backward-compatible combined operational role.

## 4. Primary business workflow

This is the recommended end-to-end flow for understanding and demonstrating the product.

### Step 1: Sign in

The browser opens at `/login`. The frontend calls `/api/auth/login`, stores the bearer token and user profile in local storage, and restores the session with `/api/auth/me` on reload. Every protected API request sends the bearer token. Expired sessions are cleared and redirected to login.

### Step 2: Configure participating CPSEs

Open **CPSE Management** (`/cpses`) as an administrator or CPSE officer. Create or maintain the organization records used to scope materials, users, imports, inventory, and reporting.

The CPSE is important because non-admin users are restricted to their assigned CPSE. The backend checks this scope on write operations such as imports.

### Step 3: Import material or inventory data

Open **Import Data** (`/import`). Choose the CPSE and one of the import types:

- **Material Master**: source material codes, descriptions, units, categories, manufacturers, models, and specifications.
- **Inventory Stock**: warehouse stock, quantity, unit of measure, and related stock fields.

The import page follows this state flow:

```text
IDLE -> PREVIEW -> QUEUED/PIPELINE -> COMPLETED
                              \\-> COMPLETED_WITH_ERRORS / FAILED / CANCELLED
```

The user uploads CSV/XLSX data. The backend previews and validates it before any processing is confirmed. The user then confirms the batch. The job is queued, progress is polled, and the recent batch history shows its final status. Inventory imports support a policy for existing stock: reject the row or update the existing quantity.

Behind the page, the import service normalizes fields, validates required values, applies hard limits, processes bounded chunks, records row errors, supports retries and dead letters, and can send material candidates to the AI service. Imports are idempotent when an idempotency key is supplied.

### Step 4: Inspect the material master

Open **Materials Master** (`/materials`). Search and filter the normalized records by description, CPSE, category, and related fields. Use a material's detail view to inspect its source identity and technical attributes. This page is the baseline from which matching and national harmonization are understood.

### Step 5: Run AI matching

Open **AI Recommendations** (`/ai-recommendations`) and run the matching process. The main API sends material data to the AI service. The service returns candidate pairs with:

- semantic similarity;
- engineering attribute similarity;
- fuzzy text similarity;
- final score;
- classification (`EXACT`, `NEAR_DUPLICATE`, `FUNCTIONAL_EQUIVALENT`, or `NO_MATCH`);
- explanation, model name, and matcher version.

The backend stores recommendations as `MaterialMatch` records. They remain AI evidence/history and can be inspected on this page, in Material Comparison, and from a cluster review. Matching discovery creates only new persisted `PROPOSED` clusters; it never overwrites a reviewed cluster or its human membership edits. **Duplicate Clusters** (`/duplicate-clusters`) is the identity-review workspace. **Material Comparison** (`/comparison`) lets a user compare two selected records directly. **Model Evaluation** (`/model-evaluation`) is AI QA only and does not mutate operational approval state.

### Visual material search

Open **Visual Material Search** (`/visual-search`) to find candidate records from a material image. Upload or choose an image, then inspect visually similar indexed material images returned by the visual-search service. Use a result only as a discovery aid: open the source material, compare technical specifications, or submit an AI candidate for normal evidence review.

Visual similarity is separate from engineering identity matching. A visual result does not create a `MaterialMatch`, change a cluster, create a National Material Code, map inventory, or approve a substitute. Identity and substitution decisions must still follow the persisted cluster and approval workflow.

### Step 6: Review identity clusters

Open **Duplicate Clusters** (`/duplicate-clusters`) as a user with `approval.review`. The page uses persisted clusters and has `PROPOSED`, `UNDER REVIEW`, `READY FOR APPROVAL`, and `APPROVED` queues.

Start a review, then inspect three separate sections: active **Identity Members**, **Functional Alternatives**, and **Removed Members**. A reviewer can keep, remove, restore, or move a valid identity member to a functional alternative; removal preserves the Material Master record and membership history. The reviewer can also select the canonical source material and add review notes.

Risk is calculated by the backend as `LOW`, `MEDIUM`, or `HIGH` from relationship evidence, technical conflicts, family/UOM consistency, confidence, mapping state, and missing engineering evidence. `LOW` clusters can be automatically triaged to `READY_FOR_APPROVAL`; this is not auto-mapping. `HIGH` clusters require detailed engineering review before they can be submitted.

### Step 7: Approve national identity at cluster level

Open **Approvals** (`/approvals`). The Approval Center has four queues:

- **Identity Approvals**: reviewed `READY_FOR_APPROVAL` clusters.
- **Functional Substitutions**: separate substitute relationships that never merge identity or stock.
- **Mapping Conflicts**: clusters whose active identity members already map to different National Materials.
- **History**: resolved governance decisions.

Approving an identity cluster validates it again, then performs one controlled transaction: create a National Material when none exists, reuse a shared existing NMC when safe, or extend that NMC to previously unmapped active identity members. Functional alternatives and removed members are never mapped. Conflicting NMCs are blocked rather than silently reassigned. A repeated approval is idempotent.

Only low-risk clusters are eligible for **Approve Selected Low-Risk Clusters** batch approval. The backend revalidates every selection and reports individual successes, already-resolved items, conflicts, and failures without rolling back unrelated clusters.

### Step 8: Create and inspect national material identities

Approved mappings become visible in **National Materials** (`/national-materials`). This is the unified registry. A national record contains the national code, standard description, category/subcategory, unit, status, and links to legacy CPSE records.

Open a record to reach **National Material 360** (`/national-materials/:id`). This page is the complete lineage view. It brings together technical identity, stock by CPSE and warehouse, procurement opportunity recommendation, legacy CPSE mappings, open demand, supplier and purchase summary, SAP/ERP sync status, AI matching history, approval history, mapping lineage, and governance audit history.

This page answers: “Why does this national code exist, which source records created it, where is it stocked, and what decisions have been made about it?”

### Step 9: Use the unified data operationally

After harmonization, the platform can be used for operational planning:

1. **Inventory** (`/inventory`) shows stock and availability by CPSE/warehouse.
2. **Material Requests** (`/requests`) lets a requesting officer create a request, add national material items, preview the allocation, and submit it.
3. **Approvals** also handles request approval/rejection for users with request approval permission. The maker-checker rule prevents an officer from approving their own request.
4. **Inventory** or the request flow records fulfillment and reservation effects.
5. **Procurement History** (`/procurement-history`) imports or analyzes historical purchases and spend.
6. **Procurement Opportunities** (`/procurement-opportunities`) highlights reuse, surplus, and demand evidence that can reduce unnecessary buying.

The request allocation preview is designed to favor the highest available stock first, while retaining the source CPSE/warehouse information needed for fulfillment.

### Step 10: Synchronize with ERP and close the audit loop

Open **Integrations** (`/integrations`) to inspect or manage connector settings and health. The integration boundary supports the local Mock SAP connector and a configured SAP OData connector with authentication, TLS options, throttling, delta pagination, reconciliation, and idempotent push-back.

Open **Audit Trail** (`/audit-trail`) to inspect recorded actions and verify the audit chain. Exports are available through the relevant registry/reporting flows and are permission controlled.

## 5. Frontend pages explained

| Page | Route | Purpose | Typical user action |
| --- | --- | --- | --- |
| Login | `/login` | Starts an authenticated session. | Enter credentials and sign in. |
| Dashboard | `/dashboard` | National overview of CPSEs, materials, duplicates, AI matches, codes, coverage, network convergence, activity, and operational metrics. | Identify where attention is needed and jump to AI analysis or reports. |
| Materials Master | `/materials` | Searchable source material registry. | Inspect, create, edit, filter, or open material details. |
| Import Data | `/import` | Validated CSV/XLSX ingestion for material and inventory data. | Select CPSE, preview, confirm, monitor, cancel, inspect errors, or retry AI. |
| AI Recommendations | `/ai-recommendations` | AI candidate matching queue and confidence view. | Run matching, filter candidates, inspect evidence, and submit a candidate for review. |
| Duplicate Clusters | `/duplicate-clusters` | Persisted identity-cluster review workspace. | Start review; correct identity, functional, and removed memberships; select canonical material; submit for approval. |
| Model Evaluation | `/model-evaluation` | AI/matcher quality and evaluation results. | Inspect the current model evaluation response. |
| Material Comparison | `/comparison` | Direct two-record comparison. | Select two materials and inspect the pair verdict. |
| National Materials | `/national-materials` | Canonical national registry. | Search national codes and open a 360-degree record. |
| National Material 360 | `/national-materials/:id` | Full national identity, stock, demand, procurement, lineage, sync, and audit view. | Trace a code from source records to current operations. |
| Approvals | `/approvals` | Cluster-level authorization center. | Approve reviewed identities, batch-approve safe low-risk clusters, review functional substitutions, or resolve mapping conflicts. |
| Inventory | `/inventory` | Stock and warehouse operations. | Inspect availability, reservations, and inventory records. |
| Procurement History | `/procurement-history` | Historical purchase and spend analysis. | Import or inspect purchase history. |
| Procurement Opportunities | `/procurement-opportunities` | Reuse, surplus, demand, and savings opportunities. | Review evidence-backed opportunities before purchasing. |
| Material Requests | `/requests` | Cross-CPSE demand and allocation workflow. | Create request, add items, preview allocation, submit, approve, and fulfill. |
| CPSE Management | `/cpses` | Organization master and CPSE assignments. | Maintain participating CPSE records. |
| Data Quality | `/data-quality` | Data-quality indicators and reclassification controls. | Inspect issues and run permitted quality remediation. |
| Integrations | `/integrations` | Connector status and integration controls. | Check health or manage SAP/mock connector settings. |
| Audit Trail | `/audit-trail` | Governance and tamper-evident activity history. | Investigate who changed or approved what, and verify audit integrity. |

The sidebar only displays pages allowed by the signed-in user's permissions. Direct URLs are also protected by frontend route guards, and the API repeats authorization checks server-side.

## 6. Feature catalog: what is used and how

### Authentication and security

- FastAPI auth endpoints issue JWT bearer tokens.
- Passwords are hashed and verified by the backend.
- The React `AuthContext` restores sessions and handles expiry.
- Route-level and API-level RBAC protect pages and operations.
- CPSE-scoped users cannot manage another CPSE's records.
- Secrets are read from environment variables or secret files; placeholder secrets are rejected.

### Data import pipeline

- CSV and XLSX parsing supports material and inventory sources.
- Preview happens before confirmation so validation failures are visible early.
- Cleaning and canonicalization normalize descriptions and structured attributes.
- Chunking, progress, cancellation, retry, dead-letter records, and idempotency make large imports safer.
- Docker uses Redis/Celery; local mode can use FastAPI background tasks.

### AI matching

- Candidate retrieval narrows the search space.
- Hybrid scoring combines semantic, attribute, and fuzzy signals.
- Engineering rules and extracted attributes provide explainable constraints.
- Each recommendation keeps classification, explanation, model, and matcher version.
- Functional equivalence is review-only and cannot be silently auto-mapped.

### Visual material search

- Material images remain attached to their original Material Master records and may be indexed by the visual-search service.
- Users can search with an uploaded or reference image and inspect visually similar indexed materials.
- A visual score is not an engineering score. It never directly creates a cluster, mapping, National Material, approval, substitute relationship, or inventory merge.
- Verify a visual candidate through Material Comparison and the normal AI evidence and cluster-review workflow.

### Governance and approvals

- `MaterialMatch` rows are AI evidence, not the primary identity-approval workflow.
- Persisted `MaterialCluster` / `MaterialClusterMember` records are the source of truth once proposed. Cluster status is `PROPOSED`, `UNDER_REVIEW`, `READY_FOR_APPROVAL`, `APPROVED`, or `REJECTED`.
- Membership removal is a persistent `REMOVED` state; it never deletes the Material Master record.
- `EXACT` and `NEAR_DUPLICATE` can be identity candidates. `FUNCTIONAL_EQUIVALENT` is a functional alternative and cannot become an automatic identity mapping.
- The backend owns risk triage, status transitions, final validation, mapping safety, and actionable approval counts; React only renders the returned state.
- Normal mapping permits unmapped-to-NMC or idempotent same-NMC mapping only. Reassignment requires the explicit governed reassignment operation, a reason, and audit evidence.
- Cluster generation, review actions, submission, returns, rejection, approval, mappings, and functional-substitution decisions are audited.

### National master and lineage

- Approved legacy records map to one national material identity.
- National code generation is rule-versioned and includes a check digit.
- Mapping history supports provenance and restoration of prior mappings.
- The 360 page exposes lineage across material, match, mapping, stock, demand, procurement, sync, and audit records.

### Inventory, demand, and procurement intelligence

- Inventory is tracked by CPSE and warehouse with available and reserved quantities.
- Requests can preview allocation before submission.
- Demand and procurement history are aggregated around the national identity.
- Opportunities use stock, demand, supplier, purchase, and timing evidence to identify reuse or savings candidates.

### Integrations and observability

- The connector boundary supports Mock SAP for demos and SAP OData for configured deployments.
- Health indicators are shown in the sidebar and integrations page.
- API logging middleware, structured errors, import statuses, dead letters, and audit records make failures diagnosable.
- FastAPI Swagger at `/docs` is the quickest way to inspect live endpoint contracts.

## 7. Important data lifecycle

```text
Material / inventory source file
        |
        v
ImportBatch + row validation/errors
        |
        v
Normalized Material or Inventory records
        |
        v
MaterialMatch recommendations
        |
        v
Persisted proposed MaterialCluster + members
        |
        v
Human cluster review, risk triage, and submission
        |
        v
Cluster-level approval + audit event
        |
        v
NationalMaterial + legacy mapping
        |
        +--> inventory availability
        +--> material request and allocation
        +--> procurement history/opportunities
        +--> SAP/ERP synchronization
        +--> dashboard, exports, and 360 lineage
```

The most important persistence boundaries are the import batch, material, match evidence, cluster/membership, approval/mapping, national material, inventory, request, procurement, integration sync, and audit records. When debugging a feature, trace the record through those boundaries instead of checking only the page that displayed it.

## 8. Where to look in the code

- Frontend routes and permission gates: `frontend/src/App.jsx`
- Frontend navigation: `frontend/src/components/layout/Sidebar.jsx`
- Frontend API client and session behavior: `frontend/src/services/` and `frontend/src/context/AuthContext.jsx`
- Backend application and router registration: `backend/app/main.py`
- Backend endpoints: `backend/app/routers/`
- Domain logic: `backend/app/services/`
- Database models: `backend/app/models/`
- Schema migrations: `backend/alembic/versions/`
- Role permissions and CPSE scope: `backend/app/utils/rbac.py`
- Environment configuration: `backend/app/config/settings.py`
- AI adapter and service: `ai-service/`
- Mock ERP: `mock-sap/`
- Tests: `backend/tests/`

Existing supporting documents are [ARCHITECTURE.md](ARCHITECTURE.md), [DEMO_FLOW.md](DEMO_FLOW.md), and [API_CONTRACT.md](API_CONTRACT.md). This document is the newcomer-oriented workflow; those documents provide deeper architecture, demo, and service-contract detail.

## 9. Troubleshooting checklist

1. If the UI cannot load data, check `http://localhost:8000/health`, the browser API URL, and the sidebar API status.
2. If matching fails, check the AI service health endpoint and `AI_SERVICE_URL`.
3. If imports remain queued in Docker, check Redis and the `numm-import-worker` container logs.
4. If a user sees an empty menu or 403 response, check the user's role, permissions, and CPSE assignment.
5. If schema errors appear after a pull, run `alembic upgrade head` against the configured database.
6. For a failed import, inspect the batch status, row errors, dead letters, and whether a retry is available.
7. For a cluster that cannot be approved, inspect its risk level, active identity members, technical conflicts, and mapping destination. High-risk engineering exceptions need review; different existing NMCs require mapping-conflict governance.
8. For an incorrect national mapping, inspect the approval history and mapping history before changing data manually. Do not use normal mapping APIs to reassign an existing mapping.
