"""H20 import gate — fail-closed checks before any `dwh` write.

Validates approval metadata, snapshot hash/count, allowlist, synthetic markers,
PII field names on the **domain payload about to be written**, and basic DQR
shape. Does not return data rows. Spec: 07-mvp-persistence-schema.md §4,
EPU §2–§5, M05b/H15 approval artifacts (decision #18).
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from datetime import datetime
from typing import List, Literal, Optional, Sequence

from pydantic import BaseModel, ConfigDict, Field

from app.ml.source_gate.gate import SOURCE_ALLOWLIST

ImportReasonCode = Literal[
    "approval_incomplete",
    "source_unapproved",
    "source_not_in_allowlist",
    "synthetic_source_rejected",
    "hash_mismatch",
    "record_count_mismatch",
    "pii_field_present",
    "schema_invalid",
    "quality_report_invalid",
    "unreadable_source",
]

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_SYNTHETIC_TEXT_MARKERS = ("synthetic",)
_SYNTHETIC_ID_RE = re.compile(r"\bSYN\d{3,}\b")
_SYNTHETIC_FIELD_PREFIX = "synth_"
_FORBIDDEN_PII_TOKENS = (
    "ho va ten",
    "ho ten",
    "hoten",
    "hovaten",
    "mssv",
    "ma so sinh vien",
    "ngay sinh",
    "ngaysinh",
    "email",
    "so dien thoai",
    "sodienthoai",
    "dien thoai",
    "sdt",
    "phone",
    "cccd",
    "cmnd",
    "token",
)

_DOMAIN_REQUIRED_KEYS_SEMESTER = (
    "source_manifest",
    "student_dimension",
    "term_grade",
    "academic_status",
    "advisor_assignment",
    "data_quality_report",
)
_DOMAIN_REQUIRED_KEYS_ATTENDANCE = (
    "source_manifest",
    "attendance_event",
    "data_quality_report",
)


class ApprovalArtifact(BaseModel):
    """Owner-approved snapshot identity (M05b / H15)."""

    model_config = ConfigDict(extra="forbid")

    source_id: str = Field(min_length=1, max_length=128)
    snapshot_sha256: str
    record_count: int = Field(ge=0)
    provenance_approved: bool
    schema_version: str = Field(min_length=1, max_length=64)
    extracted_at: datetime
    owner: str = Field(min_length=1)
    usage_rights: str = Field(min_length=1)

    @property
    def normalized_sha256(self) -> str:
        return self.snapshot_sha256.strip().lower()

    def sha256_is_wellformed(self) -> bool:
        return bool(_SHA256_RE.match(self.normalized_sha256))


class ImportGateResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: str
    admitted: bool
    reason_codes: List[ImportReasonCode] = Field(default_factory=list)
    computed_sha256: Optional[str] = None
    observed_record_count: Optional[int] = None
    pii_fields_found: List[str] = Field(default_factory=list)


def compute_sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _normalize(text: str) -> str:
    text = text.replace("đ", "d").replace("Đ", "D")
    decomposed = unicodedata.normalize("NFKD", text)
    stripped = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", " ", stripped.lower()).strip()


def _collect_keys(node: object, found: List[str], seen: set) -> None:
    if isinstance(node, dict):
        for key, value in node.items():
            if key not in seen:
                seen.add(key)
                found.append(str(key))
            _collect_keys(value, found, seen)
    elif isinstance(node, list):
        for item in node:
            _collect_keys(item, found, seen)


def _find_pii_fields(field_names: Sequence[str]) -> List[str]:
    found: List[str] = []
    for name in field_names:
        norm = _normalize(name)
        if any(token in norm for token in _FORBIDDEN_PII_TOKENS):
            found.append(name)
    return found


def _looks_synthetic(raw_text: str, field_names: Sequence[str]) -> bool:
    lowered = raw_text.lower()
    if any(marker in lowered for marker in _SYNTHETIC_TEXT_MARKERS):
        return True
    if _SYNTHETIC_ID_RE.search(raw_text):
        return True
    return any(name.lower().startswith(_SYNTHETIC_FIELD_PREFIX) for name in field_names)


def evaluate_approval(approval: ApprovalArtifact) -> List[ImportReasonCode]:
    reasons: List[ImportReasonCode] = []
    if not approval.owner.strip() or not approval.usage_rights.strip():
        reasons.append("approval_incomplete")
    if not approval.provenance_approved:
        reasons.append("source_unapproved")
    if approval.source_id not in SOURCE_ALLOWLIST:
        reasons.append("source_not_in_allowlist")
    if "synthetic" in approval.source_id.lower():
        reasons.append("synthetic_source_rejected")
    return reasons


def evaluate_snapshot_bytes(
    raw_bytes: bytes,
    approval: ApprovalArtifact,
    *,
    observed_record_count: int,
) -> ImportGateResult:
    """Gate raw snapshot bytes against approval hash/count (+ allowlist/approval)."""
    reasons = list(evaluate_approval(approval))
    computed = compute_sha256_bytes(raw_bytes)
    try:
        raw_text = raw_bytes.decode("utf-8")
    except UnicodeDecodeError:
        return ImportGateResult(
            source_id=approval.source_id,
            admitted=False,
            reason_codes=["unreadable_source"],
            computed_sha256=computed,
        )

    field_names: List[str] = []
    try:
        payload = json.loads(raw_text)
        _collect_keys(payload, field_names, set())
    except json.JSONDecodeError:
        return ImportGateResult(
            source_id=approval.source_id,
            admitted=False,
            reason_codes=["unreadable_source"],
            computed_sha256=computed,
        )

    if _looks_synthetic(raw_text, field_names):
        reasons.append("synthetic_source_rejected")
    if not approval.sha256_is_wellformed() or computed != approval.normalized_sha256:
        reasons.append("hash_mismatch")
    if observed_record_count != approval.record_count:
        reasons.append("record_count_mismatch")

    # Deduplicate while preserving order.
    deduped: List[ImportReasonCode] = []
    for code in reasons:
        if code not in deduped:
            deduped.append(code)

    return ImportGateResult(
        source_id=approval.source_id,
        admitted=not deduped,
        reason_codes=deduped,
        computed_sha256=computed,
        observed_record_count=observed_record_count,
    )


def evaluate_domain_package(
    domain: dict,
    *,
    source_id: str,
    role: Literal["primary", "attendance"],
) -> ImportGateResult:
    """Fail-closed checks on the M06 domain package about to be persisted."""
    reasons: List[ImportReasonCode] = []
    required = (
        _DOMAIN_REQUIRED_KEYS_ATTENDANCE
        if role == "attendance"
        else _DOMAIN_REQUIRED_KEYS_SEMESTER
    )
    missing = [k for k in required if k not in domain]
    if missing:
        reasons.append("schema_invalid")

    field_names: List[str] = []
    _collect_keys(domain, field_names, set())
    pii = _find_pii_fields(field_names)
    if pii:
        reasons.append("pii_field_present")

    raw_text = json.dumps(domain, ensure_ascii=False, default=str)
    if _looks_synthetic(raw_text, field_names):
        reasons.append("synthetic_source_rejected")

    manifest = domain.get("source_manifest")
    if not isinstance(manifest, dict):
        reasons.append("schema_invalid")
    else:
        if manifest.get("source_id") != source_id:
            reasons.append("schema_invalid")
        if not manifest.get("provenance_approved"):
            reasons.append("source_unapproved")
        sha = str(manifest.get("snapshot_sha256") or "").strip().lower()
        if not _SHA256_RE.match(sha):
            reasons.append("schema_invalid")

    report = domain.get("data_quality_report")
    if not isinstance(report, dict):
        reasons.append("quality_report_invalid")
    else:
        row_count = report.get("row_count")
        reject_count = report.get("reject_count")
        if not isinstance(row_count, int) or row_count < 0:
            reasons.append("quality_report_invalid")
        if not isinstance(reject_count, int) or reject_count < 0:
            reasons.append("quality_report_invalid")
        if report.get("source_id") != source_id:
            reasons.append("quality_report_invalid")

    deduped: List[ImportReasonCode] = []
    for code in reasons:
        if code not in deduped:
            deduped.append(code)

    return ImportGateResult(
        source_id=source_id,
        admitted=not deduped,
        reason_codes=deduped,
        pii_fields_found=pii,
    )
