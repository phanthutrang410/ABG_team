"""M03 — fairness gate tests (Data-ML §6, M04 §5 test plan).

MVP path: catalog has no approved audit attribute → always
`insufficient_data`. The `ok`-branch formulas are exercised with a
monkeypatched catalog entry — NOT real MVP data (mirrors H06c's own
contract-test pattern) — to prove FPR/ΔFPR/N/small-N logic before any real
audit source is approved.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.contracts.fairness import SMALL_N_MIN_DENOMINATOR, FairnessReport
from app.ml.fairness import gate
from app.ml.fairness.gate import (
    APPROVED_AUDIT_ATTRIBUTES,
    AuditRecord,
    build_fairness_report,
    compute_delta_fpr,
    compute_fairness_flag,
    compute_group_metrics,
)

_COMPUTED_AT = datetime(2026, 7, 18, tzinfo=timezone.utc)
_VERSIONS = dict(
    dataset_version="v59-empty-program-students:abcd1234:epu-1",
    model_version="m02-baseline-0.1",
    threshold_config_version="thr-epu-0.1-uncalibrated",
    label_rule_version="gt-epu-1.0",
    computed_at=_COMPUTED_AT,
)


def _records(group: str, n_neg_flagged: int, n_neg_total: int, n_pos_flagged: int, n_pos_total: int, n_unknown: int = 0, n_insufficient: int = 0) -> list:
    recs = []
    for i in range(n_neg_total):
        recs.append(
            AuditRecord(
                student_ref=f"{group}-neg-{i}",
                group=group,
                label="false",
                flagged=i < n_neg_flagged,
            )
        )
    for i in range(n_pos_total):
        recs.append(
            AuditRecord(
                student_ref=f"{group}-pos-{i}",
                group=group,
                label="true",
                flagged=i < n_pos_flagged,
            )
        )
    for i in range(n_unknown):
        recs.append(
            AuditRecord(student_ref=f"{group}-unk-{i}", group=group, label="unknown", flagged=True)
        )
    for i in range(n_insufficient):
        recs.append(
            AuditRecord(
                student_ref=f"{group}-insuff-{i}",
                group=group,
                label="false",
                flagged=True,
                coverage_sufficient=False,
            )
        )
    return recs


# --- Catalog / fail-closed gate ---------------------------------------------


def test_mvp_catalog_is_empty():
    """Regression guard: adding an entry here must go through an approval decision."""
    assert APPROVED_AUDIT_ATTRIBUTES == {}


def test_no_audit_attribute_is_fail_closed():
    report = build_fairness_report(**_VERSIONS, audit_attribute=None)
    assert report.status == "insufficient_data"
    assert report.reason_code == "no_approved_audit_attribute"
    assert report.groups is None
    assert report.fairness_flag is None
    assert report.audit_attribute is None


def test_unrecognized_audit_attribute_is_fail_closed():
    report = build_fairness_report(**_VERSIONS, audit_attribute="khoa")
    assert report.status == "insufficient_data"
    assert report.reason_code == "no_approved_audit_attribute"


def test_fail_closed_report_validates_against_contract():
    report = build_fairness_report(**_VERSIONS, audit_attribute=None)
    # Round-trips through the H06c contract cleanly (no leaked metric fields).
    assert FairnessReport.model_validate(report.model_dump()) == report


# --- compute_group_metrics ---------------------------------------------------


def test_group_metrics_fpr_tpr_selection_rate_definitions():
    records = _records("A", n_neg_flagged=3, n_neg_total=12, n_pos_flagged=2, n_pos_total=5)
    metrics = compute_group_metrics("socioeconomic", "A", records)
    assert metrics.status == "ok"
    assert metrics.n_label_neg == 12
    assert metrics.n_label_pos == 5
    assert metrics.n_total == 17
    assert metrics.fpr == pytest.approx(3 / 12)
    assert metrics.tpr == pytest.approx(2 / 5)
    assert metrics.selection_rate == pytest.approx(5 / 17, abs=1e-5)


def test_group_metrics_below_small_n_is_insufficient():
    records = _records("B", n_neg_flagged=1, n_neg_total=SMALL_N_MIN_DENOMINATOR - 1, n_pos_flagged=0, n_pos_total=2)
    metrics = compute_group_metrics("socioeconomic", "B", records)
    assert metrics.status == "insufficient_group_data"
    assert metrics.fpr is None
    assert metrics.tpr is None
    assert metrics.selection_rate is None


def test_group_metrics_at_small_n_boundary_is_ok():
    records = _records("C", n_neg_flagged=0, n_neg_total=SMALL_N_MIN_DENOMINATOR, n_pos_flagged=0, n_pos_total=0)
    metrics = compute_group_metrics("socioeconomic", "C", records)
    assert metrics.status == "ok"
    assert metrics.n_label_neg == SMALL_N_MIN_DENOMINATOR


def test_group_metrics_excludes_unknown_and_insufficient_coverage():
    records = _records(
        "D",
        n_neg_flagged=2,
        n_neg_total=10,
        n_pos_flagged=1,
        n_pos_total=3,
        n_unknown=4,
        n_insufficient=5,
    )
    metrics = compute_group_metrics("socioeconomic", "D", records)
    assert metrics.n_total == 13  # unknown + insufficient-coverage excluded from denominators
    assert metrics.n_excluded_insufficient == 5
    assert metrics.status == "ok"


def test_group_metrics_no_positives_leaves_tpr_null():
    records = _records("E", n_neg_flagged=1, n_neg_total=10, n_pos_flagged=0, n_pos_total=0)
    metrics = compute_group_metrics("socioeconomic", "E", records)
    assert metrics.status == "ok"
    assert metrics.tpr is None
    assert metrics.fpr is not None


# --- compute_delta_fpr / compute_fairness_flag ------------------------------


def test_delta_fpr_requires_two_ok_groups():
    a = compute_group_metrics("socioeconomic", "A", _records("A", 1, 10, 0, 0))
    delta = compute_delta_fpr([a])
    assert delta.status == "insufficient"
    assert delta.value is None
    assert delta.reason


def test_delta_fpr_max_minus_min():
    a = compute_group_metrics("socioeconomic", "A", _records("A", 3, 10, 0, 0))  # fpr=0.3
    b = compute_group_metrics("socioeconomic", "B", _records("B", 1, 10, 0, 0))  # fpr=0.1
    delta = compute_delta_fpr([a, b])
    assert delta.status == "ok"
    assert delta.value == pytest.approx(0.2)


def test_fairness_flag_triggers_above_threshold():
    a = compute_group_metrics("socioeconomic", "A", _records("A", 5, 10, 0, 0))  # fpr=0.5
    b = compute_group_metrics("socioeconomic", "B", _records("B", 1, 10, 0, 0))  # fpr=0.1
    delta = compute_delta_fpr([a, b])
    flag = compute_fairness_flag({"socioeconomic": delta}, threshold=0.1)
    assert flag.flagged is True
    assert flag.triggered_group_types == ["socioeconomic"]


def test_fairness_flag_not_triggered_at_or_below_threshold():
    a = compute_group_metrics("socioeconomic", "A", _records("A", 2, 10, 0, 0))  # fpr=0.2
    b = compute_group_metrics("socioeconomic", "B", _records("B", 1, 10, 0, 0))  # fpr=0.1
    delta = compute_delta_fpr([a, b])
    flag = compute_fairness_flag({"socioeconomic": delta}, threshold=0.1)
    assert flag.flagged is False
    assert flag.triggered_group_types == []


# --- build_fairness_report ok branch (future, monkeypatched catalog) -------


def test_ok_branch_end_to_end_with_approved_attribute(monkeypatch):
    monkeypatch.setitem(gate.APPROVED_AUDIT_ATTRIBUTES, "example_approved_attribute", "socioeconomic")
    records = _records("A", 3, 12, 2, 5) + _records("B", 1, 10, 0, 3)
    report = build_fairness_report(
        **_VERSIONS, audit_attribute="example_approved_attribute", records=records
    )
    assert report.status == "ok"
    assert report.audit_attribute == "example_approved_attribute"
    assert {g.group for g in report.groups} == {"A", "B"}
    assert report.delta_fpr_by_group_type["socioeconomic"].status == "ok"
    # Round-trips through the H06c contract cleanly.
    assert FairnessReport.model_validate(report.model_dump()) == report


def test_ok_branch_raises_when_no_group_records(monkeypatch):
    monkeypatch.setitem(gate.APPROVED_AUDIT_ATTRIBUTES, "example_approved_attribute", "socioeconomic")
    with pytest.raises(ValueError, match="no group records"):
        build_fairness_report(
            **_VERSIONS, audit_attribute="example_approved_attribute", records=[]
        )
