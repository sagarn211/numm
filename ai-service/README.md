# NUMM AI Service

Runs on port `8001`.

## Endpoints

- `GET /health`
- `POST /api/v1/match`
- `POST /api/v1/match-batch`
- `POST /api/v1/candidates`

## Teammate integration

Do not change the HTTP routes after frontend/backend integration.

Connect teammate logic inside:

`src/teammate_bridge.py`

The included fallback matcher exists only so the whole application can be integration-tested
before the teammate model is connected. It must not be presented as the final industrial AI.
