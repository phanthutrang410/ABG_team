"""Track A — ml_term_snapshot materializer (agent-explain-v1 + Postgres)."""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from urllib.parse import urlparse, urlunparse

import pytest
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.contracts.coverage import Coverage, attendance_unapproved_defaults
from app.contracts.normalized import NormalizedStudentRecord, NormalizedTermGrade
from app.contracts.scoring import ScoringFeatures
from app.dwh.importer import SEMESTER_SOURCE_ID, import_semester
from app.dwh.migrate import upgrade_head
from app.dwh.ml_materializer import (
    EXPLAIN_SCHEMA_VERSION,
    build_agent_explain_json,
    evidence_fingerprint,
    materialize_ml_term_snapshot,
)
from app.dwh.models import MlTermSnapshot
from app.ml.scoring import (
    MODEL_VERSION,
    THRESHOLD_CONFIG_VERSION,
    contributing_factors,
    score_student,
)

_CALC_AT = datetime(2026, 7, 18, 12, 0, 0, tzinfo=timezone.utc)


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


@pytest.fixture()
def materialize_database_url() -> str:
    base_url = os.environ.get("TEST_DATABASE_URL") or get_settings().database_url
    if not _postgres_available(base_url):
        pytest.fail(
            "Postgres required for ml materializer tests. "
            "Start `docker compose up -d db` then re-run."
        )
    test_name = f"ss_mlmat_{uuid.uuid4().hex[:10]}"
    admin = create_engine(_admin_url(base_url), isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        conn.execute(text(f'CREATE DATABASE "{test_name}"'))
    admin.dispose()
    parsed = urlparse(base_url)
    test_url = urlunparse(parsed._replace(path=f"/{test_name}"))
    upgrade_head(test_url)
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
    engine = create_engine(url)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)()


def _features_fixture() -> ScoringFeatures:
    coverage = attendance_unapproved_defaults(
        n_valid_terms=2,
        n_courses=2,
        last_term_code="2022-2023-T2",
    )
    return ScoringFeatures(
        dataset_version="v59-empty-program-students:abcd1234:epu-1",
        model_version=MODEL_VERSION,
        threshold_config_version=THRESHOLD_CONFIG_VERSION,
        calculated_at=_CALC_AT,
        student_ref="s-fixture-1",
        latest_term_gpa=3.4567,
        grade_trend_slope=-0.1234567,
        grade_volatility=1.2345678,
        failed_credits=3.0,
        attendance_rate_window=None,
        attendance_trend_slope=None,
        coverage=coverage,
    )


def test_agent_explain_json_excludes_model_score() -> None:
    features = _features_fixture()
    factors = contributing_factors(features)
    explain = build_agent_explain_json(
        features=features,
        review_priority_band="can_ra_soat",
        factors=factors,
    )
    blob = json.dumps(explain)
    assert "model_score" not in explain
    assert "model_score" not in blob
    assert explain["explain_schema_version"] == EXPLAIN_SCHEMA_VERSION
    assert explain["review_priority_band"] == "can_ra_soat"
    assert explain["coverage_status"] == features.coverage.status
    assert explain["coverage_reason_codes"] == list(features.coverage.reason_codes)
    assert explain["last_term_code"] == "2022-2023-T2"
    assert explain["model_version"] == MODEL_VERSION
    assert explain["threshold_config_version"] == THRESHOLD_CONFIG_VERSION
    assert explain["features"]["latest_term_gpa"] == 3.46
    assert explain["features"]["grade_trend_slope"] == -0.123457
    assert "factor_codes" in explain


def test_evidence_fingerprint_deterministic() -> None:
    features = _features_fixture()
    factors = contributing_factors(features)
    codes = [f.code for f in factors]
    first = evidence_fingerprint(
        student_ref=features.student_ref,
        review_priority_band="can_ra_soat",
        factor_codes=codes,
        coverage_status=features.coverage.status,
        features=features,
    )
    # Wall-clock / calculated_at must not affect the fingerprint.
    features2 = features.model_copy(
        update={"calculated_at": datetime(2099, 1, 1, tzinfo=timezone.utc)}
    )
    second = evidence_fingerprint(
        student_ref=features2.student_ref,
        review_priority_band="can_ra_soat",
        factor_codes=list(reversed(codes)),
        coverage_status=features2.coverage.status,
        features=features2,
    )
    assert first == second
    assert len(first) == 64


def test_materialize_semester_idempotent(materialize_database_url: str) -> None:
    imported = import_semester(materialize_database_url, ensure_schema=False)
    assert imported.status == "imported"
    assert imported.source_id == SEMESTER_SOURCE_ID

    with _session(materialize_database_url) as session:
        first = materialize_ml_term_snapshot(session, SEMESTER_SOURCE_ID)
        session.commit()

    assert first.status == "materialized"
    assert first.row_counts["ml_term_snapshot"] == 460

    with _session(materialize_database_url) as session:
        n = session.scalar(select(func.count()).select_from(MlTermSnapshot))
        assert n == 460
        sample = session.scalars(select(MlTermSnapshot).limit(5)).all()
        assert all(r.source_id == SEMESTER_SOURCE_ID for r in sample)
        assert all(r.explain_schema_version == EXPLAIN_SCHEMA_VERSION for r in sample)
        for row in sample:
            explain = json.loads(row.agent_explain_json or "{}")
            assert "model_score" not in explain
            assert explain.get("explain_schema_version") == EXPLAIN_SCHEMA_VERSION
            assert row.evidence_fingerprint
            assert len(row.evidence_fingerprint) == 64
            # model_score may be set on the column; must not leak into explain JSON
            if row.model_score is not None:
                assert "model_score" not in (row.agent_explain_json or "")
        fingerprints = {
            r.student_ref: r.evidence_fingerprint
            for r in session.scalars(select(MlTermSnapshot)).all()
        }

    with _session(materialize_database_url) as session:
        second = materialize_ml_term_snapshot(session, SEMESTER_SOURCE_ID)
        session.commit()

    assert second.status == "materialized"
    assert second.row_counts["ml_term_snapshot"] == 460

    with _session(materialize_database_url) as session:
        n = session.scalar(select(func.count()).select_from(MlTermSnapshot))
        assert n == 460
        again = {
            r.student_ref: r.evidence_fingerprint
            for r in session.scalars(select(MlTermSnapshot)).all()
        }
        assert again == fingerprints


def test_materialize_rejects_unknown_source(materialize_database_url: str) -> None:
    with _session(materialize_database_url) as session:
        result = materialize_ml_term_snapshot(session, "not-a-real-source")
        session.rollback()
    assert result.status == "rejected"
    assert "source_unapproved" in result.reason_codes


def test_score_pipeline_matches_pure_helpers() -> None:
    """Sanity: score_student → factors path used by materializer stays coherent."""
    coverage = Coverage(
        n_valid_terms=2,
        n_courses=2,
        n_attendance_events=0,
        last_term_code="2022-2023-T2",
        last_attendance_at=None,
        status="partial",
        reason_codes=["attendance_source_unapproved"],
    )
    record = NormalizedStudentRecord(
        student_ref="s-1",
        source_id=SEMESTER_SOURCE_ID,
        dataset_version="v59-empty-program-students:abcd1234:epu-1",
        schema_version="epu-1",
        snapshot_sha256="a" * 64,
        provenance_approved=True,
        term_grades=[
            NormalizedTermGrade(
                term_code="2022-2023-T1",
                course_ref="c1",
                credits=3.0,
                final_grade=8.0,
            ),
            NormalizedTermGrade(
                term_code="2022-2023-T2",
                course_ref="c2",
                credits=3.0,
                final_grade=2.0,
                grade_status="Không đạt",
            ),
        ],
        attendance_events=[],
        coverage=coverage,
    )
    features = score_student(record, calculated_at=_CALC_AT)
    factors = contributing_factors(features)
    explain = build_agent_explain_json(
        features=features,
        review_priority_band="uu_tien_som",
        factors=factors,
    )
    assert "model_score" not in explain
    assert features.latest_term_gpa is not None
