"""Shared auth/RBAC test helpers (H39)."""

from __future__ import annotations

from typing import Iterator, Optional

import pytest

from app.auth.principal import Principal, get_principal
from app.main import app

DEFAULT_BAN_QUAN_LY = Principal(
    actor_id="acct:quanly",
    active_role="ban_quan_ly",
    org_scope="org-demo",
    advisor_scope=None,
    roles=("ban_quan_ly",),
    display_name="Test Ban QL",
)

DEFAULT_GVCN = Principal(
    actor_id="acct:gvcn",
    active_role="gvcn",
    org_scope="org-demo",
    advisor_scope="a-240eb01d2805",
    roles=("gvcn",),
    display_name="Test GVCN",
)


@pytest.fixture
def as_principal() -> Iterator:
    """Override ``get_principal`` for the duration of a test."""

    def _set(principal: Principal) -> Principal:
        app.dependency_overrides[get_principal] = lambda: principal
        return principal

    yield _set
    app.dependency_overrides.pop(get_principal, None)


@pytest.fixture
def auth_ban_quan_ly(as_principal) -> Principal:
    return as_principal(DEFAULT_BAN_QUAN_LY)


@pytest.fixture
def auth_gvcn(as_principal) -> Principal:
    return as_principal(DEFAULT_GVCN)


def principal(
    *,
    actor_id: str = "acct:test",
    active_role: Optional[str] = "ban_quan_ly",
    org_scope: str = "org-demo",
    advisor_scope: Optional[str] = None,
    roles: Optional[tuple[str, ...]] = None,
    display_name: str = "Test",
) -> Principal:
    role_tuple = roles
    if role_tuple is None:
        role_tuple = (active_role,) if active_role else ()
    return Principal(
        actor_id=actor_id,
        active_role=active_role,
        org_scope=org_scope,
        advisor_scope=advisor_scope,
        roles=role_tuple,
        display_name=display_name,
    )
