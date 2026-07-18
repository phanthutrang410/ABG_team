"""Fail-closed source gate (M05a).

Quyết định một file nguồn ứng viên có được nạp vào pipeline hay không, TRƯỚC
M06/H20. Mọi lớp fail-closed: bất kỳ lỗi nào ⇒ `admitted=False`, không xuất
hàng dữ liệu. Spec: EPU contract §1–§3, Data-ML §7, M04 §2.

M05a chỉ là code gate. `admitted=True` trong unit test chứng minh logic gate,
KHÔNG đồng nghĩa snapshot đã được data owner duyệt (đó là M05b + artifact).
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from pathlib import Path
from typing import Dict, List

from app.ml.source_gate.models import GateReasonCode, GateResult, SourceManifest, SourceRole

#: Allowlist source_id → vai trò. EPU §1 + decision #18: v59-empty primary
#: semester; mvp-attendance-over-time = attendance; epu_data = regression.
#: Tên file không chứng minh provenance — allowlist chỉ chặn nguồn lạ.
SOURCE_ALLOWLIST: Dict[str, SourceRole] = {
    "v59-empty-program-students": "primary",
    "epu_data": "regression",
    "mvp-attendance-over-time": "attendance",
}

#: Marker nội dung synthetic (case-insensitive). Không dùng định danh legacy đầy
#: đủ (đã bị M01 loại) — phát hiện bằng dấu hiệu generic để tránh tái nhập.
_SYNTHETIC_TEXT_MARKERS = ("synthetic",)
_SYNTHETIC_ID_RE = re.compile(r"\bSYN\d{3,}\b")
_SYNTHETIC_FIELD_PREFIX = "synth_"

#: Trường PII bị cấm xuất (chuẩn hóa: bỏ dấu, lower, gộp khoảng trắng).
#: Match nếu tên trường CHỨA một trong các token này. Pseudonym (`student_ref`,
#: `advisor_ref`) không khớp và được phép.
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


def compute_sha256(path: Path) -> str:
    """SHA-256 hex của toàn bộ byte file (determinism-friendly)."""
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _normalize(text: str) -> str:
    # `đ/Đ` là ký tự riêng, không tách dấu bằng NFKD — map tay sang `d`.
    text = text.replace("đ", "d").replace("Đ", "D")
    decomposed = unicodedata.normalize("NFKD", text)
    stripped = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    lowered = stripped.lower()
    return re.sub(r"[^a-z0-9]+", " ", lowered).strip()


def _collect_field_names(payload: object) -> List[str]:
    """Union tên trường ở cấp bản ghi (list dict, hoặc dict có mảng dict con)."""
    names: List[str] = []
    seen: set = set()

    def _add_keys(record: object) -> None:
        if isinstance(record, dict):
            for key in record:
                if key not in seen:
                    seen.add(key)
                    names.append(key)

    if isinstance(payload, list):
        for item in payload:
            _add_keys(item)
    elif isinstance(payload, dict):
        _add_keys(payload)
        for value in payload.values():
            if isinstance(value, list):
                for item in value:
                    _add_keys(item)
    return names


def _count_records(payload: object) -> int:
    if isinstance(payload, list):
        return len(payload)
    if isinstance(payload, dict):
        # Snapshot dạng {"data": [...]} — đếm mảng dict con lớn nhất.
        list_lengths = [len(v) for v in payload.values() if isinstance(v, list)]
        if list_lengths:
            return max(list_lengths)
        return 1
    return 0


def _find_pii_fields(field_names: List[str]) -> List[str]:
    found: List[str] = []
    for name in field_names:
        norm = _normalize(name)
        if any(token in norm for token in _FORBIDDEN_PII_TOKENS):
            found.append(name)
    return found


def _looks_synthetic(raw_text: str, field_names: List[str]) -> bool:
    lowered = raw_text.lower()
    if any(marker in lowered for marker in _SYNTHETIC_TEXT_MARKERS):
        return True
    if _SYNTHETIC_ID_RE.search(raw_text):
        return True
    return any(name.lower().startswith(_SYNTHETIC_FIELD_PREFIX) for name in field_names)


def evaluate_source(data_path: Path, manifest: SourceManifest) -> GateResult:
    """Chạy toàn bộ lớp gate fail-closed trên (file, manifest).

    Thu thập mọi reason_code áp dụng được để báo cáo, nhưng `admitted=True` chỉ
    khi không có reason_code nào. Không trả về hàng dữ liệu.
    """
    reasons: List[GateReasonCode] = []
    role = SOURCE_ALLOWLIST.get(manifest.source_id)

    # Lớp 0 — đọc được và parse được JSON. Không đọc được ⇒ fail-closed ngay.
    try:
        raw_bytes = data_path.read_bytes()
    except OSError:
        return GateResult(
            source_id=manifest.source_id,
            admitted=False,
            reason_codes=["unreadable_source"],
            role=role,
        )

    computed_sha256 = hashlib.sha256(raw_bytes).hexdigest()
    try:
        raw_text = raw_bytes.decode("utf-8")
        payload = json.loads(raw_text)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return GateResult(
            source_id=manifest.source_id,
            admitted=False,
            reason_codes=["unreadable_source"],
            role=role,
            computed_sha256=computed_sha256,
        )

    field_names = _collect_field_names(payload)
    observed_count = _count_records(payload)
    pii_fields = _find_pii_fields(field_names)

    # Lớp 1 — register/allowlist.
    if role is None:
        reasons.append("source_not_in_allowlist")

    # Lớp 2 — từ chối synthetic theo tên + nội dung.
    if _looks_synthetic(raw_text, field_names):
        reasons.append("synthetic_source_rejected")

    # Lớp 3 — provenance approval (M05a↔M05b boundary).
    if not manifest.provenance_approved:
        reasons.append("source_unapproved")

    # Lớp 4 — hash khớp manifest.
    if not manifest.sha256_is_wellformed() or computed_sha256 != manifest.normalized_sha256:
        reasons.append("hash_mismatch")

    # Lớp 5 — record count khớp manifest.
    if observed_count != manifest.record_count:
        reasons.append("record_count_mismatch")

    # Lớp 6 — không có trường PII.
    if pii_fields:
        reasons.append("pii_field_present")

    return GateResult(
        source_id=manifest.source_id,
        admitted=not reasons,
        reason_codes=reasons,
        role=role,
        computed_sha256=computed_sha256,
        observed_record_count=observed_count,
        pii_fields_found=pii_fields,
    )
