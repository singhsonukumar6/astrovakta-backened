import time
import json
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


class ResponseWrapMiddleware:
    """Wrap raw JSON responses in the standard {success, message, data} envelope."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope["path"]
        if path in SKIP_PATHS or path.startswith("/auth/"):
            await self.app(scope, receive, send)
            return

        async def _send(message):
            if message["type"] == "http.response.start":
                headers = dict(message.get("headers", []))
                content_type = headers.get(b"content-type", b"").decode()
                message["_captured_status"] = message["status"]
                message["_captured_headers"] = headers

            elif message["type"] == "http.response.body":
                body = message.get("body", b"")

                headers = message.get("_captured_headers", {})
                status = message.get("_captured_status", 200)

                custom_headers = [
                    (k, v) for k, v in headers.items()
                    if k.decode().lower() not in _PASSTHROUGH_HEADERS
                ]

                content_type = headers.get(b"content-type", b"").decode()
                if b"application/json" not in content_type:
                    await send({
                        "type": "http.response.start",
                        "status": status,
                        "headers": custom_headers,
                    })
                    await send({
                        "type": "http.response.body",
                        "body": body,
                    })
                    return

                try:
                    data = json.loads(body)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    await send({
                        "type": "http.response.start",
                        "status": status,
                        "headers": custom_headers,
                    })
                    await send({
                        "type": "http.response.body",
                        "body": body,
                    })
                    return

                if isinstance(data, dict) and "success" in data:
                    await send({
                        "type": "http.response.start",
                        "status": status,
                        "headers": custom_headers,
                    })
                    await send({
                        "type": "http.response.body",
                        "body": body,
                    })
                    return

                if status >= 400:
                    wrapped = {"success": False, "message": "Validation error" if status == 422 else "Request failed"}
                else:
                    wrapped = {"success": True, "message": "Success"}
                if data is not None:
                    wrapped["data"] = data

                wrapped_body = json.dumps(wrapped).encode()

                await send({
                    "type": "http.response.start",
                    "status": status,
                    "headers": custom_headers,
                })
                await send({
                    "type": "http.response.body",
                    "body": wrapped_body,
                })
                return

            await send(message)

        await self.app(scope, receive, _send)


class APIKeyMiddleware:
    """Pure ASGI middleware so CORS headers are always applied."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope["path"]

        if scope["method"] == "OPTIONS":
            await self.app(scope, receive, send)
            return

        if path in SKIP_PATHS or path.startswith("/auth"):
            await self.app(scope, receive, send)
            return

        if not any(path.startswith(p) for p in PROTECTED_PREFIXES):
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive)

        api_key = request.headers.get("X-API-Key")
        if not api_key:
            response = _error_resp("Missing X-API-Key header", 401)
            await response(scope, receive, send)
            return

        key_info = validate_api_key(api_key)
        if not key_info:
            response = _error_resp("Invalid or revoked API key", 401)
            await response(scope, receive, send)
            return

        request.state.api_key_info = key_info

        monthly_limit = key_info.get("monthly_limit", 0)
        requests_this_month = key_info.get("requests_this_month", 0)

        if monthly_limit and requests_this_month >= monthly_limit:
            log_usage(key_info["id"], path, 402)
            response = _error_resp(
                "Monthly API call limit exceeded",
                402,
                {"monthly_limit": monthly_limit,
                 "requests_this_month": requests_this_month,
                 "reset": "First day of next month UTC",
                 "message": "Contact admin to increase your monthly API call limit"},
            )
            await response(scope, receive, send)
            return

        remaining = max(0, monthly_limit - requests_this_month)

        start = time.time()
        response_status = [200]

        async def _send(message):
            if message["type"] == "http.response.start":
                response_status[0] = message["status"]
                headers = list(message.get("headers", []))
                headers = [(k, v) for k, v in headers
                    if k.decode().lower() not in ("x-ratelimit-limit", "x-ratelimit-remaining", "x-ratelimit-reset")]
                headers.append((b"x-ratelimit-limit", str(monthly_limit).encode()))
                headers.append((b"x-ratelimit-remaining", str(remaining).encode()))
                headers.append((b"x-ratelimit-reset", b"First day of next month UTC"))
                message["headers"] = headers

            await send(message)

        await self.app(scope, request.receive, _send)

        elapsed = time.time() - start
        log_usage(key_info["id"], path, response_status[0])
