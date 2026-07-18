"""H36 — case-level scope checks (org/advisor), server-side only.

Callers must never widen scope by trusting client-supplied org/advisor
fields; the checks here only consult the server-resolved ``Principal``.
"""

from __future__ import annotations

from typing import Optional

from app.auth.principal import Principal


def can_access_case(
    principal: Principal,
    case_advisor_ref: Optional[str],
    case_org: str,
) -> bool:
    """True when ``principal`` may view/act on a case in ``case_org``.

    - leader/admin: authorized for any case within their own ``org_scope``.
    - advisor: authorized only when both the org matches and the case's
      ``advisor_ref`` equals their assigned ``advisor_scope`` (cross-advisor
      and org-mismatch are both denied; no existence of out-of-scope cases
      is implied by the result).
    """
    if principal.org_scope != case_org:
        return False

    if principal.active_role in ("leader", "admin"):
        return True

    if principal.active_role == "advisor":
        return bool(principal.advisor_scope) and principal.advisor_scope == case_advisor_ref

    return False
