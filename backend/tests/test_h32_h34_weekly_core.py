"""H32/H33a/H33b/H34a/H34b — weekly core modules (Mode B only, Decision #23)."""

from __future__ import annotations

import dataclasses
import os
import uuid
from datetime import datetime, timezone
from urllib.parse import urlparse, urlunparse

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.contracts.integration import assert_no_forbidden_keys
from app.dwh.importer import ATTENDANCE_SOURCE_ID, import_attendance
from app.dwh.migrate import upgrade_head
from app.dwh.models import DatasetSnapshot, DatasetSource
from app.weekly import briefing as briefing_mod
from app.weekly.briefing import BriefingStore, get_or_create_briefing, mark_ack, mark_shown
from app.weekly.cases_durable import CaseRepository, DurableCaseError
from app.weekly.delta import RunVersions, TerminalFingerprint, compute_delta, reconcile
from app.weekly.observations import (
    NamespaceMismatchError,
    SignalObservation,
    build_observations_mode_b,
    evidence_fingerprint,
)
from app.weekly.report import materialize_report

_EXTRACTED = datetime(2026, 7, 13, tzinfo=timezone.utc)


# --------------------------------------------------------------------------
# H32 — Mode B observations (real Postgres + real read_adapter/scoring)
# --------------------------------------------------------------------------


def _postgres_available(url: str) -> bool:
    try:
        engine = create_engine(url, pool_pre_ping=True)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        engine.dispose()
        return True
    except Exception:
        return False


def _admin_url(database_url: str) -> str:
    parsed = urlparse(database_url)
    return urlunparse(parsed._replace(path="/postgres"))


@pytest.fixture(scope="module")
def weekly_database_url() -> str:
    base_url = os.environ.get("TEST_DATABASE_URL") or get_settings().database_url
    if not _postgres_available(base_url):
        pytest.fail("Postgres required for H32 tests")

    test_name = f"ss_h32_{uuid.uuid4().hex[:10]}"
    admin = create_engine(_admin_url(base_url), isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        conn.execute(text(f'CREATE DATABASE "{test_name}"'))
    admin.dispose()

    parsed = urlparse(base_url)
    test_url = urlunparse(parsed._replace(path=f"/{test_name}"))
    upgrade_head(test_url)
    import_attendance(test_url, ensure_schema=False)
    yield test_url

    admin = create_engine(_admin_url(base_url), isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        conn.execute(
            text(
                "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                "WHERE datname = :name AND pid <> pg_backend_pid()"
            ),
            {"name": test_name},
        )
        conn.execute(text(f'DROP DATABASE IF EXISTS "{test_name}"'))
    admin.dispose()


def _session(url: str):
    return sessionmaker(bind=create_engine(url), autoflush=False, autocommit=False)()


def _add_snapshot(
    session,
    *,
    snapshot_id: str,
    dataset_key: str,
    legacy_source_id: str | None,
) -> None:
    if session.get(DatasetSource, dataset_key) is None:
        session.add(DatasetSource(dataset_key=dataset_key, source_owner="test"))
        session.flush()
    session.add(
        DatasetSnapshot(
            snapshot_id=snapshot_id,
            dataset_key=dataset_key,
            extracted_at=_EXTRACTED,
            schema_version="weekly-snapshot-v2",
            pseudonym_namespace_version="approval:pending-linked-namespace",
            source_snapshot_sha256="a" * 64,
            dataset_content_sha256="a" * 64,
            approval_id="approval:test-h32",
            provenance_approved=True,
            legacy_source_id=legacy_source_id,
            status="active",
        )
    )
    session.commit()


def test_mode_b_rejects_combined_branch(weekly_database_url: str) -> None:
    with _session(weekly_database_url) as session:
        with pytest.raises(ValueError, match="linked_namespace_pending"):
            build_observations_mode_b(session, "snap-any", "combined")


def test_mode_b_builds_real_observations_from_attendance_branch(
    weekly_database_url: str,
) -> None:
    with _session(weekly_database_url) as session:
        _add_snapshot(
            session,
            snapshot_id="snap-att-1",
            dataset_key="epu-care-signals-att-1",
            legacy_source_id=ATTENDANCE_SOURCE_ID,
        )
        observations = build_observations_mode_b(session, "snap-att-1", "attendance")

    assert len(observations) == 3
    for obs in observations:
        assert obs.snapshot_id == "snap-att-1"
        assert obs.branch == "attendance"
        assert obs.extracted_at == _EXTRACTED
        assert obs.coverage_status in ("ok", "partial", "insufficient")
        if obs.coverage_status == "insufficient":
            assert obs.review_priority_band is None
            assert obs.factor_codes == []
        assert len(obs.evidence_fingerprint) == 64
        blob = dataclasses.asdict(obs)
        assert_no_forbidden_keys(blob)
        for forbidden in ("model_score", "full_name", "email", "mssv"):
            assert forbidden not in blob


def test_mode_b_observations_are_deterministic(weekly_database_url: str) -> None:
    with _session(weekly_database_url) as session:
        _add_snapshot(
            session,
            snapshot_id="snap-att-det",
            dataset_key="epu-care-signals-att-det",
            legacy_source_id=ATTENDANCE_SOURCE_ID,
        )
        first = build_observations_mode_b(session, "snap-att-det", "attendance")
        second = build_observations_mode_b(session, "snap-att-det", "attendance")

    first_by_ref = {o.student_ref: o for o in first}
    second_by_ref = {o.student_ref: o for o in second}
    assert set(first_by_ref) == set(second_by_ref)
    for ref, obs in first_by_ref.items():
        assert obs.evidence_fingerprint == second_by_ref[ref].evidence_fingerprint
        assert obs.review_priority_band == second_by_ref[ref].review_priority_band


def test_mode_b_namespace_mismatch_fails(weekly_database_url: str) -> None:
    with _session(weekly_database_url) as session:
        _add_snapshot(
            session,
            snapshot_id="snap-mismatch",
            dataset_key="epu-care-signals-mismatch",
            legacy_source_id=ATTENDANCE_SOURCE_ID,
        )
        with pytest.raises(NamespaceMismatchError):
            build_observations_mode_b(session, "snap-mismatch", "semester")


def test_mode_b_dataset_key_fallback_resolves_source(weekly_database_url: str) -> None:
    with _session(weekly_database_url) as session:
        _add_snapshot(
            session,
            snapshot_id="snap-fallback",
            dataset_key=ATTENDANCE_SOURCE_ID,
            legacy_source_id=None,
        )
        observations = build_observations_mode_b(session, "snap-fallback", "attendance")
    assert len(observations) == 3


def test_mode_b_unknown_branch_raises(weekly_database_url: str) -> None:
    with _session(weekly_database_url) as session:
        with pytest.raises(ValueError):
            build_observations_mode_b(session, "snap-any", "wellbeing")


def test_mode_b_missing_snapshot_raises(weekly_database_url: str) -> None:
    with _session(weekly_database_url) as session:
        with pytest.raises(ValueError, match="snapshot_not_found"):
            build_observations_mode_b(session, "does-not-exist", "attendance")


# --------------------------------------------------------------------------
# Pure-python fixtures shared by H33b/H34a/H34b tests (no DB needed)
# --------------------------------------------------------------------------

_V1 = RunVersions(
    model_version="m02-baseline-0.1",
    threshold_config_version="thr-epu-0.1-uncalibrated",
    pseudonym_namespace_version="approval:pending-linked-namespace",
)
_V2 = RunVersions(
    model_version="m02-baseline-0.2",
    threshold_config_version="thr-epu-0.1-uncalibrated",
    pseudonym_namespace_version="approval:pending-linked-namespace",
)


def _obs(
    student_ref: str,
    branch: str,
    band: str | None,
    factors: list[str],
    *,
    coverage: str = "ok",
    snapshot_id: str = "snap-1",
) -> SignalObservation:
    return SignalObservation(
        snapshot_id=snapshot_id,
        student_ref=student_ref,
        branch=branch,
        review_priority_band=band,
        factor_codes=list(factors),
        coverage_status=coverage,
        extracted_at=_EXTRACTED,
        evidence_fingerprint=evidence_fingerprint(
            student_ref=student_ref,
            branch=branch,
            review_priority_band=band,
            factor_codes=factors,
            coverage_status=coverage,
        ),
        model_version=_V1.model_version,
    )


# --------------------------------------------------------------------------
# H33b — delta matrix
# --------------------------------------------------------------------------


def test_delta_initial_baseline_when_no_prior_versions() -> None:
    curr = [_obs("s-1", "semester", "can_ra_soat", ["grade_trend_declining"])]
    deltas = compute_delta([], curr, prev_versions=None, curr_versions=_V1)
    assert len(deltas) == 1
    assert deltas[0].delta_type == "initial_baseline"
    # Not eligible current rows are not claimed as baseline "signals".
    curr_insufficient = [_obs("s-2", "semester", None, [], coverage="insufficient")]
    deltas2 = compute_delta([], curr_insufficient, prev_versions=None, curr_versions=_V1)
    assert deltas2 == []


def test_delta_newly_detected_ongoing_changed_no_longer() -> None:
    prev = [
        _obs("s-ongoing", "semester", "can_ra_soat", ["grade_trend_declining"], snapshot_id="snap-0"),
        _obs("s-changed", "semester", "can_ra_soat", ["grade_trend_declining"], snapshot_id="snap-0"),
        _obs("s-gone", "semester", "can_ra_soat", ["grade_trend_declining"], snapshot_id="snap-0"),
    ]
    curr = [
        _obs("s-ongoing", "semester", "can_ra_soat", ["grade_trend_declining"], snapshot_id="snap-1"),
        _obs("s-changed", "semester", "uu_tien_som", ["grade_trend_declining", "grade_volatility_elevated"], snapshot_id="snap-1"),
        _obs("s-gone", "semester", None, [], coverage="insufficient", snapshot_id="snap-1"),
        _obs("s-new", "semester", "can_ra_soat", ["attendance_rate_below_target"], snapshot_id="snap-1"),
    ]
    deltas = compute_delta(prev, curr, prev_versions=_V1, curr_versions=_V1)
    by_ref = {d.student_ref: d for d in deltas}

    assert by_ref["s-ongoing"].delta_type == "ongoing"
    assert by_ref["s-ongoing"].significant_change is False

    assert by_ref["s-changed"].delta_type == "changed"
    assert by_ref["s-changed"].significant_change is True

    assert by_ref["s-gone"].delta_type == "no_longer_detected"

    assert by_ref["s-new"].delta_type == "newly_detected"
    assert by_ref["s-new"].significant_change is True


def test_delta_resurfaced_significant_vs_not() -> None:
    curr_significant = [_obs("s-r1", "semester", "uu_tien_som", ["grade_trend_declining"], snapshot_id="snap-2")]
    terminal = {
        ("s-r1", "semester"): TerminalFingerprint(
            review_priority_band="can_ra_soat", factor_codes=("grade_trend_declining",)
        ),
        ("s-r2", "semester"): TerminalFingerprint(
            review_priority_band="can_ra_soat", factor_codes=("grade_trend_declining",)
        ),
    }
    curr_not_significant = curr_significant + [
        _obs("s-r2", "semester", "can_ra_soat", ["grade_trend_declining"], snapshot_id="snap-2")
    ]
    deltas = compute_delta(
        [], curr_not_significant, prev_versions=_V1, curr_versions=_V1, prior_terminal_fingerprints=terminal
    )
    by_ref = {d.student_ref: d for d in deltas}
    assert by_ref["s-r1"].delta_type == "resurfaced"
    assert by_ref["s-r1"].significant_change is True
    assert by_ref["s-r2"].delta_type == "resurfaced"
    assert by_ref["s-r2"].significant_change is False


def test_delta_comparison_unavailable_on_version_change() -> None:
    prev = [_obs("s-1", "semester", "can_ra_soat", ["grade_trend_declining"], snapshot_id="snap-0")]
    curr = [_obs("s-1", "semester", "can_ra_soat", ["grade_trend_declining"], snapshot_id="snap-1")]
    deltas = compute_delta(prev, curr, prev_versions=_V1, curr_versions=_V2)
    assert len(deltas) == 1
    assert deltas[0].delta_type == "comparison_unavailable"
    assert "version_changed" in deltas[0].reason_codes
    # Never claim "mới" across an incompatible model/threshold/namespace change.
    assert deltas[0].delta_type != "newly_detected"


# --------------------------------------------------------------------------
# H33a/H33b — durable case repository + reconcile
# --------------------------------------------------------------------------


def test_one_active_episode_per_student_branch() -> None:
    repo = CaseRepository()
    repo.create_episode("s-1", "semester")
    with pytest.raises(DurableCaseError):
        repo.create_episode("s-1", "semester")


def test_get_helpers_never_create_or_mutate() -> None:
    repo = CaseRepository()
    assert repo.get("ep-missing") is None
    assert repo.list_active() == []
    assert repo.get_active_for("s-1", "semester") is None
    assert repo.list_all() == []


def test_transition_rejects_agent_actor() -> None:
    repo = CaseRepository()
    episode = repo.create_episode("s-1", "semester")
    with pytest.raises(DurableCaseError) as exc:
        repo.transition(episode.episode_id, "approve", actor="bot", actor_kind="agent")
    assert exc.value.code == "agent_forbidden"


def test_assign_missing_advisor_ref_queues_mapping_repair() -> None:
    repo = CaseRepository()
    episode = repo.create_episode("s-1", "semester")
    repo.transition(episode.episode_id, "approve", actor="leader:demo")
    with pytest.raises(DurableCaseError) as exc:
        repo.transition(episode.episode_id, "assign", actor="leader:demo")
    assert exc.value.code == "missing_advisor_ref"
    assert exc.value.mapping_repair_queued is True
    refreshed = repo.get(episode.episode_id)
    assert refreshed.state == "approved"
    assert refreshed.mapping_repair_queued is True


def test_reconcile_creates_episode_on_newly_detected_and_initial_baseline() -> None:
    repo = CaseRepository()
    deltas = compute_delta(
        [], [_obs("s-1", "semester", "can_ra_soat", ["grade_trend_declining"])], prev_versions=None, curr_versions=_V1
    )
    reconcile(repo, deltas)
    episode = repo.get_active_for("s-1", "semester")
    assert episode is not None
    assert episode.state == "pending_review"


def test_reconcile_preserves_approved_state_and_no_auto_close() -> None:
    repo = CaseRepository()
    baseline = compute_delta(
        [], [_obs("s-1", "semester", "can_ra_soat", ["grade_trend_declining"], snapshot_id="snap-0")],
        prev_versions=None,
        curr_versions=_V1,
    )
    reconcile(repo, baseline)
    episode = repo.get_active_for("s-1", "semester")
    repo.transition(episode.episode_id, "approve", actor="leader:demo")

    prev = [_obs("s-1", "semester", "can_ra_soat", ["grade_trend_declining"], snapshot_id="snap-0")]
    curr_gone = [_obs("s-1", "semester", None, [], coverage="insufficient", snapshot_id="snap-1")]
    deltas = compute_delta(prev, curr_gone, prev_versions=_V1, curr_versions=_V1)
    assert deltas[0].delta_type == "no_longer_detected"
    reconcile(repo, deltas)

    refreshed = repo.get(episode.episode_id)
    assert refreshed.state == "approved"
    assert refreshed.active is True
    assert any(e.kind == "observation_no_longer_detected" for e in refreshed.events)


def test_reconcile_duplicate_run_produces_no_extra_event() -> None:
    repo = CaseRepository()
    deltas = compute_delta(
        [], [_obs("s-1", "semester", "can_ra_soat", ["grade_trend_declining"], snapshot_id="snap-0")],
        prev_versions=None,
        curr_versions=_V1,
    )
    reconcile(repo, deltas)
    episode = repo.get_active_for("s-1", "semester")
    n_events_first = len(episode.events)
    reconcile(repo, deltas)  # exact same deltas replayed
    refreshed = repo.get(episode.episode_id)
    assert len(refreshed.events) == n_events_first


def test_reconcile_resurfaced_opens_episode_only_if_significant() -> None:
    repo = CaseRepository()
    baseline = compute_delta(
        [], [_obs("s-1", "semester", "can_ra_soat", ["grade_trend_declining"], snapshot_id="snap-0")],
        prev_versions=None,
        curr_versions=_V1,
    )
    reconcile(repo, baseline)
    episode = repo.get_active_for("s-1", "semester")
    repo.transition(episode.episode_id, "dismiss", actor="leader:demo", reason_code="resolved_offline")
    assert repo.get_active_for("s-1", "semester") is None  # terminal -> no longer active

    terminal = {
        ("s-1", "semester"): TerminalFingerprint(
            review_priority_band="can_ra_soat", factor_codes=("grade_trend_declining",)
        )
    }
    not_significant_curr = [_obs("s-1", "semester", "can_ra_soat", ["grade_trend_declining"], snapshot_id="snap-1")]
    deltas_ns = compute_delta(
        [], not_significant_curr, prev_versions=_V1, curr_versions=_V1, prior_terminal_fingerprints=terminal
    )
    reconcile(repo, deltas_ns)
    assert repo.get_active_for("s-1", "semester") is None  # no significant change -> no new episode

    significant_curr = [_obs("s-1", "semester", "uu_tien_som", ["grade_trend_declining"], snapshot_id="snap-2")]
    deltas_sig = compute_delta(
        [], significant_curr, prev_versions=_V1, curr_versions=_V1, prior_terminal_fingerprints=terminal
    )
    reconcile(repo, deltas_sig)
    new_episode = repo.get_active_for("s-1", "semester")
    assert new_episode is not None
    assert new_episode.episode_id != episode.episode_id


# --------------------------------------------------------------------------
# H34a — weekly report
# --------------------------------------------------------------------------


def test_report_aggregates_exact() -> None:
    repo = CaseRepository()
    repo.create_episode("s-1", "semester")
    repo.create_episode("s-2", "semester")
    repo.create_episode("s-3", "attendance")  # different branch — excluded from semester scope

    deltas = compute_delta(
        [
            _obs("s-1", "semester", "can_ra_soat", ["grade_trend_declining"], snapshot_id="snap-0"),
            _obs("s-2", "semester", "can_ra_soat", ["grade_trend_declining"], snapshot_id="snap-0"),
        ],
        [
            _obs("s-1", "semester", "can_ra_soat", ["grade_trend_declining"], snapshot_id="snap-1"),
            _obs("s-2", "semester", "uu_tien_som", ["grade_trend_declining", "grade_volatility_elevated"], snapshot_id="snap-1"),
            _obs("s-new", "semester", "can_ra_soat", ["attendance_rate_below_target"], snapshot_id="snap-1"),
        ],
        prev_versions=_V1,
        curr_versions=_V1,
    )
    report = materialize_report(repo, deltas, "snap-1", "semester")
    assert report.status == "ok"
    assert report.aggregates == {"new": 1, "ongoing": 1, "changed": 1, "total_active": 2}
    assert "student_ref" not in dataclasses.asdict(report)


def test_report_empty_baseline_failed_and_stale_states() -> None:
    repo = CaseRepository()
    empty = materialize_report(repo, [], "snap-x", "semester")
    assert empty.status == "empty"
    assert empty.aggregates["total_active"] == 0

    baseline_deltas = compute_delta(
        [], [_obs("s-1", "semester", "can_ra_soat", ["grade_trend_declining"])], prev_versions=None, curr_versions=_V1
    )
    baseline_report = materialize_report(repo, baseline_deltas, "snap-1", "semester")
    assert baseline_report.status == "baseline_unavailable"

    failed_report = materialize_report(
        repo, baseline_deltas, "snap-1", "semester", workflow_failure_reason="scoring_step_failed"
    )
    assert failed_report.status == "failed"
    assert failed_report.aggregates == {"new": 0, "ongoing": 0, "changed": 0, "total_active": 0}

    ongoing_deltas = compute_delta(
        [_obs("s-1", "semester", "can_ra_soat", ["grade_trend_declining"], snapshot_id="snap-1")],
        [_obs("s-1", "semester", "can_ra_soat", ["grade_trend_declining"], snapshot_id="snap-2")],
        prev_versions=_V1,
        curr_versions=_V1,
    )
    stale_report = materialize_report(repo, ongoing_deltas, "snap-2", "semester", stale=True)
    assert stale_report.status == "stale"
    assert "stale_snapshot" in stale_report.limitations


# --------------------------------------------------------------------------
# H34b — briefing + receipts
# --------------------------------------------------------------------------


def test_briefing_deterministic_role_scoped_and_reused() -> None:
    repo = CaseRepository()
    deltas = compute_delta(
        [], [_obs("s-1", "semester", "can_ra_soat", ["grade_trend_declining"])], prev_versions=None, curr_versions=_V1
    )
    report = materialize_report(repo, deltas, "snap-1", "semester")
    store = BriefingStore()

    leader = get_or_create_briefing(store, report, "leader")
    advisor = get_or_create_briefing(store, report, "advisor")
    assert leader.message_vi != advisor.message_vi
    assert {c.key for c in leader.action_cards} != {c.key for c in advisor.action_cards}
    assert any(c.key == "open_advisor_drafts" for c in leader.action_cards)
    assert not any(c.key == "open_advisor_drafts" for c in advisor.action_cards)

    leader_again = get_or_create_briefing(store, report, "leader")
    assert leader_again.briefing_id == leader.briefing_id
    assert leader_again is leader


def test_briefing_shown_and_ack_are_one_time() -> None:
    store = BriefingStore()
    report = materialize_report(CaseRepository(), [], "snap-1", "semester")
    briefing = get_or_create_briefing(store, report, "leader")

    receipt1 = mark_shown(store, "user-1", "leader", briefing.briefing_id)
    assert receipt1.shown_at is not None
    first_shown_at = receipt1.shown_at

    receipt2 = mark_shown(store, "user-1", "leader", briefing.briefing_id)
    assert receipt2.shown_at == first_shown_at  # not overwritten on second navigation

    ack1 = mark_ack(store, "user-1", "leader", briefing.briefing_id)
    assert ack1.ack_at is not None
    ack2 = mark_ack(store, "user-1", "leader", briefing.briefing_id)
    assert ack2.ack_at == ack1.ack_at

    # A different role for the same user gets an independent receipt.
    other_role_receipt = store.get_receipt("user-1", "advisor", briefing.briefing_id)
    assert other_role_receipt is None


def test_briefing_is_openai_independent() -> None:
    assert "openai" not in briefing_mod.__dict__
    assert not any("openai" in name.lower() for name in dir(briefing_mod))
    # Building/showing a briefing must not require any provider credentials.
    report = materialize_report(CaseRepository(), [], "snap-1", "semester")
    store = BriefingStore()
    briefing = get_or_create_briefing(store, report, "advisor")
    assert briefing.message_vi


def test_no_pii_forbidden_fields_in_report_and_briefing_public_dicts() -> None:
    repo = CaseRepository()
    deltas = compute_delta(
        [], [_obs("s-1", "semester", "can_ra_soat", ["grade_trend_declining"])], prev_versions=None, curr_versions=_V1
    )
    report = materialize_report(repo, deltas, "snap-1", "semester")
    store = BriefingStore()
    briefing = get_or_create_briefing(store, report, "leader")

    report_dict = dataclasses.asdict(report)
    briefing_dict = dataclasses.asdict(briefing)
    assert_no_forbidden_keys(report_dict)
    assert_no_forbidden_keys(briefing_dict)
    for blob in (report_dict, briefing_dict):
        assert "student_ref" not in blob
        blob_text = str(blob).lower()
        for token in ("mssv", "email", "phone", "full_name", "model_score"):
            assert token not in blob_text
