import logging
from fastapi.responses import JSONResponse
logger = logging.getLogger(__name__)

async def error_middleware(request, call_next):
    try:
        return await call_next(request)
    except Exception as exc:
        logger.exception("Unhandled error: %s", exc)
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})
