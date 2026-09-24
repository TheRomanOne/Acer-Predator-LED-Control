"""Reject HTTP and WebSocket requests that do not come from this machine's own browser.

The API has no authentication: it relies on being reachable only via loopback. Two browser-side
attacks still get through a loopback bind: a web page issuing cross-site requests to
127.0.0.1 (the Origin header gives it away) and DNS rebinding (the Host header does).
"""

from collections.abc import Awaitable, Callable, MutableMapping
from typing import Any
from urllib.parse import urlsplit

Scope = MutableMapping[str, Any]
Receive = Callable[[], Awaitable[MutableMapping[str, Any]]]
Send = Callable[[MutableMapping[str, Any]], Awaitable[None]]
ASGIApp = Callable[[Scope, Receive, Send], Awaitable[None]]

LOOPBACK_HOSTNAMES = frozenset({"localhost", "127.0.0.1", "::1", "[::1]"})
_WS_POLICY_VIOLATION = 1008


def is_local_request(headers: list[tuple[bytes, bytes]]) -> bool:
    """True when the Host header is loopback and the Origin, if present, is too."""
    host = origin = None
    for name, value in headers:
        if name == b"host":
            host = value.decode("latin-1")
        elif name == b"origin":
            origin = value.decode("latin-1")
    if host is None or _hostname("//" + host) not in LOOPBACK_HOSTNAMES:
        return False
    return origin is None or _hostname(origin) in LOOPBACK_HOSTNAMES


def _hostname(url: str) -> str | None:
    try:
        return urlsplit(url).hostname
    except ValueError:
        return None


class LocalOnlyMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self._app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in ("http", "websocket") or is_local_request(scope["headers"]):
            await self._app(scope, receive, send)
            return
        if scope["type"] == "websocket":
            await send({"type": "websocket.close", "code": _WS_POLICY_VIOLATION})
            return
        body = b"requests are only accepted from this machine"
        await send(
            {
                "type": "http.response.start",
                "status": 403,
                "headers": [
                    (b"content-type", b"text/plain"),
                    (b"content-length", str(len(body)).encode()),
                ],
            }
        )
        await send({"type": "http.response.body", "body": body})
