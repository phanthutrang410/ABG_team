"""H36 — production identity/RBAC/access-audit foundation.

Interim identity source: trusted headers set by an upstream gateway/session
layer (``X-SS-Actor-Id`` / ``X-SS-Role`` / ``X-SS-Org-Scope`` /
``X-SS-Advisor-Scope``). Client-declared role is never treated as the source
of truth — outside local/dev/test convenience defaults, every header is
required and validated server-side before a :class:`Principal` is built.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, List, Optional

from fastapi import Depends, Header, HTTPException

from app.config import Settings, get_settings

VALID_ROLES = frozenset({"leader", "advisor", "admin"})

# Convenience-only envs where a missing header set falls back to a fixed demo
# identity. Any other env (including "demo"/"live"/"production") is treated
# as production for identity purposes and requires real trusted headers.
_LOCAL_DEFAULT_ENVS = frozenset({"local", "dev", "development", "test"})

_DEFAULT_ACTOR_ID = "leader:demo"
_DEFAULT_ROLE = "leader"
_DEFAULT_ORG_SCOPE = "org-demo"


@dataclass(frozen=True)
class Principal:
    """Server-resolved identity for the current request. Never client-built."""

    actor_id: str
    active_role: str
    org_scope: str
    advisor_scope: Optional[str] = None


@dataclass(frozen=True)
class AccessAuditEvent:
    """Minimal, PII-free access-audit record."""

    actor_id: str
    role: str
    action: str
    resource_handle: str
    at: datetime


_ACCESS_AUDIT_LOG: List[AccessAuditEvent] = []


def record_access_event(
    *, actor_id: str, role: str, action: str, resource_handle: str
) -> AccessAuditEvent:
    """Append an in-memory audit record.

    Callers must pass opaque handles (e.g. case/report IDs) — never raw
    student names, contact info, or free-text prompts.
    """
    event = AccessAuditEvent(
        actor_id=actor_id,
        role=role,
        action=action,
        resource_handle=resource_handle,
        at=datetime.now(timezone.utc),
    )
    _ACCESS_AUDIT_LOG.append(event)
    return event


def get_access_audit_log() -> List[AccessAuditEvent]:
    """Read-only snapshot of recorded access events."""
    return list(_ACCESS_AUDIT_LOG)


def clear_access_audit_log() -> None:
    """Test-only helper to reset the in-memory audit log between tests."""
    _ACCESS_AUDIT_LOG.clear()


def _is_local_default_env(settings: Settings) -> bool:
    return settings.app_env.strip().lower() in _LOCAL_DEFAULT_ENVS


def get_principal(
    x_ss_actor_id: Optional[str] = Header(default=None, alias="X-SS-Actor-Id"),
    x_ss_role: Optional[str] = Header(default=None, alias="X-SS-Role"),
    x_ss_org_scope: Optional[str] = Header(default=None, alias="X-SS-Org-Scope"),
    x_ss_advisor_scope: Optional[str] = Header(default=None, alias="X-SS-Advisor-Scope"),
    settings: Settings = Depends(get_settings),
) -> Principal:
    """FastAPI dependency resolving the trusted :class:`Principal` for a request.

    Local/dev/test with no headers at all get a fixed demo identity so
    existing demo routes keep working. Every other case — including a
    partially-filled header set in any env, or any header set at all in
    production/live/demo — is validated in full and fails closed.
    """
    actor_id = (x_ss_actor_id or "").strip()
    role = (x_ss_role or "").strip().lower()
    org_scope = (x_ss_org_scope or "").strip()
    advisor_scope = (x_ss_advisor_scope or "").strip() or None

    headers_present = bool(actor_id or role or org_scope or advisor_scope)

    if not headers_present and _is_local_default_env(settings):
        return Principal(
            actor_id=_DEFAULT_ACTOR_ID,
            active_role=_DEFAULT_ROLE,
            org_scope=_DEFAULT_ORG_SCOPE,
            advisor_scope=None,
        )

    if not actor_id or not role or not org_scope:
        raise HTTPException(
            status_code=401,
            detail={
                "code": "missing_identity",
                "message": (
                    "X-SS-Actor-Id, X-SS-Role and X-SS-Org-Scope are required"
                ),
            },
        )

    if role not in VALID_ROLES:
        raise HTTPException(
            status_code=403,
            detail={"code": "unknown_role", "message": "unrecognized X-SS-Role"},
        )

    if role == "advisor" and not advisor_scope:
        raise HTTPException(
            status_code=403,
            detail={
                "code": "missing_advisor_scope",
                "message": "advisor role requires X-SS-Advisor-Scope",
            },
        )

    return Principal(
        actor_id=actor_id,
        active_role=role,
        org_scope=org_scope,
        advisor_scope=advisor_scope,
    )


def require_roles(*roles: str) -> Callable[[Principal], Principal]:
    """Dependency factory: deny-by-default unless ``principal.active_role in roles``."""
    allowed = frozenset(r.strip().lower() for r in roles)

    def _dependency(principal: Principal = Depends(get_principal)) -> Principal:
        if principal.active_role not in allowed:
            raise HTTPException(
                status_code=403,
                detail={"code": "role_not_permitted", "message": "role not permitted"},
            )
        return principal

    return _dependency
