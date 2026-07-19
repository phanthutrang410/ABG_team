"""M10 Reality-460 dataset, artifact, runtime, and acceptance gates."""

from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from app.dwh.ml_materializer import materialize_ml_term_snapshot
from app.contracts.coverage import Coverage
from app.contracts.scoring import ScoringFeatures
from app.ml.dropout.artifact import load_artifact
from app.ml.dropout.dataset import load_reality460
from app.ml.dropout.runtime import score_features
from app.ml.dropout.train import _confusion, select_thresholds, train

ROOT = Path(__file__).resolve().parents[2]
DATASET = ROOT / "data" / "approved" / "semester" / "domain_package.json"
ARTIFACT = ROOT / "backend" / "app" / "ml" / "artifacts" / "m10_reality460.json"


def _features(*, gpa: float = 4.5, failed: float = 9.0, terms: int = 2) -> ScoringFeatures:
    return ScoringFeatures(
        dataset_version="v59-empty-program-students:73274079:epu-1",
        model_version="m10-reality460-logreg-1.0",
        threshold_config_version="thr-reality460-oof-recall70-v1",
        calculated_at=datetime(2026, 7, 19, tzinfo=timezone.utc),
        student_ref="s-test",
        latest_term_gpa=gpa,
        grade_trend_slope=-0.2,
        grade_volatility=0.8,
        failed_credits=failed,
        coverage=Coverage(
            n_valid_terms=terms,
            n_courses=8,
            n_attendance_events=0,
            last_term_code="2022-2023-T2",
            status="partial",
            reason_codes=["attendance_source_unapproved"],
        ),
    )


def test_reality460_dataset_exact_gate_and_feature_boundary() -> None:
    dataset = load_reality460(DATASET)
    assert len(dataset.rows) == 460
    assert sum(dataset.labels) == 46
    assert len(dataset.labels) - sum(dataset.labels) == 414
    assert dataset.dataset_version == "v59-empty-program-students:73274079:epu-1"
    assert dataset.training_package_sha256 == (
        "73274079b30487f066cb2e1751c7ec70e2737ff794d6ae76e3e26ec4cf86df24"
    )
    assert all(len(row.vector("A")) == 2 for row in dataset.rows)
    assert all(len(row.vector("B")) == 3 for row in dataset.rows)
    # No attendance/status/advisor/context field can enter the training vector.
    assert set(dataset.rows[0].__dict__) == {
        "student_ref",
        "latest_term_gpa",
        "failed_credits_log1p",
        "grade_trend_slope",
        "outcome",
    }


def test_reality460_rejects_tampered_training_package(tmp_path: Path) -> None:
    payload = json.loads(DATASET.read_text(encoding="utf-8"))
    payload["term_grade"][0]["final_grade"] = 0.0
    tampered = tmp_path / "domain_package.json"
    tampered.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(ValueError, match="training_package_gate_failed"):
        load_reality460(tampered)


def test_artifact_is_promoted_digest_valid_and_contains_no_rows() -> None:
    artifact = load_artifact(ARTIFACT)
    assert artifact.promoted is True
    assert artifact.feature_set == "A"
    assert artifact.feature_order == ["latest_term_gpa", "failed_credits_log1p"]
    assert artifact.aggregate_metrics["oof_recall"] >= 0.70
    assert artifact.aggregate_metrics["oof_precision"] >= 0.50
    assert artifact.aggregate_metrics["oof_fpr"] <= 0.10
    blob = ARTIFACT.read_text(encoding="utf-8").casefold()
    for forbidden in ("student_ref", "status_code", "is_dropout_outcome", "advisor_ref"):
        assert forbidden not in blob


def test_artifact_tamper_is_rejected(tmp_path: Path) -> None:
    payload = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    payload["intercept"] += 0.01
    path = tmp_path / "tampered.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="artifact_hash_mismatch"):
        load_artifact(path)


def test_runtime_matches_exported_linear_equation() -> None:
    artifact = load_artifact(ARTIFACT)
    features = _features()
    result = score_features(features, artifact)
    raw = {
        "latest_term_gpa": float(features.latest_term_gpa),
        "failed_credits_log1p": math.log1p(float(features.failed_credits)),
    }
    logit = artifact.intercept + sum(
        artifact.coefficients[name]
        * (raw[name] - artifact.means[name])
        / artifact.scales[name]
        for name in artifact.feature_order
    )
    expected = 1.0 / (1.0 + math.exp(-logit))
    assert result.score == pytest.approx(expected, abs=1e-12)
    assert result.review_priority_band is not None
    assert result.factors
    assert "grade_only_model" in result.limitations
    assert "two_term_history" in result.limitations


def test_runtime_fails_closed_without_two_terms() -> None:
    result = score_features(_features(terms=1), load_artifact(ARTIFACT))
    assert result.score is None
    assert result.review_priority_band is None
    assert result.factors == []
    assert result.reason_codes == ["grade_coverage_insufficient"]


def test_threshold_selection_is_deterministic_and_enforces_gate() -> None:
    labels = [1, 1, 1] + [0] * 17
    scores = [0.95, 0.85, 0.75, 0.7] + [0.2 - index * 0.01 for index in range(16)]
    first = select_thresholds(labels, scores)
    second = select_thresholds(labels, scores)
    assert first == second
    case, high = first
    assert case.recall >= 0.70
    assert case.precision >= 0.50
    assert case.fpr <= 0.10
    assert case.selection_rate <= 0.15
    assert high.threshold >= case.threshold


def test_confusion_denominators() -> None:
    metric = _confusion([1, 1, 0, 0], [0.9, 0.1, 0.8, 0.2], 0.5)
    assert (metric.tp, metric.fp, metric.tn, metric.fn) == (1, 1, 1, 1)
    assert metric.precision == 0.5
    assert metric.recall == 0.5
    assert metric.fpr == 0.5


def test_nested_cv_training_reproduces_committed_artifact() -> None:
    dataset = load_reality460(DATASET)
    trained, report = train(dataset)
    committed = load_artifact(ARTIFACT)
    assert report["status"] == "promoted"
    assert trained.artifact_sha256 == committed.artifact_sha256
    assert trained.model_dump() == committed.model_dump()


def test_invalid_artifact_rejects_before_snapshot_delete(monkeypatch: pytest.MonkeyPatch) -> None:
    import app.dwh.ml_materializer as materializer

    session = MagicMock()
    monkeypatch.setattr(materializer, "list_normalized_students", lambda *_args: [object()])
    monkeypatch.setattr(
        materializer,
        "active_artifact",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(ValueError("artifact_hash_mismatch")),
    )
    result = materialize_ml_term_snapshot(session, "v59-empty-program-students")
    assert result.status == "rejected"
    assert result.reason_codes == ["model_artifact_invalid"]
    session.execute.assert_not_called()


def test_dataset_hash_mismatch_rejects_before_snapshot_delete(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import app.dwh.ml_materializer as materializer

    record = MagicMock(dataset_version="v59-empty-program-students:73274079:epu-1")
    artifact = MagicMock(
        training_package_sha256="7" * 64,
        dataset_version=record.dataset_version,
    )
    session = MagicMock()
    session.get.return_value = MagicMock(snapshot_sha256="a" * 64)
    monkeypatch.setattr(materializer, "list_normalized_students", lambda *_args: [record] * 460)
    monkeypatch.setattr(materializer, "active_artifact", lambda: artifact)

    result = materialize_ml_term_snapshot(session, "v59-empty-program-students")
    assert result.status == "rejected"
    assert result.reason_codes == ["model_dataset_mismatch"]
    session.execute.assert_not_called()
