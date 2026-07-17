from app.ml.early_warning.types import EarlyWarningFeatures, EarlyWarningPrediction


def test_feature_contract_has_non_invasive_fields() -> None:
    feats = EarlyWarningFeatures(
        student_id="S001",
        grade_volatility_30d=0.2,
        attendance_rate_30d=0.85,
        attendance_trend_slope=-0.01,
        grade_trend_slope=-0.05,
        synth_socioeconomic_group="A",
        synth_ethnicity_group="X",
    )
    assert feats.student_id == "S001"


def test_prediction_carries_factors() -> None:
    pred = EarlyWarningPrediction(
        student_id="S001",
        risk_score=0.72,
        model_version="ew-0.1.0",
        contributing_factors={"attendance_trend_slope": 0.4},
    )
    assert 0.0 <= pred.risk_score <= 1.0
    assert "attendance_trend_slope" in pred.contributing_factors
