import logging, time
logger = logging.getLogger("numm.api")

async def logging_middleware(request, call_next):
    started = time.perf_counter()
    response = await call_next(request)
    ms = round((time.perf_counter() - started) * 1000, 2)
    logger.info("%s %s -> %s (%sms)", request.method, request.url.path, response.status_code, ms)
    return response
