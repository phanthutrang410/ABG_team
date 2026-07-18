"""H18 — quarantine legacy ML synthetic khỏi API / MVP public path.

Builds on M01 (module/CSV/scoring field bans). This suite locks the *API surface*:
cases router, public contracts, OpenAPI — no EarlyWarning*, no raw risk public,
no synthetic dataset on ReviewCase path.

Does **not** ban approved attendance_event after H15.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

from fastapi.testclient import TestClient

from app.contracts.integration import FORBIDDEN_PUBLIC_FIELDS
from app.contracts.review_case import ReviewCase
from app.main import app

BACKEND_DIR = Path(__file__).resolve().parents[1]
APP_DIR = BACKEND_DIR / "app"

# API / MVP packages that must never re-import legacy synthetic ML.
API_MVP_PACKAGES = (
    APP_DIR / "cases",
    APP_DIR / "contracts",
    APP_DIR / "main.py",
    APP_DIR / "config.py",
    APP_DIR / "database.py",
    APP_DIR / "dwh",
)

FORBIDDEN_LEGACY_IDENTIFIERS = (
    "app.ml.early_warning",
    "EarlyWarningFeatures",
    "EarlyWarningPrediction",
    "generate_synthetic",
    "synth_socioeconomic_group",
    "synth_ethnicity_group",
    "attendance_timeseries",
)

# Raw risk / score names that must never appear as public response model fields.
FORBIDDEN_PUBLIC_RISK_FIELDS = (
    "risk_score",
    "model_score",
    "raw_score",
    "probability",
)


def _iter_api_mvp_py() -> list[Path]:
    paths: list[Path] = []
    for entry in API_MVP_PACKAGES:
        if entry.is_file() and entry.suffix == ".py":
            paths.append(entry)
        elif entry.is_dir():
            paths.extend(sorted(entry.rglob("*.py")))
    return paths


def test_legacy_early_warning_module_absent() -> None:
    assert importlib.util.find_spec("app.ml.early_warning") is None, (
        "H18: app.ml.early_warning phải vắng trên MVP path (sau M01)"
    )
    leftover = APP_DIR / "ml" / "early_warning"
    assert not leftover.exists(), (
        f"H18: leftover path còn tồn tại: {leftover} (xóa cả __pycache__)"
    )


def test_api_mvp_packages_do_not_reference_legacy_synthetic() -> None:
    offenders: list[str] = []
    for path in _iter_api_mvp_py():
        text = path.read_text(encoding="utf-8")
        for identifier in FORBIDDEN_LEGACY_IDENTIFIERS:
            if identifier in text:
                offenders.append(f"{path.relative_to(BACKEND_DIR)}: {identifier}")
    assert offenders == [], (
        "H18 API/MVP path còn legacy synthetic: " + "; ".join(offenders)
    )


def test_forbidden_public_fields_include_raw_risk() -> None:
    for name in FORBIDDEN_PUBLIC_RISK_FIELDS:
        assert name in FORBIDDEN_PUBLIC_FIELDS, (
            f"H18: FORBIDDEN_PUBLIC_FIELDS thiếu {name}"
        )


def test_review_case_public_fields_exclude_raw_risk() -> None:
    public = set(ReviewCase.model_fields.keys())
    leaked = public.intersection(FORBIDDEN_PUBLIC_RISK_FIELDS)
    assert leaked == set(), f"H18: ReviewCase còn field raw risk: {sorted(leaked)}"
    for banned in (
        "EarlyWarningFeatures",
        "synth_socioeconomic_group",
        "is_dropout_outcome",
        "advisor_ref",
    ):
        assert banned not in public


def test_openapi_paths_do_not_expose_raw_risk_properties() -> None:
    """OpenAPI components/schemas must not advertise raw risk on public models."""
    schema = app.openapi()
    offenders: list[str] = []
    for schema_name, body in (schema.get("components") or {}).get("schemas", {}).items():
        props = body.get("properties") or {}
        for field in FORBIDDEN_PUBLIC_RISK_FIELDS:
            if field in props:
                offenders.append(f"{schema_name}.{field}")
    assert offenders == [], (
        "H18 OpenAPI còn raw risk properties: " + ", ".join(offenders)
    )


def test_health_and_cases_surface_reachable_without_legacy_ml() -> None:
    client = TestClient(app)
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"
    # Transition surface exists; list/detail ReviewCase is H02 (after M02).
    openapi = client.get("/openapi.json")
    assert openapi.status_code == 200
    paths = openapi.json().get("paths", {})
    assert "/health" in paths
    assert any(p.startswith("/cases") for p in paths)
