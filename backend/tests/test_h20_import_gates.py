"""H20a — import_gate unit tests (no DB). Fail-closed approval/hash/PII/synthetic."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

import pytest

from app.dwh.import_gate import (
    ApprovalArtifact,
    evaluate_domain_package,
    evaluate_snapshot_bytes,
)

_EXTRACTED = datetime(2026, 7, 18, tzinfo=timezone.utc)


def _approval(**kw) -> ApprovalArtifact:
    defaults = dict(
        source_id="mvp-attendance-over-time",
        snapshot_sha256="a" * 64,
        record_count=1,
        provenance_approved=True,
        schema_version="epu-1",
        extracted_at=_EXTRACTED,
        owner="test-owner",
        usage_rights="mvp-only",
    )
    defaults.update(kw)
    return ApprovalArtifact(**defaults)


def _bytes_for(payload: object) -> tuple[bytes, str]:
    raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    return raw, hashlib.sha256(raw).hexdigest()


def test_clean_snapshot_admitted():
    payload = {"events": [{"student_ref": "s-1", "observed_at": "2026-05-01"}]}
    raw, sha = _bytes_for(payload)
    gate = evaluate_snapshot_bytes(
        raw, _approval(snapshot_sha256=sha, record_count=1), observed_record_count=1
    )
    assert gate.admitted is True
    assert gate.reason_codes == []


def test_unapproved_rejected():
    payload = [{"student_ref": "s-1"}]
    raw, sha = _bytes_for(payload)
    gate = evaluate_snapshot_bytes(
        raw,
        _approval(
            source_id="v59-empty-program-students",
            snapshot_sha256=sha,
            record_count=1,
            provenance_approved=False,
        ),
        observed_record_count=1,
    )
    assert gate.admitted is False
    assert "source_unapproved" in gate.reason_codes


def test_hash_mismatch_rejected():
    payload = [{"student_ref": "s-1"}]
    raw, _sha = _bytes_for(payload)
    gate = evaluate_snapshot_bytes(
        raw,
        _approval(
            source_id="v59-empty-program-students",
            snapshot_sha256="b" * 64,
            record_count=1,
        ),
        observed_record_count=1,
    )
    assert gate.admitted is False
    assert "hash_mismatch" in gate.reason_codes


def test_record_count_mismatch_rejected():
    payload = [{"student_ref": "s-1"}, {"student_ref": "s-2"}]
    raw, sha = _bytes_for(payload)
    gate = evaluate_snapshot_bytes(
        raw,
        _approval(
            source_id="v59-empty-program-students",
            snapshot_sha256=sha,
            record_count=99,
        ),
        observed_record_count=2,
    )
    assert gate.admitted is False
    assert "record_count_mismatch" in gate.reason_codes


def test_synthetic_marker_rejected():
    payload = [{"student_ref": "s-1", "note": "synthetic demo"}]
    raw, sha = _bytes_for(payload)
    gate = evaluate_snapshot_bytes(
        raw,
        _approval(
            source_id="v59-empty-program-students",
            snapshot_sha256=sha,
            record_count=1,
        ),
        observed_record_count=1,
    )
    assert gate.admitted is False
    assert "synthetic_source_rejected" in gate.reason_codes


def test_unknown_source_rejected():
    payload = [{"student_ref": "s-1"}]
    raw, sha = _bytes_for(payload)
    gate = evaluate_snapshot_bytes(
        raw,
        _approval(source_id="not-allowlisted", snapshot_sha256=sha, record_count=1),
        observed_record_count=1,
    )
    assert gate.admitted is False
    assert "source_not_in_allowlist" in gate.reason_codes


def test_domain_package_pii_rejected():
    domain = {
        "source_manifest": {
            "source_id": "mvp-attendance-over-time",
            "snapshot_sha256": "a" * 64,
            "provenance_approved": True,
            "schema_version": "epu-1",
            "record_count": 0,
            "extracted_at": _EXTRACTED.isoformat(),
        },
        "attendance_event": [{"student_ref": "s-1", "MSSV": "123"}],
        "data_quality_report": {
            "source_id": "mvp-attendance-over-time",
            "row_count": 0,
            "reject_count": 0,
        },
    }
    gate = evaluate_domain_package(
        domain, source_id="mvp-attendance-over-time", role="attendance"
    )
    assert gate.admitted is False
    assert "pii_field_present" in gate.reason_codes
    assert "MSSV" in gate.pii_fields_found


def test_domain_package_missing_tables_rejected():
    domain = {
        "source_manifest": {
            "source_id": "v59-empty-program-students",
            "snapshot_sha256": "a" * 64,
            "provenance_approved": True,
        },
        "data_quality_report": {
            "source_id": "v59-empty-program-students",
            "row_count": 0,
            "reject_count": 0,
        },
    }
    gate = evaluate_domain_package(
        domain, source_id="v59-empty-program-students", role="primary"
    )
    assert gate.admitted is False
    assert "schema_invalid" in gate.reason_codes


def test_approval_incomplete_rejected():
    with pytest.raises(Exception):
        # pydantic min_length should reject empty owner
        ApprovalArtifact(
            source_id="mvp-attendance-over-time",
            snapshot_sha256="a" * 64,
            record_count=0,
            provenance_approved=True,
            schema_version="epu-1",
            extracted_at=_EXTRACTED,
            owner="",
            usage_rights="mvp",
        )
