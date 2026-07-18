"""H39 — production identity/RBAC/scope + durable access-audit."""

from app.auth.principal import (
    SESSION_COOKIE,
    VALID_ROLES,
    AccessAuditEvent,
    Principal,
    clear_access_audit_log,
    get_access_audit_log,
    get_principal,
    record_access_event,
    require_active_role,
    require_roles,
)
from app.auth.scope import GVCN_VISIBLE_STATES, can_access_case, gvcn_may_see_case_state

__all__ = [
    "GVCN_VISIBLE_STATES",
    "SESSION_COOKIE",
    "VALID_ROLES",
    "AccessAuditEvent",
    "Principal",
    "can_access_case",
    "clear_access_audit_log",
    "get_access_audit_log",
    "get_principal",
    "gvcn_may_see_case_state",
    "record_access_event",
    "require_active_role",
    "require_roles",
]
