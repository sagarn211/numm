from contextlib import asynccontextmanager

from fastapi import FastAPI
from app.engine_adapter import log_engine_startup
from app.routers import evaluation, health, matching, visual_search


@asynccontextmanager
async def lifespan(_app: FastAPI):
    log_engine_startup()
    yield

app = FastAPI(
    title="NUMM AI Matching Service",
    version="1.0.0",
    description="AI-assisted material matching service for National Unified Material Master",
    lifespan=lifespan,
)

app.include_router(health.router)
app.include_router(matching.router)
app.include_router(evaluation.router)
app.include_router(visual_search.router)

@app.get("/")
def root():
    return {
        "service": "NUMM AI Matching Service",
        "docs": "/docs",
    }
