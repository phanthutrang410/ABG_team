"""H39 — production identity from cookie session (DB-backed RBAC).

Identity source of truth: HttpOnly cookie ``ss_session`` → hashed token →
``app.auth_session`` + ``app.auth_account``. Client-declared role/scope is
never trusted. Canonical human roles: ``ban_quan_ly`` | ``gvcn``.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, List, Optional

from fastapi import Cookie, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.auth.models import AccessAuditEventRow, AuthAccount, AuthSession
from app.auth.session_tokens import hash_session_token
from app.config import Settings, get_settings
from app.database import get_db

VALID_ROLES = frozenset({"ban_quan_ly", "gvcn"})

SESSION_COOKIE = "ss_session"
SESSION_TTL_SECONDS = 8 * 60 * 60

_LOCAL_COOKIE_ENVS = frozenset({"local", "dev", "development", "test"})


@dataclass(frozen=True)
class Principal:
    """Server-resolved identity for the current request. Never client-built."""

    actor_id: str
    active_role: Optional[str]
    org_scope: str
    advisor_scope: Optional[str] = None
    roles: tuple[str, ...] = ()
    display_name: str = ""
    session_id: Optional[str] = None


@dataclass(frozen=True)
class AccessAuditEvent:
    """Minimal, PII-free access-audit record (in-memory mirror + DB row)."""

    actor_id: str
    role: str
    action: str
    resource_handle: str
    at: datetime
    decision: str = "allowed"


_ACCESS_AUDIT_LOG: List[AccessAuditEvent] = []


def cookie_secure(settings: Optional[Settings] = None) -> bool:
    cfg = settings or get_settings()
    return cfg.app_env.strip().lower() not in _LOCAL_COOKIE_ENVS


def record_access_event(
    *,
    actor_id: str,
    role: str,
    action: str,
    resource_handle: str,
    decision: str = "allowed",
    db: Optional[Session] = None,
) -> AccessAuditEvent:
    """Append audit record. Callers must pass opaque handles only.

    When ``db`` is provided, also persist to ``app.access_audit_event``.
    Persistence is best-effort: if the table is missing (pre-migration local
    DB), the in-memory mirror still records the event and the request continues.
    """
    if decision not in ("allowed", "denied"):
        raise ValueError("decision must be allowed|denied")
    now = datetime.now(timezone.utc)
    event = AccessAuditEvent(
        actor_id=actor_id,
        role=role or "",
        action=action,
        resource_handle=resource_handle,
        at=now,
        decision=decision,
    )
    _ACCESS_AUDIT_LOG.append(event)
    if db is not None:
        try:
            db.add(
                AccessAuditEventRow(
                    actor_id=actor_id,
                    role=role or "",
                    action=action,
                    resource_handle=resource_handle,
                    decision=decision,
                    at=now,
                )
            )
            db.commit()
        except Exception:
            db.rollback()
    return event


def get_access_audit_log() -> List[AccessAuditEvent]:
    """Read-only snapshot of in-process access events (tests + process mirror)."""
    return list(_ACCESS_AUDIT_LOG)


def clear_access_audit_log() -> None:
    """Test-only helper to reset the in-memory audit log between tests."""
    _ACCESS_AUDIT_LOG.clear()


def _load_session(db: Session, raw_token: str) -> Optional[AuthSession]:
    token_hash = hash_session_token(raw_token)
    return (
        db.query(AuthSession)
        .options(joinedload(AuthSession.account).joinedload(AuthAccount.roles))
        .filter(AuthSession.token_hash == token_hash)
        .one_or_none()
    )


def principal_from_session(session_row: AuthSession) -> Principal:
    account = session_row.account
    role_codes = tuple(sorted(r.role for r in account.roles))
    return Principal(
        actor_id=account.actor_id,
        active_role=session_row.active_role,
        org_scope=account.org_scope,
        advisor_scope=account.advisor_scope,
        roles=role_codes,
        display_name=account.display_name,
        session_id=session_row.session_id,
    )


def get_principal(
    ss_session: Optional[str] = Cookie(default=None, alias=SESSION_COOKIE),
    db: Session = Depends(get_db),
) -> Principal:
    """Resolve Principal from ``ss_session`` cookie. Fail closed when missing/invalid."""
    token = (ss_session or "").strip()
    if not token:
        raise HTTPException(
            status_code=401,
            detail={"code": "missing_identity", "message": "session cookie required"},
        )

    row = _load_session(db, token)
    if row is None:
        raise HTTPException(
            status_code=401,
            detail={"code": "invalid_session", "message": "session not found"},
        )

    now = datetime.now(timezone.utc)
    expires = row.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if row.revoked_at is not None or expires <= now:
        raise HTTPException(
            status_code=401,
            detail={"code": "session_expired", "message": "session expired or revoked"},
        )

    account = row.account
    if not account.is_active:
        raise HTTPException(
            status_code=403,
            detail={"code": "account_disabled", "message": "account is disabled"},
        )

    active = row.active_role
    if active is not None and active not in VALID_ROLES:
        raise HTTPException(
            status_code=403,
            detail={"code": "unknown_role", "message": "unrecognized active_role"},
        )

    if active == "gvcn" and not (account.advisor_scope or "").strip():
        raise HTTPException(
            status_code=403,
            detail={
                "code": "missing_advisor_scope",
                "message": "gvcn role requires advisor_scope on account",
            },
        )

    return principal_from_session(row)


def require_active_role(principal: Principal = Depends(get_principal)) -> Principal:
    """Deny when multi-role session has not selected an active role."""
    if not principal.active_role:
        raise HTTPException(
            status_code=403,
            detail={
                "code": "active_role_required",
                "message": "select an active role before continuing",
            },
        )
    if principal.active_role not in VALID_ROLES:
        raise HTTPException(
            status_code=403,
            detail={"code": "unknown_role", "message": "unrecognized active_role"},
        )
    return principal


def require_roles(*roles: str) -> Callable[..., Principal]:
    """Dependency factory: deny-by-default unless ``principal.active_role in roles``."""
    allowed = frozenset(r.strip().lower() for r in roles)

    def _dependency(principal: Principal = Depends(require_active_role)) -> Principal:
        assert principal.active_role is not None
        if principal.active_role not in allowed:
            raise HTTPException(
                status_code=403,
                detail={"code": "role_not_permitted", "message": "role not permitted"},
            )
        return principal

    return _dependency
