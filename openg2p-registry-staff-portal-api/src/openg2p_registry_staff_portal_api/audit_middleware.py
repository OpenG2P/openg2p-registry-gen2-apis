"""
Audit middleware — emits one CloudEvent to OpenG2P Audit Manager per
audited API call.

Mirrors the pattern of `iam_core.user_auth.middleware.AuthMiddleware`:

  * Registered AFTER AuthMiddleware in main.py → becomes the OUTERMOST
    middleware. Request flow: AuditMiddleware → AuthMiddleware → handler →
    response → AuthMiddleware → AuditMiddleware. By the time we read
    request.state.auth and the response status, both are populated.

Audit policy (v2):

  Request kind                                              | Audited?
  --------------------------------------------------------- | --------
  Authenticated (request.state.auth set), any outcome       | YES
  Anonymous + outcome 2xx (legitimate public endpoint)      | NO
  Anonymous + outcome non-2xx, audit_anonymous_failures=true| YES (anon)
  Health probes / OpenAPI surfaces / OPTIONS preflight      | NO

For 403 (Forbidden) responses the JWT was definitely valid (AuthMiddleware
validated it before raising the perms error), so we decode the bearer
token to recover the real actor — even though `request.state.auth` is
not set on that path. For 401 (Unauthorized) responses the JWT may be
invalid/missing/expired, so we record the call as anonymous (only the
client IP is trustworthy).

Emission is fire-and-forget via `asyncio.create_task` — never delays the
response. All errors are logged, never raised to the caller.

Disabled by default: set REGISTRY_STAFF_PORTAL_API_AUDIT_ENABLED=true
AND REGISTRY_STAFF_PORTAL_API_AUDIT_MANAGER_URL=<base-url> to turn on.
Set REGISTRY_STAFF_PORTAL_API_AUDIT_ANONYMOUS_FAILURES=false to skip
auditing of rejected anonymous calls.
"""

from __future__ import annotations

import asyncio
import base64
import json
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


def _decode_jwt_payload(token: str) -> dict | None:
    """Base64url-decode a JWT's payload segment WITHOUT verifying the signature.

    Safe to use only on tokens we know were validated by an upstream
    middleware (e.g. AuthMiddleware confirms signature validity before
    raising 403). For untrusted tokens (401 path), do NOT trust the
    decoded claims — record the request as anonymous instead.
    """
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        payload = parts[1]
        payload += "=" * (-len(payload) % 4)
        return json.loads(base64.urlsafe_b64decode(payload))
    except Exception:
        return None


def _extract_bearer(request: Request) -> str | None:
    """Pull the bearer token from the Authorization header, or None."""
    auth = request.headers.get("authorization", "")
    parts = auth.split(maxsplit=1)
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1]
    return None


def _client_ip(request: Request) -> str | None:
    """Real client IP — prefer the first hop in `X-Forwarded-For` so audits
    behind Istio / a load balancer record the actual user, not the proxy."""
    xff = request.headers.get("x-forwarded-for")
    if xff:
        first = xff.split(",", 1)[0].strip()
        if first:
            return first
    real = request.headers.get("x-real-ip")
    if real:
        return real.strip()
    return request.client.host if request.client else None


class AuditMiddleware(BaseHTTPMiddleware):
    """Emit one CloudEvent to Audit Manager per audited API call."""

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
        audit_anonymous_failures: bool = True,
    ):
        super().__init__(app)
        self._url = (audit_manager_url or "").rstrip("/")
        self._enabled = enabled and bool(self._url)
        self._timeout_seconds = timeout_seconds
        self._source = source
        self._module = module
        self._client_id = client_id
        self._state_key = state_key
        self._audit_anonymous_failures = audit_anonymous_failures
        self._client: httpx.AsyncClient | None = None

        if self._enabled:
            _logger.info(
                "AuditMiddleware enabled — emitting to %s "
                "(audit_anonymous_failures=%s)",
                self._url + "/v1/auditmanager/events",
                self._audit_anonymous_failures,
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

    # ---------- audit decision ----------

    async def dispatch(self, request: Request, call_next):
        # Always run the inner stack first — never delay the user's response.
        response = await call_next(request)

        if not self._enabled:
            return response
        if request.method == "OPTIONS":
            return response
        if request.url.path in _SKIP_PATHS:
            return response

        principal = getattr(request.state, self._state_key, None)
        is_success = 200 <= response.status_code < 300

        # Decide: should we emit for this request?
        if principal is not None:
            # Authenticated and let through — always emit.
            pass
        elif (not is_success) and self._audit_anonymous_failures:
            # Rejected anonymous-looking call — emit per v2 policy.
            pass
        else:
            # Successful anonymous (legitimate public endpoint) — skip.
            return response

        # Build event and fire-and-forget (never blocks the response).
        try:
            route = self._match_route(request)
            actor = self._build_actor(request, principal, response)
            event = self._build_event(request, response, actor, route)
            asyncio.create_task(self._emit(event))
        except Exception:
            _logger.exception("AuditMiddleware: failed to build event; skipping")

        return response

    # ---------- actor construction ----------

    def _build_actor(self, request: Request, principal, response) -> dict:
        """Produce the `data.actor` payload from the best available identity source.

        Three paths, in order of preference:
          1. AuthPrincipal (request.state.auth set) — name, sub, roles.
             Try to enrich with `username` and `session_id` from JWT claims
             since AuthPrincipal doesn't carry them.
          2. 403 Forbidden + bearer token — JWT is known-valid (AuthMiddleware
             verified it before raising), so decode is trustworthy.
          3. Anonymous fallback — actor.type=anonymous, only IP is recorded.
        """
        ip = _client_ip(request)
        bearer = _extract_bearer(request)

        if principal is not None:
            roles: list[str] = []
            if self._client_id and principal.client_roles:
                roles = list(principal.client_roles.get(self._client_id, []))
            # Enrich from JWT claims (AuthPrincipal lacks preferred_username
            # and session_state).
            username = None
            session_id = None
            if bearer:
                claims = _decode_jwt_payload(bearer)
                if claims:
                    username = claims.get("preferred_username")
                    session_id = claims.get("session_state") or claims.get("sid")
            return {
                "type": "user",
                "id": principal.sub or "",
                "name": principal.name,
                "username": username,
                "roles": roles,
                "ip": ip,
                "session_id": session_id,
            }

        if response.status_code == 403 and bearer:
            # AuthMiddleware confirmed signature validity before raising.
            # We can trust the decoded claims.
            claims = _decode_jwt_payload(bearer)
            if claims:
                roles = []
                if self._client_id:
                    roles = list(
                        claims.get("resource_access", {})
                        .get(self._client_id, {})
                        .get("roles", [])
                    )
                return {
                    "type": "user",
                    "id": claims.get("sub") or "unknown",
                    "name": claims.get("name"),
                    "username": claims.get("preferred_username"),
                    "roles": roles,
                    "ip": ip,
                    "session_id": claims.get("session_state") or claims.get("sid"),
                }

        # Anonymous fallback — token absent, malformed, or unverified.
        return {
            "type": "anonymous",
            "id": "anonymous",
            "ip": ip,
        }

    # ---------- event construction ----------

    def _build_event(self, request: Request, response, actor: dict, route) -> dict:
        # Endpoint function name → CloudEvents `type` and `action` derivation.
        func_name = "unknown"
        if route is not None and getattr(route, "endpoint", None) is not None:
            func_name = route.endpoint.__name__

        # First word of the function name as the action verb (best effort).
        action = func_name.split("_", 1)[0] if "_" in func_name else func_name

        return {
            "specversion": "1.0",
            "id": str(uuid4()),
            "source": self._source,
            "type": f"org.openg2p.staff_portal.{func_name}",
            "time": _now_iso(),
            "datacontenttype": "application/json",
            "data": {
                "actor": actor,
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

    # ---------- emission ----------

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
