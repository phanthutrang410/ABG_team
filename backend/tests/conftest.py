"""Pytest fixtures — default session Principal for authenticated API routes (H39)."""

from __future__ import annotations

import pytest

from app.auth.principal import get_principal
from app.cases.store import reset_case_store_backend_for_tests
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


@pytest.fixture(autouse=True)
def _in_memory_case_store(monkeypatch: pytest.MonkeyPatch):
    """Keep Process §4 CaseStore in-memory for unit tests (D460-08).

    Persistence coverage lives in ``test_care_case_persist.py`` which opts into
    Postgres explicitly.
    """
    monkeypatch.setenv("CASES_STORE_BACKEND", "memory")
    reset_case_store_backend_for_tests()
    yield
    reset_case_store_backend_for_tests()
