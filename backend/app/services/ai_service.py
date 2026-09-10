import httpx
import logging
from app.config.settings import settings

logger = logging.getLogger(__name__)

class AIServiceUnavailable(Exception):
    pass

async def ai_health():
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(f"{settings.AI_SERVICE_URL}/health")
            r.raise_for_status()
            return r.json()
    except Exception:
        logger.exception("AI service health check failed")
        return {"status": "offline", "error": "AI service unreachable"}


async def ai_evaluation():
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"{settings.AI_SERVICE_URL}/evaluation")
            response.raise_for_status()
            data = response.json()
            if not isinstance(data, dict) or "accuracy" not in data:
                raise AIServiceUnavailable("AI evaluation artifact is malformed")
            return data
    except AIServiceUnavailable:
        raise
    except Exception as exc:
        raise AIServiceUnavailable(str(exc)) from exc

async def match_batch(materials, focus_material_ids=None):
    payload = {"materials": materials, "focus_material_ids": sorted(focus_material_ids or [])}
    url = f"{settings.AI_SERVICE_URL}/api/v1/match-batch"
    timeout = httpx.Timeout(settings.AI_BATCH_TIMEOUT_SECONDS, connect=10.0)
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
    except Exception as exc:
        raise AIServiceUnavailable(
            f"AI batch matching failed at {url}: {type(exc).__name__}: {exc}"
        ) from exc
    if isinstance(data, list):
        return {"matches": data}
    if isinstance(data, dict) and isinstance(data.get("matches"), list):
        return data
    raise AIServiceUnavailable("AI response missing a valid matches list")


async def match_pair(material_a, material_b):
    """Return the real AI verdict for one explicitly selected material pair."""
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{settings.AI_SERVICE_URL}/api/v1/match",
                json={"material_a": material_a, "material_b": material_b},
            )
            response.raise_for_status()
            data = response.json()
            if not isinstance(data, dict) or "final_score" not in data:
                raise AIServiceUnavailable("AI response missing pair-match scores")
            return data
    except AIServiceUnavailable:
        raise
    except Exception as exc:
        raise AIServiceUnavailable(str(exc)) from exc

async def find_candidates(material, candidates, top_k=10):
    payload = {
        "material": material,
        "candidates": candidates,
        "top_k": top_k,
    }
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{settings.AI_SERVICE_URL}/api/v1/candidates",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            if not isinstance(data, dict) or "matches" not in data:
                raise AIServiceUnavailable("AI response missing matches")
            return data["matches"]
    except AIServiceUnavailable:
        raise
    except Exception as exc:
        raise AIServiceUnavailable(str(exc)) from exc
