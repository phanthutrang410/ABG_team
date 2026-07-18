"""M05a — fail-closed source gate tests.

Chứng minh gate logic; KHÔNG tạo/nạp dữ liệu "đã duyệt" vào repo. Mọi file là
ephemeral trong tmp_path. `admitted=True` ở đây = gate logic đúng, không phải
M05b (approval artifact của data owner).
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.ml.source_gate import (
    GateResult,
    SourceManifest,
    compute_sha256,
    evaluate_source,
)

# Bản ghi hợp lệ tối thiểu: pseudonym + trường domain điểm, không PII, không synthetic.
_CLEAN_RECORDS = [
    {"student_ref": "s-0001", "term_code": "2022-2023-T1", "course_ref": "c1", "final_grade": 7.5},
    {"student_ref": "s-0002", "term_code": "2022-2023-T1", "course_ref": "c1", "final_grade": 6.0},
]


def _write_json(path: Path, payload: object) -> str:
    text = json.dumps(payload, ensure_ascii=False)
    path.write_text(text, encoding="utf-8")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _manifest(
    *,
    source_id: str = "v59-empty-program-students",
    sha256: str,
    record_count: int,
    provenance_approved: bool = True,
) -> SourceManifest:
    return SourceManifest(
        source_id=source_id,
        snapshot_sha256=sha256,
        record_count=record_count,
        provenance_approved=provenance_approved,
        schema_version="epu-1",
        extracted_at=datetime(2026, 7, 18, tzinfo=timezone.utc),
        owner="data-owner-epu",
        usage_rights="approved-for-mvp",
    )


def _clean_source(tmp_path: Path, **manifest_kw) -> tuple[Path, SourceManifest]:
    path = tmp_path / "source.json"
    sha = _write_json(path, _CLEAN_RECORDS)
    manifest = _manifest(sha256=sha, record_count=len(_CLEAN_RECORDS), **manifest_kw)
    return path, manifest


# --- Happy path (gate logic admits) ---------------------------------------


def test_clean_approved_source_admitted(tmp_path: Path) -> None:
    path, manifest = _clean_source(tmp_path)
    result = evaluate_source(path, manifest)
    assert result.admitted is True
    assert result.reason_codes == []
    assert result.role == "primary"
    assert result.observed_record_count == len(_CLEAN_RECORDS)
    assert result.computed_sha256 == manifest.normalized_sha256
    assert result.pii_fields_found == []


def test_result_carries_no_data_rows(tmp_path: Path) -> None:
    path, manifest = _clean_source(tmp_path)
    result = evaluate_source(path, manifest)
    # GateResult chỉ quyết định admission — không có field mang hàng dữ liệu.
    assert set(result.model_dump()) == set(GateResult.model_fields)
    assert set(GateResult.model_fields) == {
        "source_id",
        "admitted",
        "reason_codes",
        "role",
        "computed_sha256",
        "observed_record_count",
        "pii_fields_found",
    }


# --- Fail-closed layers ----------------------------------------------------


def test_unapproved_provenance_rejected(tmp_path: Path) -> None:
    path, manifest = _clean_source(tmp_path, provenance_approved=False)
    result = evaluate_source(path, manifest)
    assert result.admitted is False
    assert "source_unapproved" in result.reason_codes


def test_source_not_in_allowlist_rejected(tmp_path: Path) -> None:
    path, manifest = _clean_source(tmp_path, source_id="some-unknown-source")
    result = evaluate_source(path, manifest)
    assert result.admitted is False
    assert "source_not_in_allowlist" in result.reason_codes
    assert result.role is None


def test_hash_mismatch_rejected(tmp_path: Path) -> None:
    path, _ = _clean_source(tmp_path)
    manifest = _manifest(sha256="0" * 64, record_count=len(_CLEAN_RECORDS))
    result = evaluate_source(path, manifest)
    assert result.admitted is False
    assert "hash_mismatch" in result.reason_codes


def test_record_count_mismatch_rejected(tmp_path: Path) -> None:
    path = tmp_path / "source.json"
    sha = _write_json(path, _CLEAN_RECORDS)
    manifest = _manifest(sha256=sha, record_count=999)
    result = evaluate_source(path, manifest)
    assert result.admitted is False
    assert "record_count_mismatch" in result.reason_codes


@pytest.mark.parametrize(
    "records",
    [
        [{"student_ref": "SYN0001", "final_grade": 7.0}],  # id synthetic
        [{"student_ref": "s-1", "synth_group": "A", "final_grade": 7.0}],  # field prefix synth_
        [{"student_ref": "s-1", "note": "synthetic sample", "final_grade": 7.0}],  # text marker
    ],
)
def test_synthetic_source_rejected(tmp_path: Path, records: list) -> None:
    path = tmp_path / "source.json"
    sha = _write_json(path, records)
    manifest = _manifest(sha256=sha, record_count=len(records))
    result = evaluate_source(path, manifest)
    assert result.admitted is False
    assert "synthetic_source_rejected" in result.reason_codes


@pytest.mark.parametrize(
    "pii_field",
    ["MSSV", "Họ và tên", "Email", "Số điện thoại", "Ngày sinh", "token"],
)
def test_pii_field_rejected(tmp_path: Path, pii_field: str) -> None:
    records = [{"student_ref": "s-1", pii_field: "x", "final_grade": 7.0}]
    path = tmp_path / "source.json"
    sha = _write_json(path, records)
    manifest = _manifest(sha256=sha, record_count=len(records))
    result = evaluate_source(path, manifest)
    assert result.admitted is False
    assert "pii_field_present" in result.reason_codes
    assert pii_field in result.pii_fields_found


def test_pseudonym_fields_not_flagged_as_pii(tmp_path: Path) -> None:
    records = [{"student_ref": "s-1", "advisor_ref": "a-1", "final_grade": 7.0}]
    path = tmp_path / "source.json"
    sha = _write_json(path, records)
    manifest = _manifest(sha256=sha, record_count=len(records))
    result = evaluate_source(path, manifest)
    assert result.pii_fields_found == []
    assert result.admitted is True


def test_missing_file_rejected(tmp_path: Path) -> None:
    manifest = _manifest(sha256="0" * 64, record_count=0)
    result = evaluate_source(tmp_path / "does_not_exist.json", manifest)
    assert result.admitted is False
    assert result.reason_codes == ["unreadable_source"]


def test_non_json_rejected(tmp_path: Path) -> None:
    path = tmp_path / "source.json"
    path.write_text("not json {", encoding="utf-8")
    manifest = _manifest(sha256=compute_sha256(path), record_count=1)
    result = evaluate_source(path, manifest)
    assert result.admitted is False
    assert result.reason_codes == ["unreadable_source"]


def test_multiple_failures_accumulate(tmp_path: Path) -> None:
    records = [{"student_ref": "SYN0001", "MSSV": "123", "final_grade": 7.0}]
    path = tmp_path / "source.json"
    _write_json(path, records)
    manifest = _manifest(
        source_id="unknown",
        sha256="0" * 64,
        record_count=999,
        provenance_approved=False,
    )
    result = evaluate_source(path, manifest)
    assert result.admitted is False
    assert {
        "source_not_in_allowlist",
        "synthetic_source_rejected",
        "source_unapproved",
        "hash_mismatch",
        "record_count_mismatch",
        "pii_field_present",
    } <= set(result.reason_codes)


# --- Determinism -----------------------------------------------------------


def test_hash_is_deterministic(tmp_path: Path) -> None:
    path, manifest = _clean_source(tmp_path)
    first = evaluate_source(path, manifest)
    second = evaluate_source(path, manifest)
    assert first.computed_sha256 == second.computed_sha256
    assert first.model_dump() == second.model_dump()


# --- Manifest validation ---------------------------------------------------


def test_manifest_rejects_bad_sha256_via_gate(tmp_path: Path) -> None:
    # sha256 sai định dạng ⇒ không well-formed ⇒ hash_mismatch (fail-closed).
    path, _ = _clean_source(tmp_path)
    manifest = _manifest(sha256="xyz", record_count=len(_CLEAN_RECORDS))
    result = evaluate_source(path, manifest)
    assert result.admitted is False
    assert "hash_mismatch" in result.reason_codes


def test_manifest_negative_record_count_rejected() -> None:
    with pytest.raises(ValidationError):
        _manifest(sha256="0" * 64, record_count=-1)


def test_manifest_forbids_unknown_field() -> None:
    with pytest.raises(ValidationError):
        SourceManifest(
            source_id="v59-empty-program-students",
            snapshot_sha256="0" * 64,
            record_count=0,
            provenance_approved=True,
            schema_version="epu-1",
            extracted_at=datetime(2026, 7, 18, tzinfo=timezone.utc),
            owner="o",
            usage_rights="r",
            unexpected="boom",
        )


# --- H15 allowlisted attendance (decision #18) -----------------------------

_ATTENDANCE_FIXTURE = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "approved"
    / "attendance"
    / "mvp_attendance_over_time.json"
)


def test_mvp_attendance_fixture_admitted() -> None:
    assert _ATTENDANCE_FIXTURE.is_file()
    sha = compute_sha256(_ATTENDANCE_FIXTURE)
    manifest = SourceManifest(
        source_id="mvp-attendance-over-time",
        snapshot_sha256=sha,
        record_count=7360,
        provenance_approved=True,
        schema_version="epu-1",
        extracted_at=datetime(2026, 7, 18, tzinfo=timezone.utc),
        owner="admin-ky-thuat-hoang",
        usage_rights="mvp-demo-attendance",
    )
    result = evaluate_source(_ATTENDANCE_FIXTURE, manifest)
    assert result.admitted is True
    assert result.reason_codes == []
    assert result.role == "attendance"
    assert result.observed_record_count == 7360
    assert result.pii_fields_found == []


def test_mvp_attendance_unapproved_rejected() -> None:
    sha = compute_sha256(_ATTENDANCE_FIXTURE)
    manifest = SourceManifest(
        source_id="mvp-attendance-over-time",
        snapshot_sha256=sha,
        record_count=7360,
        provenance_approved=False,
        schema_version="epu-1",
        extracted_at=datetime(2026, 7, 18, tzinfo=timezone.utc),
        owner="admin-ky-thuat-hoang",
        usage_rights="mvp-demo-attendance",
    )
    result = evaluate_source(_ATTENDANCE_FIXTURE, manifest)
    assert result.admitted is False
    assert "source_unapproved" in result.reason_codes


def test_legacy_synthetic_marker_still_rejected_on_attendance_id(tmp_path: Path) -> None:
    """Allowlist id không miễn marker 'synthetic' trong payload."""
    records = {
        "source_id": "mvp-attendance-over-time",
        "events": [
            {
                "student_ref": "s-1",
                "observed_at": "2026-07-01",
                "presence_status": "present",
                "note": "synthetic sample",
            }
        ],
    }
    path = tmp_path / "bad.json"
    sha = _write_json(path, records)
    manifest = SourceManifest(
        source_id="mvp-attendance-over-time",
        snapshot_sha256=sha,
        record_count=1,
        provenance_approved=True,
        schema_version="epu-1",
        extracted_at=datetime(2026, 7, 18, tzinfo=timezone.utc),
        owner="o",
        usage_rights="r",
    )
    result = evaluate_source(path, manifest)
    assert result.admitted is False
    assert "synthetic_source_rejected" in result.reason_codes
