"""Local-only protection: Host/Origin checks, per-launch token, security headers.

There are no accounts, but any web page open in the browser can try to reach
127.0.0.1. The launch token plus strict Host/Origin checks stop that.
"""

from __future__ import annotations

import hmac
import json
from urllib.parse import parse_qs

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from .config import Settings

# Written by Claude Code hooks, which cannot know the token. It only changes
# the cosmetic status of an agent, and still requires a JSON content type
# (which forces a CORS preflight that this server never grants).
OPEN_API_PATHS = {"/api/health"}
HOOK_PATH = "/api/hook"


def _header(scope: Scope, name: bytes) -> str | None:
    for k, v in scope.get("headers", []):
        if k == name:
            return v.decode("latin-1")
    return None


def _token_ok(expected: str, scope: Scope) -> bool:
    supplied = None
    auth = _header(scope, b"authorization")
    if auth and auth.lower().startswith("bearer "):
        supplied = auth[7:].strip()
    if supplied is None:
        query = parse_qs(scope.get("query_string", b"").decode("latin-1"))
        supplied = (query.get("t") or [None])[0]
    return supplied is not None and hmac.compare_digest(supplied, expected)


def _csp(port: int) -> str:
    return "; ".join(
        [
            "default-src 'self'",
            "img-src 'self' data:",
            "style-src 'self' 'unsafe-inline'",
            f"connect-src 'self' ws://127.0.0.1:{port} ws://localhost:{port}",
            "object-src 'none'",
            "base-uri 'none'",
            "frame-ancestors 'none'",
            "form-action 'self'",
        ]
    )


class LocalGuard:
    """Pure ASGI middleware so it covers HTTP and WebSocket the same way."""

    def __init__(self, app: ASGIApp, settings: Settings, token: str) -> None:
        self.app = app
        self.settings = settings
        self.token = token

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        host = _header(scope, b"host")
        origin = _header(scope, b"origin")
        path: str = scope["path"]

        if host not in self.settings.allowed_hosts:
            await self._deny(scope, send, 403, "host not allowed")
            return
        if origin is not None and origin not in self.settings.allowed_origins:
            await self._deny(scope, send, 403, "origin not allowed")
            return

        protected = path.startswith(("/api/", "/ws"))
        if protected and path not in OPEN_API_PATHS:
            if path == HOOK_PATH:
                ctype = (_header(scope, b"content-type") or "").split(";")[0].strip().lower()
                if scope.get("method") != "POST" or ctype != "application/json" or origin is not None:
                    await self._deny(scope, send, 403, "hook requires a JSON POST without Origin")
                    return
            elif not _token_ok(self.token, scope):
                await self._deny(scope, send, 401, "missing or invalid token")
                return

        if scope["type"] == "websocket":
            await self.app(scope, receive, send)
            return

        async def send_with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                extra = {
                    b"content-security-policy": _csp(self.settings.port).encode(),
                    b"x-content-type-options": b"nosniff",
                    b"referrer-policy": b"no-referrer",
                    b"x-frame-options": b"DENY",
                    b"cache-control": b"no-store" if path.startswith("/api/") else b"no-cache",
                }
                present = {k for k, _ in headers}
                headers.extend((k, v) for k, v in extra.items() if k not in present)
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_with_headers)

    async def _deny(self, scope: Scope, send: Send, status: int, reason: str) -> None:
        if scope["type"] == "websocket":
            await send({"type": "websocket.close", "code": 1008})
            return
        body = json.dumps({"detail": reason}).encode()
        await send(
            {
                "type": "http.response.start",
                "status": status,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"content-length", str(len(body)).encode()),
                ],
            }
        )
        await send({"type": "http.response.body", "body": body})
