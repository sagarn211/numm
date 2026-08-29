import logging

from fastapi import Request
from fastapi.responses import JSONResponse


logger = logging.getLogger(__name__)


async def error_middleware(
    request: Request,
    call_next
):

    try:

        response = await call_next(request)

        return response

    except Exception as exc:

        logger.exception(
            "Unhandled exception: %s",
            exc
        )

        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": "Internal server error"
            }
        )