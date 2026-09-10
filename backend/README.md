# National Unified Material Master — Main Backend

Run:

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(48))"
# Paste the generated value after SECRET_KEY= in .env.
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

Swagger: http://localhost:8000/docs

## Compatibility retained

The following previous API routes are preserved:
- POST /api/auth/register
- POST /api/auth/login
- GET /api/auth/me
- POST /api/materials
- GET /api/materials
- GET /api/materials/{id}
- POST /api/import
- POST /api/matching/run
- GET /api/matching
- POST/PUT /api/approvals/{id}/approve
- POST/PUT /api/approvals/{id}/reject
- POST /api/national-materials
- GET /api/national-materials
- GET /api/dashboard/stats
- GET /api/audit

The old frontend field names `material_code`, `description`, `unit`, `model`, and
`specifications` are intentionally retained. New canonical meanings are implemented
without forcing a frontend rename.

## Remediation features

- New and imported materials receive rule-versioned category/subcategory assignments.
- Safety-critical canonical conflicts block approval until explicitly resolved.
- New national codes use `NMC-{category}-{subcategory}-{sequence}-{check-digit}`.
- Imports support idempotent queued execution, progress, cancellation, parallel chunk
  preparation, hard limits, retry/dead-letter handling, AI candidate generation, and
  a durable Celery/Redis worker in Docker Compose.
- SAP integration uses MOCK and ODATA connectors with health checks, OAuth/mTLS,
  throttling, delta pagination, idempotent push-back, and reconciliation.
- Dashboard analytics include duplicate risk, mapping coverage, approval time, import errors,
  excess inventory and price-backed savings estimates.

Apply the schema migration before starting the updated application:

```bash
alembic upgrade head
```

The baseline migration creates fresh databases as well as tracking schema ownership through
Alembic. Local development defaults to in-process background imports; Docker Compose sets
`IMPORT_QUEUE_MODE=celery`.

AI remains a separate service. This backend only calls it through HTTP.
