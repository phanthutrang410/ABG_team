"""Export M05b raw V59 → git-safe M06 semester domain_package.json.

Requires local raw file (outside git). Does not write MSSV/map/PII.

Usage (repo root):
  set SILENT_SHIELD_SEMESTER_SOURCE_PATH=...\\v59-empty-program-students.json
  python scripts/export_approved_semester_domain.py

Or:
  python scripts/export_approved_semester_domain.py --source PATH
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND = REPO_ROOT / "backend"
OUT_PATH = REPO_ROOT / "data" / "approved" / "semester" / "domain_package.json"
DEFAULT_RAW = (
    REPO_ROOT
    / "reference-Learning-Analytics-AI"
    / "backend"
    / "db"
    / "v59-empty-program-students.json"
)
SEMESTER_SOURCE_ID = "v59-empty-program-students"
# Provenance of upstream raw (M05b); embedded in source_manifest, not package gate hash.
RAW_PROVENANCE_SHA256 = "34a53298df3dafd4d248496e75fbc10d95f997b76d0a7e6566e04ea97c367c66"
RAW_RECORD_COUNT = 460
EXTRACTED_AT = datetime(2026, 7, 18, 0, 5, tzinfo=timezone.utc)

_FORBIDDEN_TOKENS = (
    "mssv",
    "ho va ten",
    "ho ten",
    "email",
    "so dien thoai",
    "sdt",
    "token",
    "ngay sinh",
)


def _ensure_backend_on_path() -> None:
    if str(BACKEND) not in sys.path:
        sys.path.insert(0, str(BACKEND))


def _collect_keys(node: object, found: list[str]) -> None:
    if isinstance(node, dict):
        for key, value in node.items():
            found.append(str(key))
            _collect_keys(value, found)
    elif isinstance(node, list):
        for item in node:
            _collect_keys(item, found)


def _assert_no_pii(domain: dict) -> None:
    keys: list[str] = []
    _collect_keys(domain, keys)
    for key in keys:
        norm = key.lower().replace("đ", "d")
        for token in _FORBIDDEN_TOKENS:
            if token in norm:
                raise SystemExit(f"PII/token field name detected: {key!r}")
    blob = json.dumps(domain, ensure_ascii=False)
    for banned in ("Họ và tên", "MSSV", "Số ĐT", "@gmail.com", "@yahoo"):
        if banned in blob:
            raise SystemExit(f"Forbidden substring in domain package: {banned!r}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        type=Path,
        default=None,
        help="Raw V59 JSON path (default: env SILENT_SHIELD_SEMESTER_SOURCE_PATH or reference clone)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=OUT_PATH,
        help=f"Output domain package (default: {OUT_PATH})",
    )
    args = parser.parse_args(argv)

    env_path = os.environ.get("SILENT_SHIELD_SEMESTER_SOURCE_PATH", "").strip()
    source = args.source
    if source is None:
        source = Path(env_path) if env_path else DEFAULT_RAW
    if not source.is_file():
        raise SystemExit(
            f"Raw semester source not found: {source}\n"
            "Set SILENT_SHIELD_SEMESTER_SOURCE_PATH or pass --source."
        )

    raw_bytes = source.read_bytes()
    raw_sha = hashlib.sha256(raw_bytes).hexdigest()
    if raw_sha != RAW_PROVENANCE_SHA256:
        raise SystemExit(
            f"Raw SHA mismatch: got {raw_sha}, expected M05b {RAW_PROVENANCE_SHA256}"
        )
    payload = json.loads(raw_bytes.decode("utf-8"))
    if not isinstance(payload, list) or len(payload) != RAW_RECORD_COUNT:
        raise SystemExit(
            f"Raw record_count mismatch: got {len(payload) if isinstance(payload, list) else type(payload)}"
        )

    _ensure_backend_on_path()
    from app.dwh.semester_adapt import adapt_v59_records
    from app.ml.domain.models import DomainSourceManifest
    from app.ml.domain.transform import build_semester_dataset

    records = adapt_v59_records(payload)
    manifest = DomainSourceManifest(
        source_id=SEMESTER_SOURCE_ID,
        snapshot_sha256=RAW_PROVENANCE_SHA256,
        provenance_approved=True,
        schema_version="epu-1",
        record_count=RAW_RECORD_COUNT,
        extracted_at=EXTRACTED_AT,
    )
    dataset = build_semester_dataset(
        records,
        manifest=manifest,
        report_version="m06-semester-1",
        generated_at=EXTRACTED_AT,
    )
    domain = {
        "source_manifest": dataset.source_manifest.model_dump(mode="json"),
        "student_dimension": [r.model_dump(mode="json") for r in dataset.student_dimension],
        "term_grade": [r.model_dump(mode="json") for r in dataset.term_grade],
        "academic_status": [r.model_dump(mode="json") for r in dataset.academic_status],
        "advisor_assignment": [r.model_dump(mode="json") for r in dataset.advisor_assignment],
        "data_quality_report": dataset.data_quality_report.model_dump(mode="json"),
    }
    _assert_no_pii(domain)

    # Deterministic bytes for stable package SHA (gate hash ≠ raw provenance hash).
    text = json.dumps(domain, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    out_bytes = text.encode("utf-8")
    package_sha = hashlib.sha256(out_bytes).hexdigest()

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(out_bytes)

    print(
        json.dumps(
            {
                "out": str(args.out),
                "package_sha256": package_sha,
                "raw_provenance_sha256": RAW_PROVENANCE_SHA256,
                "student_dimension": len(domain["student_dimension"]),
                "term_grade": len(domain["term_grade"]),
                "academic_status": len(domain["academic_status"]),
                "advisor_assignment": len(domain["advisor_assignment"]),
                "dqr_row_count": domain["data_quality_report"]["row_count"],
                "dqr_reject_count": domain["data_quality_report"]["reject_count"],
                "next": "Update SEMESTER_APPROVAL.snapshot_sha256 in importer.py + semester/APPROVAL.md",
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
