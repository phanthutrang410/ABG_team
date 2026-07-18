"""Contract tests cho FairnessReport (H06c) — fail-closed theo Data-ML §6 / M04 §3.

MVP path: không có audit attribute đã duyệt → `insufficient_data`, không rò rỉ
metric. Nhánh `ok` (audit attribute tương lai) vẫn phải enforce group/GT/N/ΔFPR.
"""

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.contracts.fairness import SMALL_N_MIN_DENOMINATOR, FairnessReport

FIXTURE = Path(__file__).parent / "fixtures" / "fairness_report.json"


def load_fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _valid_ok_report() -> dict:
    """Nhánh `ok` hợp lệ (audit attribute giả định đã duyệt) — dùng test schema-shape.

    KHÔNG phải dữ liệu MVP; MVP luôn fail-closed. Chỉ chứng minh validator nhánh
    `ok` vẫn enforce group/GT/N/ΔFPR khi tương lai có nguồn audit được phê duyệt.
    """
    return {
        "dataset_version": "epu-v59empty-approved-abc1234",
        "model_version": "ew-1.0.0",
        "threshold_config_version": "thr-epu-1.0",
        "label_rule_version": "gt-epu-1.0",
        "computed_at": "2026-07-18T00:15:00+07:00",
        "status": "ok",
        "audit_attribute": "example_approved_attribute",
        "small_n_min_denominator": SMALL_N_MIN_DENOMINATOR,
        "groups": [
            {
                "group_type": "socioeconomic",
                "group": "A",
                "n_total": 36,
                "n_label_neg": 29,
                "n_label_pos": 7,
                "n_excluded_insufficient": 4,
                "fpr": 0.1034,
                "tpr": 0.7143,
                "selection_rate": 0.2222,
                "status": "ok",
            },
            {
                "group_type": "socioeconomic",
                "group": "B",
                "n_total": 12,
                "n_label_neg": 9,
                "n_label_pos": 3,
                "n_excluded_insufficient": 9,
                "fpr": None,
                "tpr": None,
                "selection_rate": None,
                "status": "insufficient_group_data",
            },
        ],
        "delta_fpr_by_group_type": {
            "socioeconomic": {"status": "insufficient", "value": None, "reason": "< 2 nhóm đủ mẫu số"}
        },
        "fairness_flag": {
            "flagged": False,
            "delta_fpr_threshold": 0.1,
            "triggered_group_types": [],
        },
    }


# --- Fail-closed MVP path -------------------------------------------------


def test_failclosed_fixture_validates() -> None:
    report = FairnessReport.model_validate(load_fixture())
    assert report.status == "insufficient_data"
    assert report.reason_code == "no_approved_audit_attribute"
    # Không rò rỉ bất kỳ metric nào.
    assert report.groups is None
    assert report.delta_fpr_by_group_type is None
    assert report.fairness_flag is None
    assert report.audit_attribute is None
    assert report.small_n_min_denominator is None


def test_insufficient_data_requires_reason_code() -> None:
    data = load_fixture()
    del data["reason_code"]
    with pytest.raises(ValidationError, match="reason_code"):
        FairnessReport.model_validate(data)


@pytest.mark.parametrize(
    "field,value",
    [
        ("groups", []),
        ("groups", [_valid_ok_report()["groups"][0]]),
        ("fairness_flag", {"flagged": False, "delta_fpr_threshold": 0.1, "triggered_group_types": []}),
        ("audit_attribute", "leaked_attribute"),
        ("small_n_min_denominator", 10),
        ("delta_fpr_by_group_type", {"socioeconomic": {"status": "ok", "value": 0.05, "reason": None}}),
    ],
)
def test_insufficient_data_must_not_carry_metrics(field: str, value: object) -> None:
    data = load_fixture()
    data[field] = value
    with pytest.raises(ValidationError, match="fail-closed|insufficient_data"):
        FairnessReport.model_validate(data)


def test_versioning_fields_required() -> None:
    for field in (
        "dataset_version",
        "model_version",
        "threshold_config_version",
        "label_rule_version",
        "computed_at",
    ):
        data = load_fixture()
        del data[field]
        with pytest.raises(ValidationError):
            FairnessReport.model_validate(data)


def test_synthetic_dataset_version_rejected() -> None:
    data = load_fixture()
    data["dataset_version"] = "synthetic-v0.2-seed42"
    with pytest.raises(ValidationError, match="synthetic"):
        FairnessReport.model_validate(data)


def test_unknown_field_rejected() -> None:
    data = load_fixture()
    data["raw_model_weights"] = {"w": 1.0}
    with pytest.raises(ValidationError):
        FairnessReport.model_validate(data)


# --- Ok branch (future approved audit attribute) --------------------------


def test_ok_report_validates() -> None:
    report = FairnessReport.model_validate(_valid_ok_report())
    assert report.status == "ok"
    assert report.reason_code is None
    assert report.audit_attribute == "example_approved_attribute"
    b = next(g for g in report.groups if g.group == "B")
    assert b.status == "insufficient_group_data"
    assert b.fpr is None


def test_ok_must_not_carry_reason_code() -> None:
    data = _valid_ok_report()
    data["reason_code"] = "no_approved_audit_attribute"
    with pytest.raises(ValidationError, match="reason_code"):
        FairnessReport.model_validate(data)


@pytest.mark.parametrize(
    "field", ["audit_attribute", "small_n_min_denominator", "groups", "delta_fpr_by_group_type", "fairness_flag"]
)
def test_ok_requires_all_metric_fields(field: str) -> None:
    data = _valid_ok_report()
    del data[field]
    with pytest.raises(ValidationError, match="thiếu|status=ok"):
        FairnessReport.model_validate(data)


def test_ok_group_requires_fpr_and_selection_rate() -> None:
    data = _valid_ok_report()
    data["groups"][0]["fpr"] = None
    with pytest.raises(ValidationError, match="fpr"):
        FairnessReport.model_validate(data)


def test_ok_insufficient_group_must_null_metrics() -> None:
    data = _valid_ok_report()
    b = next(g for g in data["groups"] if g["group"] == "B")
    b["fpr"] = 0.2
    with pytest.raises(ValidationError, match="insufficient_group_data"):
        FairnessReport.model_validate(data)


def test_ok_n_total_must_equal_neg_plus_pos() -> None:
    data = _valid_ok_report()
    data["groups"][0]["n_total"] = 99
    with pytest.raises(ValidationError, match="n_label_neg"):
        FairnessReport.model_validate(data)


def test_ok_status_below_small_n_rejected() -> None:
    data = _valid_ok_report()
    g = data["groups"][0]
    g["n_label_neg"] = SMALL_N_MIN_DENOMINATOR - 1
    g["n_total"] = g["n_label_neg"] + g["n_label_pos"]
    with pytest.raises(ValidationError, match="status=ok"):
        FairnessReport.model_validate(data)


def test_ok_sufficient_denominator_cannot_be_insufficient() -> None:
    data = _valid_ok_report()
    b = next(g for g in data["groups"] if g["group"] == "B")
    b.update(
        {
            "n_label_neg": SMALL_N_MIN_DENOMINATOR,
            "n_total": SMALL_N_MIN_DENOMINATOR + b["n_label_pos"],
        }
    )
    with pytest.raises(ValidationError, match="insufficient"):
        FairnessReport.model_validate(data)


def test_ok_delta_keys_must_match_group_types() -> None:
    data = _valid_ok_report()
    data["delta_fpr_by_group_type"] = {}
    with pytest.raises(ValidationError, match="delta_fpr_by_group_type"):
        FairnessReport.model_validate(data)


def test_ok_delta_insufficient_requires_reason_and_null_value() -> None:
    data = _valid_ok_report()
    data["delta_fpr_by_group_type"]["socioeconomic"] = {
        "status": "insufficient",
        "value": None,
        "reason": None,
    }
    with pytest.raises(ValidationError, match="reason"):
        FairnessReport.model_validate(data)


def test_ok_flag_must_match_triggered_types() -> None:
    data = _valid_ok_report()
    data["fairness_flag"]["flagged"] = True
    with pytest.raises(ValidationError, match="triggered_group_types"):
        FairnessReport.model_validate(data)


def test_ok_triggered_type_requires_ok_delta() -> None:
    data = _valid_ok_report()
    data["fairness_flag"] = {
        "flagged": True,
        "delta_fpr_threshold": 0.1,
        "triggered_group_types": ["socioeconomic"],
    }
    with pytest.raises(ValidationError, match="delta status=ok"):
        FairnessReport.model_validate(data)


def test_ok_duplicate_group_rejected() -> None:
    data = _valid_ok_report()
    data["groups"].append(dict(data["groups"][0]))
    with pytest.raises(ValidationError, match="trùng lặp"):
        FairnessReport.model_validate(data)


def test_ok_rate_out_of_range_rejected() -> None:
    data = _valid_ok_report()
    data["groups"][0]["fpr"] = 1.2
    with pytest.raises(ValidationError):
        FairnessReport.model_validate(data)
