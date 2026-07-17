"""M01 — guard quarantine legacy ML synthetic.

Cấm feature attendance-week / synth group / raw risk quay lại scoring contract,
và cấm MVP path (backend/app, scripts) import lại module legacy đã gỡ.
Không cấm audit group hợp lệ trong fairness contract (H06c) hay blocklist
guard trong integration contract — chỉ nhắm định danh legacy.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

from app.contracts.scoring import ScoringFeatures

BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_DIR.parent
APP_DIR = BACKEND_DIR / "app"
SCRIPTS_DIR = REPO_ROOT / "scripts"

# Tên field bị cấm trong scoring (substring, case-insensitive).
FORBIDDEN_FEATURE_SUBSTRINGS = (
    "synth",
    "ethnic",
    "socioeconomic",
    "week",
    "risk",
    "outcome",
    "dropout",
)

# Định danh legacy bị cấm xuất hiện trong MVP path (exact substring).
FORBIDDEN_LEGACY_IDENTIFIERS = (
    "app.ml.early_warning",
    "EarlyWarningFeatures",
    "EarlyWarningPrediction",
    "generate_synthetic",
    "synth_socioeconomic_group",
    "synth_ethnicity_group",
    "attendance_timeseries",
)


def test_legacy_early_warning_module_removed() -> None:
    assert importlib.util.find_spec("app.ml.early_warning") is None, (
        "Module legacy app.ml.early_warning phải bị gỡ khỏi MVP path (M01)"
    )


def test_scoring_features_forbids_week_synth_group_risk_fields() -> None:
    for field_name in ScoringFeatures.model_fields:
        lowered = field_name.lower()
        for forbidden in FORBIDDEN_FEATURE_SUBSTRINGS:
            assert forbidden not in lowered, (
                f"ScoringFeatures.{field_name} vi phạm cấm feature '{forbidden}' "
                "(attendance-week/synth group/raw risk không được vào scoring)"
            )


def test_mvp_paths_do_not_reference_legacy_synthetic() -> None:
    offenders: list[str] = []
    for base in (APP_DIR, SCRIPTS_DIR):
        for path in sorted(base.rglob("*.py")):
            text = path.read_text(encoding="utf-8")
            for identifier in FORBIDDEN_LEGACY_IDENTIFIERS:
                if identifier in text:
                    offenders.append(f"{path.relative_to(REPO_ROOT)}: {identifier}")
    assert offenders == [], (
        "MVP path còn tham chiếu legacy synthetic: " + "; ".join(offenders)
    )


def test_legacy_synthetic_csv_artifacts_removed() -> None:
    data_dir = REPO_ROOT / "data" / "synthetic"
    leftover = sorted(p.name for p in data_dir.glob("*.csv")) if data_dir.exists() else []
    assert leftover == [], f"CSV synthetic cũ còn trong repo: {leftover}"
