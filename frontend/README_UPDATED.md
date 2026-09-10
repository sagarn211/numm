# Updated NUMM Frontend

This version keeps the original UI but replaces mock-first API behavior with real integration to the new FastAPI backend.

## Run
```powershell
cd frontend
npm install
Copy-Item .env.example .env
npm run dev
```

## Backend expected
`VITE_API_URL=http://localhost:8000`

## Important fixes
- OAuth2 form login now matches `/api/auth/login`.
- Registration uses JSON body.
- Import uses `/api/imports/preview` then `/api/imports/{id}/confirm`.
- Audit uses `/api/audit`.
- Dashboard derives its extra widgets from APIs that really exist.
- AI recommendations adapt backend snake_case match records to the existing visual cards.
- New pages: Inventory, Material Requests, CPSE Management, Data Quality, Integrations.
- AI is not implemented in React; frontend only talks to main backend.
