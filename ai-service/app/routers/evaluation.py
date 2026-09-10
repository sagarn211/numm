import json
import os
from pathlib import Path

from fastapi import APIRouter, HTTPException

router = APIRouter(tags=["Evaluation"])


@router.get("/evaluation")
def evaluation():
    path = Path(os.getenv("EVALUATION_REPORT_PATH", "/app/evaluation/latest.json"))
    if not path.is_file():
        raise HTTPException(503, "No executed model evaluation artifact is available")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HTTPException(500, f"Evaluation artifact is unreadable: {type(exc).__name__}") from exc
