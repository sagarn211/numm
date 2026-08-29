import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.database import (
    Base,
    engine
)

from app.config.settings import settings

from app.models import (
    User,
    CPSE,
    Material,
    MaterialMatch,
    NationalMaterial,
    MaterialMapping,
    ImportBatch,
    AuditLog
)

from app.middleware.error_middleware import (
    error_middleware
)

from app.middleware.logging_middleware import (
    logging_middleware
)

from app.routers import (
    materials,
    imports,
    matching,
    approvals,
    national_materials,
    dashboard,
    audit,
    auth
    
)


logging.basicConfig(
    level=logging.INFO
)


# Create database tables
Base.metadata.create_all(
    bind=engine
)


app = FastAPI(
    title=(
        "National Unified "
        "Material Master API"
    ),
    description=(
        "AI-powered platform for "
        "material master standardization "
        "across CPSEs."
    ),
    version="1.0.0"
)


# Middleware
app.middleware(
    "http"
)(error_middleware)

app.middleware(
    "http"
)(logging_middleware)


# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.FRONTEND_URL,
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


# Routers
app.include_router(
    materials.router
)

app.include_router(
    imports.router
)

app.include_router(
    matching.router
)

app.include_router(
    approvals.router
)

app.include_router(
    national_materials.router
)

app.include_router(
    dashboard.router
)

app.include_router(
    audit.router
)

app.include_router(
    audit.router,
    prefix="/api/audit-trail"
)

app.include_router(
    auth.router
)

@app.get("/")
def root():

    return {
        "success": True,
        "message": (
            "National Unified Material "
            "Master API is running"
        )
    }


@app.get("/health")
def health():

    return {
        "success": True,
        "status": "healthy"
    }