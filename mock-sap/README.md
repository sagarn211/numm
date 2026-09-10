# Mock SAP

Demo ERP/SAP service used to prove integration readiness.

Run:

```powershell
uvicorn app.main:app --reload --port 8002
```

Endpoints:

- `GET /health`
- `GET /api/materials`
- `GET /api/materials?cpse_id=1`
- `GET /api/materials/{material_code}`
