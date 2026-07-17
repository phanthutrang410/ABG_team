"""FairnessReport contract (H06c) — fail-closed.

Semantics: docs/04-engineering/08-data-ml-scoring-fairness-contract.md (H10) §6
và docs/03-project/10-m04-data-ml-handoff.md §3.

MVP path fail-closed: catalog EPU hiện **không có** thuộc tính audit được phê
duyệt, nên `FairnessReport` trả `status="insufficient_data"` với
`reason_code="no_approved_audit_attribute"` và **không** mang bất kỳ metric nhóm
nào. Nhánh `status="ok"` (mang group/ΔFPR/flag) chỉ hợp lệ khi có audit
attribute đã duyệt trong tương lai — không phải trên MVP path hiện tại.

Cấm `dataset_version` synthetic trên MVP path (§1). Group attrs synthetic cũ đã
bị loại; lịch sử: docs/04-engineering/09-synthetic-data-ml-fairness-contract-superseded.md.
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

#: Loại nhóm audit — chỉ dùng trong nhánh `ok` (tương lai, sau khi có audit
#: attribute được phê duyệt). Không có nhóm nào hợp lệ trên MVP path hiện tại.
GroupType = Literal["socioeconomic", "ethnicity"]

#: Lý do fail-closed (máy đọc được) — Data-ML §3 bảng reason_code.
FairnessReasonCode = Literal[
    "no_approved_audit_attribute",
    "insufficient_group_data",
]

#: Mẫu số (n_label_neg) tối thiểu để một nhóm được báo metric — M04 §8, `gt-0.1`.
SMALL_N_MIN_DENOMINATOR = 10


class GroupFairnessMetrics(BaseModel):
    """Metric của một nhóm audit đã duyệt (nhánh `ok`). Mẫu số theo M04 §7.3.

    `tpr` được phép null ngay cả khi status=ok (n_label_pos quá nhỏ để báo trung thực);
    `fpr` và `selection_rate` bắt buộc khi status=ok.
    """

    model_config = ConfigDict(extra="forbid")

    group_type: GroupType
    group: str = Field(min_length=1)
    n_total: int = Field(ge=0, description="SV đủ coverage trong nhóm (= neg + pos)")
    n_label_neg: int = Field(ge=0, description="Mẫu số FPR: label=0, đủ coverage")
    n_label_pos: int = Field(ge=0, description="Mẫu số TPR: label=1, đủ coverage")
    n_excluded_insufficient: int = Field(
        ge=0, description="SV bị loại khỏi mẫu số vì coverage insufficient (M04 §5)"
    )
    fpr: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    tpr: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    selection_rate: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    status: Literal["ok", "insufficient_group_data"]

    @model_validator(mode="after")
    def _consistent(self) -> "GroupFairnessMetrics":
        if self.n_total != self.n_label_neg + self.n_label_pos:
            raise ValueError("n_total phải bằng n_label_neg + n_label_pos (M04 §7.3)")
        if self.status == "insufficient_group_data":
            if (self.fpr, self.tpr, self.selection_rate) != (None, None, None):
                raise ValueError(
                    "nhóm insufficient_group_data phải có metric = null; "
                    "hiển thị cỡ mẫu, không hiển thị số (M04 §8)"
                )
        elif self.fpr is None or self.selection_rate is None:
            raise ValueError("nhóm status=ok phải có fpr và selection_rate")
        return self


class DeltaFpr(BaseModel):
    """ΔFPR = max − min giữa các nhóm đủ điều kiện của một group_type."""

    model_config = ConfigDict(extra="forbid")

    status: Literal["ok", "insufficient"]
    value: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    reason: Optional[str] = Field(
        default=None, description="Bắt buộc khi insufficient, vd: '< 2 nhóm đủ mẫu số'"
    )

    @model_validator(mode="after")
    def _consistent(self) -> "DeltaFpr":
        if self.status == "ok":
            if self.value is None:
                raise ValueError("delta status=ok phải có value")
        elif self.value is not None or not self.reason:
            raise ValueError("delta insufficient: value phải null và reason bắt buộc (M04 §8)")
        return self


class FairnessFlag(BaseModel):
    """Cờ nội bộ ΔFPR vượt ngưỡng demo — không phải kết luận 'unfair' production."""

    model_config = ConfigDict(extra="forbid")

    flagged: bool
    delta_fpr_threshold: float = Field(gt=0.0, le=1.0)
    triggered_group_types: List[GroupType] = Field(default_factory=list)

    @model_validator(mode="after")
    def _consistent(self) -> "FairnessFlag":
        if len(set(self.triggered_group_types)) != len(self.triggered_group_types):
            raise ValueError("triggered_group_types không được trùng")
        if self.flagged != bool(self.triggered_group_types):
            raise ValueError("flagged phải khớp với triggered_group_types")
        return self


class FairnessReport(BaseModel):
    """Report fairness (M03 output, G04 panel input) — fail-closed theo Data-ML §6.

    - `status="insufficient_data"`: trạng thái MVP duy nhất hiện tại. Bắt buộc
      `reason_code`; **cấm** mọi field mang metric (audit_attribute / groups /
      delta / flag / small_n) — không rò rỉ số theo nhóm.
    - `status="ok"`: chỉ hợp lệ khi có audit attribute đã duyệt. Bắt buộc
      `audit_attribute`, `small_n_min_denominator`, `groups` (≥1),
      `delta_fpr_by_group_type`, `fairness_flag`.
    """

    model_config = ConfigDict(extra="forbid")

    dataset_version: str = Field(min_length=1)
    model_version: str = Field(min_length=1)
    threshold_config_version: str = Field(min_length=1)
    label_rule_version: str = Field(min_length=1)
    computed_at: datetime

    status: Literal["insufficient_data", "ok"]
    reason_code: Optional[FairnessReasonCode] = None

    # Chỉ hiện diện khi status="ok" (audit attribute đã duyệt).
    audit_attribute: Optional[str] = Field(
        default=None, min_length=1, description="Tên thuộc tính audit đã được phê duyệt"
    )
    small_n_min_denominator: Optional[int] = Field(default=None, ge=1)
    groups: Optional[List[GroupFairnessMetrics]] = None
    delta_fpr_by_group_type: Optional[Dict[GroupType, DeltaFpr]] = None
    fairness_flag: Optional[FairnessFlag] = None

    @model_validator(mode="after")
    def _consistent(self) -> "FairnessReport":
        if self.dataset_version.lower().startswith("synthetic"):
            raise ValueError(
                "dataset_version synthetic bị cấm trên MVP path (Data-ML §1); "
                "chỉ snapshot EPU đã qua gate"
            )

        if self.status == "insufficient_data":
            return self._validate_insufficient()
        return self._validate_ok()

    def _validate_insufficient(self) -> "FairnessReport":
        if self.reason_code is None:
            raise ValueError("status=insufficient_data phải có reason_code (Data-ML §6)")
        metric_fields = {
            "audit_attribute": self.audit_attribute,
            "small_n_min_denominator": self.small_n_min_denominator,
            "groups": self.groups,
            "delta_fpr_by_group_type": self.delta_fpr_by_group_type,
            "fairness_flag": self.fairness_flag,
        }
        leaked = [name for name, value in metric_fields.items() if value is not None]
        if leaked:
            raise ValueError(
                "status=insufficient_data phải fail-closed: các field mang metric "
                f"phải vắng mặt, nhưng thấy {sorted(leaked)} (Data-ML §6)"
            )
        return self

    def _validate_ok(self) -> "FairnessReport":
        if self.reason_code is not None:
            raise ValueError("status=ok không được có reason_code")
        missing = [
            name
            for name, value in {
                "audit_attribute": self.audit_attribute,
                "small_n_min_denominator": self.small_n_min_denominator,
                "groups": self.groups,
                "delta_fpr_by_group_type": self.delta_fpr_by_group_type,
                "fairness_flag": self.fairness_flag,
            }.items()
            if value is None
        ]
        if missing:
            raise ValueError(f"status=ok phải có đủ metric fields, thiếu {sorted(missing)}")
        # An toàn kiểu: các field đã được xác nhận non-None ở trên.
        assert self.groups is not None
        assert self.delta_fpr_by_group_type is not None
        assert self.fairness_flag is not None
        if len(self.groups) < 1:
            raise ValueError("status=ok phải có ≥1 nhóm")

        seen: set = set()
        for g in self.groups:
            key = (g.group_type, g.group)
            if key in seen:
                raise ValueError(f"nhóm trùng lặp: {key}")
            seen.add(key)
            # Small-N rule là biconditional: status phải suy ra được từ mẫu số (M04 §8)
            if g.status == "ok" and g.n_label_neg < self.small_n_min_denominator:
                raise ValueError(
                    f"nhóm {key}: status=ok nhưng mẫu số {g.n_label_neg} "
                    f"< {self.small_n_min_denominator}"
                )
            if g.status == "insufficient_group_data" and (
                g.n_label_neg >= self.small_n_min_denominator
            ):
                raise ValueError(
                    f"nhóm {key}: mẫu số {g.n_label_neg} đủ nhưng status=insufficient"
                )

        group_types_present = {g.group_type for g in self.groups}
        delta_keys = set(self.delta_fpr_by_group_type)
        if delta_keys != group_types_present:
            raise ValueError(
                f"delta_fpr_by_group_type keys {sorted(delta_keys)} phải khớp "
                f"group_type trong groups {sorted(group_types_present)}"
            )

        for gt in self.fairness_flag.triggered_group_types:
            delta = self.delta_fpr_by_group_type.get(gt)
            if delta is None or delta.status != "ok":
                raise ValueError(f"triggered group_type '{gt}' phải có delta status=ok")
        return self
