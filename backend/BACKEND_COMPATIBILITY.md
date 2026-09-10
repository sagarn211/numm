# Compatibility comparison

| Previous backend/frontend contract | New backend |
|---|---|
| `material_code` | Preserved |
| `description` | Preserved |
| `unit` | Preserved |
| `model` | Preserved |
| `specifications` | Preserved |
| `/api/auth/register` | Preserved |
| `/api/auth/login` | Preserved |
| `/api/auth/me` | Preserved |
| `/api/materials` | Preserved |
| `/api/import` | Preserved |
| `/api/matching/run` | Preserved |
| `/api/matching` | Preserved |
| approve/reject endpoints | Preserved; POST and PUT accepted |
| `/api/national-materials` | Preserved |
| `/api/dashboard/stats` | Preserved with additional fields |
| `/api/audit` | Preserved |

## New additive APIs

- `/api/cpses`
- `/api/materials/paginated`
- `/api/imports/preview`
- `/api/imports/{batch_id}/confirm`
- `/api/imports/{batch_id}/errors`
- `/api/inventory`
- `/api/national-materials/{id}/availability`
- `/api/requests`
- `/api/integrations/sap/*`
- `/api/data-quality`
- `/api/demand`
- `/api/exports/*`

Exact zero-change frontend compatibility can only be guaranteed after checking the
actual current frontend service files. This package preserves all earlier API contracts
we previously defined.
