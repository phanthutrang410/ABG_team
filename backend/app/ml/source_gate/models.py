"""Contract models cho source gate (M05a).

Semantics: docs/04-engineering/04-epu-data-integration-contract.md §2–§3 và
docs/04-engineering/08-data-ml-scoring-fairness-contract.md §7.

`SourceManifest` ở đây là manifest do data owner biên soạn (input của gate),
phân biệt với bảng persistence SQLAlchemy `app/dwh/models.py::SourceManifest`
(nơi lưu sau khi qua gate + H20). Trường trùng nghĩa được giữ tên nhất quán.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

#: Lý do fail-closed (máy đọc được). Đồng bộ với reason_codes ở EPU §2 / Data-ML §7.
GateReasonCode = Literal[
    "unreadable_source",
    "source_not_in_allowlist",
    "synthetic_source_rejected",
    "source_unapproved",
    "hash_mismatch",
    "record_count_mismatch",
    "pii_field_present",
]

SourceRole = Literal["primary", "regression", "attendance"]


class SourceManifest(BaseModel):
    """Manifest provenance do data owner cung cấp — input của gate.

    `provenance_approved=True` là điều kiện cần (không đủ): gate CODE (M05a) kiểm
    tra cờ này; cờ được bật khi có artifact duyệt (M05b/H15 — decision #18: team
    approver MVP demo). M05a Done ≠ nguồn đã duyệt.
    """

    model_config = ConfigDict(extra="forbid")

    source_id: str = Field(min_length=1, max_length=128)
    snapshot_sha256: str = Field(description="Hash snapshot (64 hex thường)")
    record_count: int = Field(ge=0)
    provenance_approved: bool
    schema_version: str = Field(min_length=1, max_length=64)
    extracted_at: datetime
    owner: str = Field(min_length=1, description="Định danh data owner (không phải PII SV)")
    usage_rights: str = Field(min_length=1, description="Quyền sử dụng đã được cấp")

    @property
    def normalized_sha256(self) -> str:
        return self.snapshot_sha256.strip().lower()

    def sha256_is_wellformed(self) -> bool:
        return bool(_SHA256_RE.match(self.normalized_sha256))


class GateResult(BaseModel):
    """Kết quả gate — fail-closed. `admitted=True` chỉ khi reason_codes rỗng.

    Không mang bất kỳ hàng dữ liệu nào: gate chỉ quyết định admission và phát
    hành lý do; transform/quality-report đầy đủ thuộc M06.
    """

    model_config = ConfigDict(extra="forbid")

    source_id: str
    admitted: bool
    reason_codes: List[GateReasonCode] = Field(default_factory=list)
    role: Optional[SourceRole] = None
    computed_sha256: Optional[str] = None
    observed_record_count: Optional[int] = None
    pii_fields_found: List[str] = Field(default_factory=list)
