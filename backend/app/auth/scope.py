"""H39 — case-level scope checks (org/advisor), server-side only.

Callers must never widen scope by trusting client-supplied org/advisor
fields; the checks here only consult the server-resolved ``Principal``.
"""

from __future__ import annotations

from typing import Optional

from app.auth.principal import Principal

#: Care states a ``gvcn`` may see (post-handoff). Pre-handoff is invisible.
GVCN_VISIBLE_STATES = frozenset(
    {
        "assigned",
        "follow_up_in_progress",
        "monitoring",
        "resolved",
    }
)


def can_access_case(
    principal: Principal,
    case_advisor_ref: Optional[str],
    case_org: str,
) -> bool:
    """True when ``principal`` may view/act on a case in ``case_org``.

    - ban_quan_ly: authorized for any case within their own ``org_scope``.
    - gvcn: authorized only when both the org matches and the case's
      ``advisor_ref`` equals their assigned ``advisor_scope``.
    """
    if not principal.active_role:
        return False

    if principal.org_scope != case_org:
        return False

    if principal.active_role == "ban_quan_ly":
        return True

    if principal.active_role == "gvcn":
        return bool(principal.advisor_scope) and principal.advisor_scope == case_advisor_ref

    return False


def gvcn_may_see_case_state(case_state: Optional[str]) -> bool:
    """True when a ``gvcn`` is allowed to see a case in this workflow state."""
    return bool(case_state) and case_state in GVCN_VISIBLE_STATES
