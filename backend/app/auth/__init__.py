"""H36 — production identity/RBAC/scope + access-audit foundation."""

from app.auth.principal import (
    AccessAuditEvent,
    Principal,
    VALID_ROLES,
    clear_access_audit_log,
    get_access_audit_log,
    get_principal,
    record_access_event,
    require_roles,
)
from app.auth.scope import can_access_case

__all__ = [
    "VALID_ROLES",
    "AccessAuditEvent",
    "Principal",
    "can_access_case",
    "clear_access_audit_log",
    "get_access_audit_log",
    "get_principal",
    "record_access_event",
    "require_roles",
]
