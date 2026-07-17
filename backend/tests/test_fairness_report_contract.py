"""Contract tests cho FairnessReport (H06c) — semantics theo M04 §7-§8."""

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.contracts.fairness import SMALL_N_MIN_DENOMINATOR, FairnessReport

FIXTURE = Path(__file__).parent / "fixtures" / "fairness_report.json"


def load_fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_fixture_validates() -> None:
    report = FairnessReport.model_validate(load_fixture())
    assert report.synthetic is True
    assert report.small_n_min_denominator == SMALL_N_MIN_DENOMINATOR
    hmong = next(g for g in report.groups if g.group == "Hmong")
    assert hmong.status == "insufficient_group_data"
    assert hmong.fpr is None and hmong.tpr is None and hmong.selection_rate is None
    assert hmong.n_label_neg < report.small_n_min_denominator
    assert report.fairness_flag.flagged is False


def test_rejects_non_synthetic() -> None:
    data = load_fixture()
    data["synthetic"] = False
    with pytest.raises(ValidationError):
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


def test_ok_group_requires_fpr_and_selection_rate() -> None:
    data = load_fixture()
    data["groups"][0]["fpr"] = None
    with pytest.raises(ValidationError, match="fpr"):
        FairnessReport.model_validate(data)


def test_insufficient_group_must_null_metrics() -> None:
    data = load_fixture()
    hmong = next(g for g in data["groups"] if g["group"] == "Hmong")
    hmong["fpr"] = 0.2
    with pytest.raises(ValidationError, match="insufficient_group_data"):
        FairnessReport.model_validate(data)


def test_n_total_must_equal_neg_plus_pos() -> None:
    data = load_fixture()
    data["groups"][0]["n_total"] = 99
    with pytest.raises(ValidationError, match="n_label_neg"):
        FairnessReport.model_validate(data)


def test_ok_status_below_small_n_rejected() -> None:
    data = load_fixture()
    g = data["groups"][0]
    g["n_label_neg"] = SMALL_N_MIN_DENOMINATOR - 1
    g["n_total"] = g["n_label_neg"] + g["n_label_pos"]
    with pytest.raises(ValidationError, match="status=ok"):
        FairnessReport.model_validate(data)


def test_sufficient_denominator_cannot_be_insufficient() -> None:
    data = load_fixture()
    data["groups"][0].update(
        {"status": "insufficient_group_data", "fpr": None, "tpr": None, "selection_rate": None}
    )
    with pytest.raises(ValidationError, match="insufficient"):
        FairnessReport.model_validate(data)


def test_delta_insufficient_requires_reason_and_null_value() -> None:
    data = load_fixture()
    data["delta_fpr_by_group_type"]["ethnicity"] = {
        "status": "insufficient",
        "value": None,
        "reason": None,
    }
    with pytest.raises(ValidationError, match="reason"):
        FairnessReport.model_validate(data)

    data["delta_fpr_by_group_type"]["ethnicity"] = {
        "status": "insufficient",
        "value": None,
        "reason": "< 2 nhóm đủ mẫu số",
    }
    report = FairnessReport.model_validate(data)
    assert report.delta_fpr_by_group_type["ethnicity"].value is None


def test_delta_keys_must_match_group_types() -> None:
    data = load_fixture()
    del data["delta_fpr_by_group_type"]["ethnicity"]
    with pytest.raises(ValidationError, match="delta_fpr_by_group_type"):
        FairnessReport.model_validate(data)


def test_flag_must_match_triggered_types() -> None:
    data = load_fixture()
    data["fairness_flag"]["flagged"] = True
    with pytest.raises(ValidationError, match="triggered_group_types"):
        FairnessReport.model_validate(data)


def test_triggered_type_requires_ok_delta() -> None:
    data = load_fixture()
    data["delta_fpr_by_group_type"]["ethnicity"] = {
        "status": "insufficient",
        "value": None,
        "reason": "< 2 nhóm đủ mẫu số",
    }
    data["fairness_flag"] = {
        "flagged": True,
        "delta_fpr_threshold": 0.1,
        "triggered_group_types": ["ethnicity"],
    }
    with pytest.raises(ValidationError, match="delta status=ok"):
        FairnessReport.model_validate(data)


def test_rate_out_of_range_rejected() -> None:
    data = load_fixture()
    data["groups"][0]["fpr"] = 1.2
    with pytest.raises(ValidationError):
        FairnessReport.model_validate(data)


def test_duplicate_group_rejected() -> None:
    data = load_fixture()
    data["groups"].append(dict(data["groups"][0]))
    with pytest.raises(ValidationError, match="trùng lặp"):
        FairnessReport.model_validate(data)


def test_unknown_field_rejected() -> None:
    data = load_fixture()
    data["raw_model_weights"] = {"w": 1.0}
    with pytest.raises(ValidationError):
        FairnessReport.model_validate(data)
