"""H38 — safe report export: aggregate CSV (no identifiers) vs one-case CSV."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.auth.principal import Principal, clear_access_audit_log, get_access_audit_log
from app.main import app
from app.weekly import state as weekly_state
from app.weekly.export import (
    ExportError,
    export_aggregate_csv,
    export_case,
    export_case_csv,
    validate_export_kind,
)
from app.weekly.report import materialize_report

_LEADER_A = Principal(
    actor_id="acct:quanly", active_role="ban_quan_ly", org_scope="org-a", roles=("ban_quan_ly",)
)
_ADVISOR_1 = Principal(
    actor_id="acct:gvcn1",
    active_role="gvcn",
    org_scope="org-a",
    advisor_scope="adv-1",
    roles=("gvcn",),
)
_ADVISOR_2 = Principal(
    actor_id="acct:gvcn2",
    active_role="gvcn",
    org_scope="org-a",
    advisor_scope="adv-2",
    roles=("gvcn",),
)


@pytest.fixture(autouse=True)
def _reset_state():
    weekly_state.clear()
    clear_access_audit_log()
    yield
    weekly_state.clear()
    clear_access_audit_log()
    app.dependency_overrides.clear()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


# --- aggregate: no identifiers -----------------------------------------------


def test_aggregate_csv_has_no_student_identifiers() -> None:
    repo = weekly_state.case_repository
    repo.create_episode("s-1", "semester", org_scope="org-a")
    report = materialize_report(repo, [], None, "semester")

    csv_text = export_aggregate_csv(report)
    assert "s-1" not in csv_text
    for token in ("student_ref", "mssv", "email", "phone", "full_name"):
        assert token not in csv_text.lower()
    assert "new" in csv_text and "total_active" in csv_text


def test_aggregate_csv_deterministic_counts() -> None:
    repo = weekly_state.case_repository
    report = materialize_report(repo, [], None, "semester")
    csv_text = export_aggregate_csv(report)
    lines = csv_text.strip().splitlines()
    assert lines[0] == "report_id,branch,status,metric,count"
    assert len(lines) == 5  # header + 4 metrics


# --- per-case: watermark + audit ---------------------------------------------


def test_case_export_includes_watermark_and_records_audit() -> None:
    repo = weekly_state.case_repository
    episode = repo.create_episode("s-1", "semester", org_scope="org-a")
    repo.transition(episode.episode_id, "approve", actor="leader:demo")
    repo.transition(episode.episode_id, "assign", actor="leader:demo", advisor_ref="adv-1")

    result = export_case(repo, episode.episode_id, _LEADER_A)
    assert result.episode_id == episode.episode_id
    assert result.watermark.actor_id == _LEADER_A.actor_id
    assert result.watermark.exported_at is not None

    log = get_access_audit_log()
    assert len(log) == 1
    assert log[0].action == "export_case"
    assert log[0].resource_handle == episode.episode_id


def test_case_export_csv_has_no_email_phone_name() -> None:
    repo = weekly_state.case_repository
    episode = repo.create_episode("s-1", "semester", org_scope="org-a")
    repo.transition(episode.episode_id, "approve", actor="leader:demo")
    repo.transition(episode.episode_id, "assign", actor="leader:demo", advisor_ref="adv-1")

    result = export_case(repo, episode.episode_id, _LEADER_A)
    csv_text = export_case_csv(result)
    for token in ("email", "phone", "full_name", "mssv"):
        assert token not in csv_text.lower()


def test_case_export_not_found_raises() -> None:
    repo = weekly_state.case_repository
    with pytest.raises(ExportError) as exc:
        export_case(repo, "ep-missing", _LEADER_A)
    assert exc.value.code == "not_found"


def test_case_export_cross_scope_denied() -> None:
    repo = weekly_state.case_repository
    episode = repo.create_episode("s-1", "semester", org_scope="org-a")
    repo.transition(episode.episode_id, "approve", actor="leader:demo")
    repo.transition(episode.episode_id, "assign", actor="leader:demo", advisor_ref="adv-1")

    with pytest.raises(ExportError) as exc:
        export_case(repo, episode.episode_id, _ADVISOR_2)
    assert exc.value.code == "forbidden"
    assert get_access_audit_log() == []  # denied access must not be logged as a successful export


def test_advisor_can_export_own_assigned_case() -> None:
    repo = weekly_state.case_repository
    episode = repo.create_episode("s-1", "semester", org_scope="org-a")
    repo.transition(episode.episode_id, "approve", actor="leader:demo")
    repo.transition(episode.episode_id, "assign", actor="leader:demo", advisor_ref="adv-1")

    result = export_case(repo, episode.episode_id, _ADVISOR_1)
    assert result.episode_id == episode.episode_id


# --- reject bulk / missing episode ------------------------------------------


@pytest.mark.parametrize("kind", ["bulk", "all_students", "full_list", "unknown", ""])
def test_invalid_or_bulk_kind_rejected(kind: str) -> None:
    with pytest.raises(ExportError) as exc:
        validate_export_kind(kind, episode_id=None)
    assert exc.value.code == "invalid_kind"


def test_case_kind_missing_episode_id_rejected() -> None:
    with pytest.raises(ExportError) as exc:
        validate_export_kind("case", episode_id=None)
    assert exc.value.code == "missing_episode_id"


def test_aggregate_kind_does_not_require_episode_id() -> None:
    validate_export_kind("aggregate", episode_id=None)  # must not raise


# --- CSV injection escaping ---------------------------------------------------


def test_csv_injection_leading_characters_are_escaped() -> None:
    repo = weekly_state.case_repository
    episode = repo.create_episode("=cmd|' /C calc'!A0", "semester", org_scope="org-a")
    repo.transition(episode.episode_id, "approve", actor="leader:demo")
    repo.transition(episode.episode_id, "assign", actor="leader:demo", advisor_ref="adv-1")

    result = export_case(repo, episode.episode_id, _LEADER_A)
    csv_text = export_case_csv(result)
    assert "\n=cmd" not in csv_text
    assert "'=cmd" in csv_text


# --- HTTP wiring --------------------------------------------------------------


def test_http_export_aggregate_ok(client: TestClient) -> None:
    repo = weekly_state.case_repository
    report = materialize_report(repo, [], None, "semester")
    weekly_state.put_report(report)

    response = client.get(f"/weekly-reports/{report.report_id}/export", params={"kind": "aggregate"})
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "s-" not in response.text


def test_http_export_case_ok(client: TestClient) -> None:
    repo = weekly_state.case_repository
    episode = repo.create_episode("s-1", "semester", org_scope="org-demo")
    repo.transition(episode.episode_id, "approve", actor="leader:demo")
    repo.transition(episode.episode_id, "assign", actor="leader:demo", advisor_ref="adv-1")
    report = materialize_report(repo, [], None, "semester")
    weekly_state.put_report(report)

    response = client.get(
        f"/weekly-reports/{report.report_id}/export",
        params={"kind": "case", "episode_id": episode.episode_id},
    )
    assert response.status_code == 200
    assert episode.episode_id in response.text


def test_http_export_bulk_kind_rejected_400(client: TestClient) -> None:
    response = client.get("/weekly-reports/wr-1/export", params={"kind": "bulk"})
    assert response.status_code == 400


def test_http_export_case_missing_episode_id_rejected_400(client: TestClient) -> None:
    response = client.get("/weekly-reports/wr-1/export", params={"kind": "case"})
    assert response.status_code == 400


def test_http_export_case_cross_scope_denied_403(client: TestClient) -> None:
    repo = weekly_state.case_repository
    episode = repo.create_episode("s-1", "semester", org_scope="org-b")
    repo.transition(episode.episode_id, "approve", actor="leader:demo")
    repo.transition(episode.episode_id, "assign", actor="leader:demo", advisor_ref="adv-1")
    report = materialize_report(repo, [], None, "semester")
    weekly_state.put_report(report)

    response = client.get(
        f"/weekly-reports/{report.report_id}/export",
        params={"kind": "case", "episode_id": episode.episode_id},
    )
    assert response.status_code == 403
