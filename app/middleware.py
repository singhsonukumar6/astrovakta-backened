import time
import json
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from .response import error as _error_resp

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

_PASSTHROUGH_HEADERS = frozenset((
    "content-length", "content-type", "content-encoding", "transfer-encoding",
))


class ResponseWrapMiddleware(BaseHTTPMiddleware):
    """Wrap raw JSON responses in the standard {success, message, data} envelope."""

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if path in SKIP_PATHS or path.startswith("/auth/"):
            return await call_next(request)

        response = await call_next(request)

        content_type = response.headers.get("content-type", "")
        if "application/json" not in content_type:
            return response

        body = b""
        async for chunk in response.body_iterator:
            body += chunk

        custom_headers = {
            k: v for k, v in response.headers.items()
            if k.lower() not in _PASSTHROUGH_HEADERS
        }

        try:
            data = json.loads(body)
        except (json.JSONDecodeError, UnicodeDecodeError):
            return Response(content=body, status_code=response.status_code,
                            media_type="application/json", headers=custom_headers)

        if isinstance(data, dict) and "success" in data:
            return Response(content=body, status_code=response.status_code,
                            media_type="application/json", headers=custom_headers)

        if response.status_code >= 400:
            wrapped = {"success": False, "message": "Validation error" if response.status_code == 422 else "Request failed"}
        else:
            wrapped = {"success": True, "message": "Success"}
        if data is not None:
            wrapped["data"] = data

        return Response(
            content=json.dumps(wrapped).encode(),
            status_code=response.status_code,
            media_type="application/json",
            headers=custom_headers,
        )


class APIKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        if request.method == "OPTIONS":
            return await call_next(request)

        if path in SKIP_PATHS or path.startswith("/auth"):
            response = await call_next(request)
            return response

        if not any(path.startswith(p) for p in PROTECTED_PREFIXES):
            response = await call_next(request)
            return response

        api_key = request.headers.get("X-API-Key")
        if not api_key:
            return _error_resp("Missing X-API-Key header", 401)

        key_info = validate_api_key(api_key)
        if not key_info:
            return _error_resp("Invalid or revoked API key", 401)

        request.state.api_key_info = key_info

        monthly_limit = key_info.get("monthly_limit", 0)
        requests_this_month = key_info.get("requests_this_month", 0)

        if monthly_limit and requests_this_month >= monthly_limit:
            log_usage(key_info["id"], path, 402)
            return _error_resp(
                "Monthly API call limit exceeded",
                402,
                {"monthly_limit": monthly_limit,
                 "requests_this_month": requests_this_month,
                 "reset": "First day of next month UTC",
                 "message": "Contact admin to increase your monthly API call limit"},
            )

        remaining = max(0, monthly_limit - requests_this_month)

        start = time.time()
        response = await call_next(request)
        elapsed = time.time() - start

        log_usage(key_info["id"], path, response.status_code)

        response.headers["X-RateLimit-Limit"] = str(monthly_limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = "First day of next month UTC"

        return response
