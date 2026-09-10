# NUMM Remaining Project Components

Copy these folders/files into the root of your existing `numm/` project.

Expected final structure:

```text
numm/
├── backend/
├── frontend/
├── ai-service/
├── mock-sap/
├── datasets/
├── docs/
├── scripts/
├── docker-compose.yml
├── .env
└── README.md
```

## Important AI note

`ai-service/app/engine_adapter.py` gives the API a stable contract.

It first tries to load teammate matching code from `ai-service/src/teammate_bridge.py`.
If that bridge is not implemented, it uses a safe lightweight fallback matcher for integration testing.

The fallback is NOT your final engineering AI model. Replace only the bridge implementation,
not the HTTP endpoints.

## Local run order

1. PostgreSQL
2. Main backend on 8000
3. AI service on 8001
4. Mock SAP on 8002
5. React frontend on 5173

Or use `scripts/start-all.ps1`.
