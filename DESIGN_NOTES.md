# NUMM Design Notes

NUMM standardizes material-master records across participating CPSEs. The
application is a React/Vite client, a FastAPI service, PostgreSQL, Redis/Celery
for import jobs, and a separate matching service.

## Boundaries

- The backend owns authorization, CPSE access checks, audit records, and all
  workflow state. The client does not make authorization decisions.
- A user is assigned to at most one CPSE. CPSE-scoped data is enforced in the
  API using the authenticated user's assignment.
- Public registration creates a pending user. A system administrator must
  assign a role and CPSE before that account can access protected workflows.

## Material workflow

1. A CPSE imports or creates material records.
2. The matching service generates candidate relationships using semantic,
   attribute, and fuzzy evidence.
3. Reviewers govern clusters and mappings under maker-checker restrictions.
4. Approved mappings create National Material records and preserve audit data.

## Request workflow

1. A requesting officer creates a material request for their assigned CPSE.
2. Submission reserves available inventory and marks any unmet quantity for
   procurement.
3. A different authorized officer approves or rejects the request.
4. Fulfilment converts reservations into allocated inventory.

## Notifications

Notifications are individual records, not a shared CPSE inbox. CPSE context is
used only to select recipients. Each officer has independent unread/read state.
Request and account-workflow events create notifications for the affected user
and, when appropriate, approved users assigned to the same CPSE.

## Local operation

`docker compose up --build` starts PostgreSQL, Redis, the backend, import
worker, matching service, mock SAP service, and frontend. The backend applies
Alembic migrations before it starts serving requests.
