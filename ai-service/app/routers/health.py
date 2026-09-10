from fastapi import APIRouter
from app.engine_adapter import engine_health

router = APIRouter(tags=["Health"])

@router.get("/health")
def health():
    return engine_health()
