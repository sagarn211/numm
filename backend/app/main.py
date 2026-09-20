import logging
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.config.settings import settings
from app.routers import procurement
from app.routers import clusters
from app.routers import mapping_history
from app.routers import visual_search
import app.models

from app.middleware.error_middleware import error_middleware
from app.middleware.logging_middleware import logging_middleware
from app.middleware.rate_limit_middleware import LoginRateLimiter
from app.routers import (
    auth, cpses, materials, imports, matching, approvals, national_materials,
    inventory, requests, audit, dashboard, integrations, data_quality, demand, exports, users, notifications
)

logging.basicConfig(level=logging.INFO)
if not settings.SECRET_KEY or settings.SECRET_KEY.lower().startswith(("dev-secret", "change-this", "replace-with")):
    raise RuntimeError("SECRET_KEY must be configured with a non-placeholder value")

app = FastAPI(
    title="National Unified Material Master API",
    version="1.0.0",
    description="One Nation - One Material Code",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(dict.fromkeys([
        settings.FRONTEND_URL,
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ])),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.middleware("http")(logging_middleware)
app.middleware("http")(LoginRateLimiter())
app.middleware("http")(error_middleware)

for router in [
    procurement.router,
    clusters.router,
    mapping_history.router,
    auth.router, cpses.router, materials.router, imports.router, matching.router,
    approvals.router, national_materials.router, inventory.router, requests.router,
    audit.router, dashboard.router, integrations.router, data_quality.router,
    demand.router, exports.router, users.router, visual_search.router, notifications.router,
]:
    app.include_router(router)

@app.get("/")
def root():
    return {
        "name": "National Unified Material Master",
        "theme": "One Nation - One Material Code",
        "version": "1.0.0",
    }

@app.get("/health")
def health(db: Session = Depends(get_db)):
    """Report ready only when the API can also reach PostgreSQL."""
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=503, detail="Database is unavailable") from exc
    return {"status": "ok", "database": "ok"}
