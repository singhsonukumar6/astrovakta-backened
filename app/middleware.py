import re
import time
import json
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from .response import error as _error_resp

from .auth import validate_api_key, log_usage, get_credit_cost

# Static fallback used only if route introspection fails on a future FastAPI
# version — deny-by-default is too important to silently degrade.
FALLBACK_PROTECTED_PREFIXES = (
    "/api/", "/horoscope/", "/chart/", "/pooja/", "/reports/", "/dasha/",
    "/calendar-api/", "/kp", "/lal-kitab", "/lucky", "/varshaphal",
    "/ai/", "/numerology", "/yogini", "/prashna",
)

SKIP_PATHS = {
    "/health",
    "/docs",
    "/openapi.json",
    "/redoc",
    "/robots.txt",
    "/llms.txt",
    "/favicon.ico",
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


class SecurityHeadersMiddleware:
    """Baseline hardening headers on every HTTP response."""

    _HEADERS = (
        (b"x-content-type-options", b"nosniff"),
        (b"referrer-policy", b"strict-origin-when-cross-origin"),
        (b"x-frame-options", b"DENY"),
    )

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def _send(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                present = {k.lower() for k, _ in headers}
                headers.extend(h for h in self._HEADERS if h[0] not in present)
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, _send)


class APIKeyMiddleware:
    """Pure ASGI middleware so CORS headers are always applied.

    Enforces the X-API-Key (validation + credit accounting) on every route
    that is neither public nor guarded by the platform JWT dependencies.
    The route table is classified once from the FastAPI app (scope["app"])
    on the first request, so newly mounted routers are protected by default
    — no prefix list to fall out of sync.
    """

    # Paths that never require an API key (public content, webhooks with
    # their own auth, docs). JWT-guarded routes are detected automatically
    # from their dependencies and also pass through.
    PUBLIC_PREFIXES = (
        "/auth",
        "/api/page-config",
        "/api/blogs",
        "/api/location/",
        # tenant visitor sites (booking/store auth is handled per-route)
        "/sites/site",
        "/sites/invoice/",
        "/sites/check-slug",
        "/sites/check-domain",
        "/sites/templates",
        # integration callbacks & the WP plugin claim endpoint authenticate
        # via single-use state / activation key, not an API key
        "/sites/integrations/",
        # payment webhooks verify their own signatures
        "/payments/webhook",
        "/payments/razorpay/webhook",
    )

    _JWT_GUARD_NAMES = frozenset(("get_current_user", "require_admin"))

    def __init__(self, app):
        self.app = app
        self._route_table = None  # [(path_regex, requires_api_key)]

    def _collect_api_routes(self, routes, prefix=""):
        """Flatten (path, APIRoute) pairs, following FastAPI's router
        inclusions. Newer FastAPI wraps each include_router() in an
        _IncludedRouter (original_router + include_context.prefix)."""
        from fastapi.routing import APIRoute

        out = []
        for route in routes:
            if isinstance(route, APIRoute):
                out.append((prefix + route.path, route))
                continue
            inner = getattr(route, "original_router", None)
            if inner is not None:
                inc_prefix = getattr(getattr(route, "include_context", None), "prefix", "") or ""
                out += self._collect_api_routes(inner.routes, prefix + inc_prefix)
            elif hasattr(route, "routes"):
                out += self._collect_api_routes(route.routes, prefix + (getattr(route, "path", "") or ""))
        return out

    @staticmethod
    def _path_regex(path_template):
        parts = re.split(r"(\{[^}]+\})", path_template)
        pattern = "".join("[^/]+" if p.startswith("{") else re.escape(p) for p in parts)
        return re.compile("^" + pattern + "$")

    def _build_route_table(self, fastapi_app):
        try:
            routes = self._collect_api_routes(fastapi_app.routes)
        except Exception:
            return None  # signal: use the static fallback prefixes

        def collect_guards(dep, into):
            call = getattr(dep, "call", None)
            if call is not None:
                into.add(getattr(call, "__name__", ""))
            for sub in getattr(dep, "dependencies", None) or []:
                collect_guards(sub, into)

        table = []
        for path, route in routes:
            guards = set()
            collect_guards(getattr(route, "dependant", None), guards)
            jwt_guarded = bool(guards & self._JWT_GUARD_NAMES)
            public = path.startswith(self.PUBLIC_PREFIXES)
            table.append((self._path_regex(path), not (jwt_guarded or public)))
        return table

    def _requires_api_key(self, scope, path):
        if self._route_table is None:
            fastapi_app = scope.get("app")
            if fastapi_app is None:
                return False
            self._route_table = self._build_route_table(fastapi_app)
        if self._route_table is None:
            # introspection failed — fall back to explicit prefixes
            return path.startswith(FALLBACK_PROTECTED_PREFIXES)
        for regex, needs_key in self._route_table:
            if regex.match(path):
                return needs_key
        return False  # unmatched paths 404/405 downstream

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope["path"]

        if scope["method"] == "OPTIONS":
            await self.app(scope, receive, send)
            return

        if path in SKIP_PATHS or path.startswith(self.PUBLIC_PREFIXES):
            await self.app(scope, receive, send)
            return

        if not self._requires_api_key(scope, path):
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
        credits_this_month = key_info.get("credits_this_month", 0)
        credit_cost = get_credit_cost(path)

        if monthly_limit and (credits_this_month + credit_cost) > monthly_limit:
            log_usage(key_info["id"], path, 402, credits=credit_cost)
            response = _error_resp(
                "Monthly API call limit exceeded",
                402,
                {"monthly_limit": monthly_limit,
                 "credits_this_month": credits_this_month,
                 "credit_cost": credit_cost,
                 "reset": "First day of next month UTC",
                 "message": "Contact admin to increase your monthly credit limit"},
            )
            await response(scope, receive, send)
            return

        remaining = max(0, monthly_limit - credits_this_month)

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
        log_usage(key_info["id"], path, response_status[0], credits=credit_cost)
