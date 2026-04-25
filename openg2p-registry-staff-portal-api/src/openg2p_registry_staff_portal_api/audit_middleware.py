"""
Audit middleware — emits one CloudEvent to OpenG2P Audit Manager per
authenticated API call.

Mirrors the pattern of `iam_core.user_auth.middleware.AuthMiddleware`:

  * Registered AFTER AuthMiddleware in main.py → becomes the OUTERMOST
    middleware. Request flow: AuditMiddleware → AuthMiddleware → handler →
    response → AuthMiddleware → AuditMiddleware. By the time we read
    request.state.auth and the response status, both are populated.

  * Skips:
      - Health/probe endpoints (/ping)
      - OpenAPI surfaces (/docs, /redoc, /openapi.json, oauth2-redirect)
      - OPTIONS preflight requests
      - Anonymous calls (no request.state.auth) — implements the
        "only audit authenticated user calls" policy with no per-route
        allowlist needed.

  * Emission is fire-and-forget via `asyncio.create_task` — never delays
    the response. All errors are logged, never raised to the caller.

  * Disabled by default: set REGISTRY_STAFF_PORTAL_API_AUDIT_ENABLED=true
    AND REGISTRY_STAFF_PORTAL_API_AUDIT_MANAGER_URL=<base-url> to turn on.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

import httpx
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.routing import Match

from .config import Settings

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)


_SKIP_PATHS = frozenset(
    {
        "/ping",
        "/openapi.json",
        "/docs",
        "/redoc",
        "/docs/oauth2-redirect",
    }
)


def _status_to_outcome(status_code: int) -> str:
    """Map HTTP status to CloudEvents outcome enum."""
    if 200 <= status_code < 300:
        return "success"
    if status_code in (401, 403):
        return "denied"
    return "failure"


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


class AuditMiddleware(BaseHTTPMiddleware):
    """Emit one CloudEvent to Audit Manager per authenticated API call."""

    def __init__(
        self,
        app,
        *,
        audit_manager_url: str | None,
        enabled: bool = True,
        timeout_seconds: float = 2.0,
        source: str = "/openg2p/registry-staff-portal-api",
        module: str = "registry-staff-portal-api",
        client_id: str | None = None,
        state_key: str = "auth",
    ):
        super().__init__(app)
        self._url = (audit_manager_url or "").rstrip("/")
        self._enabled = enabled and bool(self._url)
        self._timeout_seconds = timeout_seconds
        self._source = source
        self._module = module
        self._client_id = client_id
        self._state_key = state_key
        self._client: httpx.AsyncClient | None = None

        if self._enabled:
            _logger.info(
                "AuditMiddleware enabled — emitting to %s",
                self._url + "/v1/auditmanager/events",
            )
        else:
            _logger.info(
                "AuditMiddleware disabled (enabled=%s, url=%r). No-op.",
                enabled,
                audit_manager_url,
            )

    def _get_client(self) -> httpx.AsyncClient:
        # Lazy-create on first emit so import time is unaffected.
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self._timeout_seconds),
            )
        return self._client

    def _match_route(self, request: Request) -> Any | None:
        """Match the request to its FastAPI route (mirrors AuthMiddleware)."""
        router = getattr(request.app, "router", None)
        for route in getattr(router, "routes", []):
            match, _ = route.matches(request.scope)
            if match == Match.FULL:
                return route
        return None

    async def dispatch(self, request: Request, call_next):
        # Always run the inner stack first — never delay the user's response.
        response = await call_next(request)

        # Audit decision: should we emit for this request?
        if not self._enabled:
            return response
        if request.method == "OPTIONS":
            return response
        if request.url.path in _SKIP_PATHS:
            return response

        principal = getattr(request.state, self._state_key, None)
        if principal is None:
            # Anonymous request — AuthMiddleware let it through with
            # allow_by_default=True. Skip per "only audit authenticated user calls".
            return response

        # Build event and fire-and-forget (never blocks the response).
        try:
            route = self._match_route(request)
            event = self._build_event(request, response, principal, route)
            asyncio.create_task(self._emit(event))
        except Exception:
            _logger.exception("AuditMiddleware: failed to build event; skipping")

        return response

    def _build_event(
        self,
        request: Request,
        response,
        principal,
        route,
    ) -> dict:
        # Endpoint function name → CloudEvents `type` and `action` derivation.
        func_name = "unknown"
        if route is not None and getattr(route, "endpoint", None) is not None:
            func_name = route.endpoint.__name__

        # First word of the function name as the action verb (best effort).
        action = func_name.split("_", 1)[0] if "_" in func_name else func_name

        # Roles for this user on this client.
        roles: list[str] = []
        if self._client_id and principal.client_roles:
            roles = list(principal.client_roles.get(self._client_id, []))

        return {
            "specversion": "1.0",
            "id": str(uuid4()),
            "source": self._source,
            "type": f"org.openg2p.staff_portal.{func_name}",
            "time": _now_iso(),
            "datacontenttype": "application/json",
            "data": {
                "actor": {
                    "type": "user",
                    "id": principal.sub or "",
                    "name": principal.name,
                    "roles": roles,
                    "ip": request.client.host if request.client else None,
                },
                "action": action,
                "outcome": _status_to_outcome(response.status_code),
                "context": {
                    "api": f"{request.method} {request.url.path}",
                    "module": self._module,
                    "http_status": response.status_code,
                    "request_id": request.headers.get("x-request-id"),
                },
            },
        }

    async def _emit(self, event: dict) -> None:
        """POST a single CloudEvent. Errors logged, never raised."""
        try:
            client = self._get_client()
            url = f"{self._url}/v1/auditmanager/events"
            resp = await client.post(url, json=event)
            if resp.status_code != 202:
                _logger.warning(
                    "Audit Manager returned %s for event %s: %s",
                    resp.status_code,
                    event["id"],
                    resp.text[:200],
                )
        except httpx.HTTPError as exc:
            _logger.warning(
                "Audit emission failed for event %s: %s", event["id"], exc
            )
        except Exception:
            _logger.exception(
                "Audit emission failed unexpectedly for event %s",
                event.get("id"),
            )
