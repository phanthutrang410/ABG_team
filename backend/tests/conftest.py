"""Pytest fixtures — default session Principal for authenticated API routes (H39)."""

from __future__ import annotations

import pytest

from app.auth.principal import get_principal
from app.main import app
from tests.auth_helpers import DEFAULT_BAN_QUAN_LY


@pytest.fixture(autouse=True)
def _default_session_principal():
    """Most API tests assume an authenticated ban_quan_ly session.

    Auth-negative tests and modules that manage overrides themselves should
    clear or replace ``app.dependency_overrides[get_principal]``.
    """
    app.dependency_overrides[get_principal] = lambda: DEFAULT_BAN_QUAN_LY
    yield
    app.dependency_overrides.pop(get_principal, None)
