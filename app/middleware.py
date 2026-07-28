import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from .auth import validate_api_key, log_usage

PROTECTED_PREFIXES = (
    "/api/",
    "/horoscope/",
    "/chart/",
    "/pooja/",
    "/reports/",
    "/dasha/",
    "/calendar-api/",
)

SKIP_PATHS = {
    "/health",
    "/docs",
    "/openapi.json",
    "/redoc",
}


class APIKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        if path in SKIP_PATHS or path.startswith("/auth"):
            response = await call_next(request)
            return response

        if not any(path.startswith(p) for p in PROTECTED_PREFIXES):
            response = await call_next(request)
            return response

        api_key = request.headers.get("X-API-Key")
        if not api_key:
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing X-API-Key header"},
            )

        key_info = validate_api_key(api_key)
        if not key_info:
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid or revoked API key"},
            )

        # Attach key info so routers can access user_id
        request.state.api_key_info = key_info

        rate_limit = key_info["rate_limit"]
        request_count = key_info["request_count"]

        if request_count > rate_limit:
            log_usage(key_info["id"], path, 402)
            return JSONResponse(
                status_code=402,
                content={
                    "detail": "Rate limit exceeded",
                    "tier": key_info["tier"],
                    "rate_limit": rate_limit,
                    "requests_today": request_count,
                },
            )

        remaining = max(0, rate_limit - request_count)

        start = time.time()
        response = await call_next(request)
        elapsed = time.time() - start

        log_usage(key_info["id"], path, response.status_code)

        response.headers["X-RateLimit-Limit"] = str(rate_limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Tier"] = key_info["tier"]
        response.headers["X-Response-Time"] = f"{elapsed:.3f}s"

        return response
