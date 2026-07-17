"""FairnessReport contract (H06c).

Semantics: docs/04-engineering/05-data-ml-fairness-contract.md (M04) §7-§8.
Chỉ tính trên dữ liệu synthetic; thuộc tính nhóm không tham gia scoring (FR-09).
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

GroupType = Literal["socioeconomic", "ethnicity"]

#: Mẫu số (n_label_neg) tối thiểu để một nhóm được báo metric — M04 §8, `gt-0.1`.
SMALL_N_MIN_DENOMINATOR = 10


class GroupFairnessMetrics(BaseModel):
    """Metric của một nhóm synthetic. Mẫu số theo M04 §7.3.

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
    """Report fairness trên synthetic — output của M03, input của G04 panel."""

    model_config = ConfigDict(extra="forbid")

    dataset_version: str = Field(min_length=1)
    model_version: str = Field(min_length=1)
    threshold_config_version: str = Field(min_length=1)
    label_rule_version: str = Field(min_length=1)
    computed_at: datetime
    synthetic: Literal[True] = Field(
        description="Hằng số trong MVP: mọi metric phải mang nhãn synthetic (PRD §2)"
    )
    small_n_min_denominator: int = Field(ge=1)
    groups: List[GroupFairnessMetrics] = Field(min_length=1)
    delta_fpr_by_group_type: Dict[GroupType, DeltaFpr]
    fairness_flag: FairnessFlag

    @model_validator(mode="after")
    def _consistent(self) -> "FairnessReport":
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
                raise ValueError(
                    f"triggered group_type '{gt}' phải có delta status=ok"
                )
        return self
