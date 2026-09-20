import time
from collections import defaultdict, deque

from fastapi.responses import JSONResponse


class LoginRateLimiter:
    """Small in-process guard for login endpoints; reverse proxies still need edge limits."""

    def __init__(self, attempts=10, window_seconds=300):
        self.attempts = attempts
        self.window_seconds = window_seconds
        self.requests = defaultdict(deque)

    async def __call__(self, request, call_next):
        if request.url.path not in {"/api/auth/login", "/api/auth/login-json"}:
            return await call_next(request)
        now = time.monotonic()
        client = request.client.host if request.client else "unknown"
        bucket = self.requests[client]
        while bucket and bucket[0] <= now - self.window_seconds:
            bucket.popleft()
        if len(bucket) >= self.attempts:
            return JSONResponse({"detail": "Too many sign-in attempts. Try again later."}, status_code=429, headers={"Retry-After": str(self.window_seconds)})
        bucket.append(now)
        return await call_next(request)
