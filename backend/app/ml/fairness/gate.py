"""M03 — fairness gate: FPR / ΔFPR / N computation (Data-ML §6, M04 §3).

Fail-closed entrypoint `build_fairness_report`: the EPU catalog currently has
**no** approved audit attribute, so on the MVP path this always returns
`status="insufficient_data"` — the formulas below are the consumer this gate
unlocks once a data owner approves an attribute (`APPROVED_AUDIT_ATTRIBUTES`).

Group labels must come from a pre-approved external audit slice — this
module never derives a group from department/major/class/gender (proxy ban,
Data-ML §6) and never imports `ScoringFeatures` / `NormalizedStudentRecord`;
the audit slice stays separate from scoring/public case (Data-ML §6, tách
tuyệt đối audit slice ↔ scoring).

`academic_status.is_dropout_outcome` labels feeding `AuditRecord.label` are
evaluation-only (Data-ML §5) — never scoring input.
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Literal, Optional, Sequence

from app.contracts.fairness import (
    SMALL_N_MIN_DENOMINATOR,
    DeltaFpr,
    FairnessFlag,
    FairnessReport,
    GroupFairnessMetrics,
    GroupType,
)

#: EPU catalog audit attributes with signed data-owner approval (Data-ML §6).
#: Empty on the MVP path — every entry must map to an approval artifact kept
#: outside this repo before being added here. Do not add proxies (khoa/ngành/
#: lớp/giới tính) — see Data-ML §6.
APPROVED_AUDIT_ATTRIBUTES: Dict[str, GroupType] = {}

DEFAULT_DELTA_FPR_THRESHOLD = 0.1

Label = Literal["true", "false", "unknown"]


class AuditRecord:
    """One student's audit-slice row: group label + evaluation label + flag.

    `label="unknown"` and `coverage_sufficient=False` are excluded from every
    FPR/TPR/selection_rate denominator (Data-ML §5); the latter is counted in
    `n_excluded_insufficient` instead.
    """

    __slots__ = ("student_ref", "group", "label", "flagged", "coverage_sufficient")

    def __init__(
        self,
        *,
        student_ref: str,
        group: str,
        label: Label,
        flagged: bool,
        coverage_sufficient: bool = True,
    ) -> None:
        self.student_ref = student_ref
        self.group = group
        self.label = label
        self.flagged = flagged
        self.coverage_sufficient = coverage_sufficient


def compute_group_metrics(
    group_type: GroupType,
    group: str,
    records: Sequence[AuditRecord],
    *,
    small_n_min_denominator: int = SMALL_N_MIN_DENOMINATOR,
) -> GroupFairnessMetrics:
    """FPR/TPR/selection_rate for one group (Data-ML §5–§6).

    FPR = flagged / n_label_neg over `label="false"`; TPR = flagged /
    n_label_pos over `label="true"`; both computed only on the
    coverage-sufficient, non-`unknown` eligible population. Small-N gate is
    on `n_label_neg` (the FPR denominator) per Data-ML §6.
    """
    own = [r for r in records if r.group == group]
    excluded = sum(1 for r in own if not r.coverage_sufficient)
    eligible = [r for r in own if r.coverage_sufficient and r.label != "unknown"]
    negatives = [r for r in eligible if r.label == "false"]
    positives = [r for r in eligible if r.label == "true"]
    n_label_neg = len(negatives)
    n_label_pos = len(positives)
    n_total = n_label_neg + n_label_pos

    if n_label_neg < small_n_min_denominator:
        return GroupFairnessMetrics(
            group_type=group_type,
            group=group,
            n_total=n_total,
            n_label_neg=n_label_neg,
            n_label_pos=n_label_pos,
            n_excluded_insufficient=excluded,
            fpr=None,
            tpr=None,
            selection_rate=None,
            status="insufficient_group_data",
        )

    fpr = sum(1 for r in negatives if r.flagged) / n_label_neg
    tpr = sum(1 for r in positives if r.flagged) / n_label_pos if n_label_pos else None
    selection_rate = sum(1 for r in eligible if r.flagged) / n_total
    return GroupFairnessMetrics(
        group_type=group_type,
        group=group,
        n_total=n_total,
        n_label_neg=n_label_neg,
        n_label_pos=n_label_pos,
        n_excluded_insufficient=excluded,
        fpr=round(fpr, 6),
        tpr=round(tpr, 6) if tpr is not None else None,
        selection_rate=round(selection_rate, 6),
        status="ok",
    )


def compute_delta_fpr(groups: Sequence[GroupFairnessMetrics]) -> DeltaFpr:
    """ΔFPR = max − min FPR among `status="ok"` groups of one `group_type`."""
    ok_fprs = [g.fpr for g in groups if g.status == "ok" and g.fpr is not None]
    if len(ok_fprs) < 2:
        return DeltaFpr(status="insufficient", value=None, reason="< 2 nhóm đủ mẫu số")
    return DeltaFpr(status="ok", value=round(max(ok_fprs) - min(ok_fprs), 6), reason=None)


def compute_fairness_flag(
    delta_by_type: Dict[GroupType, DeltaFpr],
    *,
    threshold: float = DEFAULT_DELTA_FPR_THRESHOLD,
) -> FairnessFlag:
    """Internal ΔFPR-over-threshold flag — a demo signal, not a production verdict."""
    triggered: List[GroupType] = sorted(
        gt
        for gt, delta in delta_by_type.items()
        if delta.status == "ok" and delta.value is not None and delta.value > threshold
    )
    return FairnessFlag(
        flagged=bool(triggered), delta_fpr_threshold=threshold, triggered_group_types=triggered
    )


def build_fairness_report(
    *,
    dataset_version: str,
    model_version: str,
    threshold_config_version: str,
    label_rule_version: str,
    computed_at: datetime,
    audit_attribute: Optional[str] = None,
    records: Optional[Sequence[AuditRecord]] = None,
    small_n_min_denominator: int = SMALL_N_MIN_DENOMINATOR,
    delta_fpr_threshold: float = DEFAULT_DELTA_FPR_THRESHOLD,
) -> FairnessReport:
    """Fail-closed fairness gate (Data-ML §6).

    Returns `insufficient_data(no_approved_audit_attribute)` unless
    `audit_attribute` is a key of `APPROVED_AUDIT_ATTRIBUTES` — always true on
    the MVP path today, since that catalog is empty.
    """
    if audit_attribute is None or audit_attribute not in APPROVED_AUDIT_ATTRIBUTES:
        return FairnessReport(
            dataset_version=dataset_version,
            model_version=model_version,
            threshold_config_version=threshold_config_version,
            label_rule_version=label_rule_version,
            computed_at=computed_at,
            status="insufficient_data",
            reason_code="no_approved_audit_attribute",
        )

    group_type = APPROVED_AUDIT_ATTRIBUTES[audit_attribute]
    records = records or []
    groups_present = sorted({r.group for r in records})
    if not groups_present:
        raise ValueError(
            "build_fairness_report: audit_attribute approved but no group records supplied"
        )
    groups = [
        compute_group_metrics(
            group_type, g, records, small_n_min_denominator=small_n_min_denominator
        )
        for g in groups_present
    ]
    delta = compute_delta_fpr(groups)
    flag = compute_fairness_flag({group_type: delta}, threshold=delta_fpr_threshold)
    return FairnessReport(
        dataset_version=dataset_version,
        model_version=model_version,
        threshold_config_version=threshold_config_version,
        label_rule_version=label_rule_version,
        computed_at=computed_at,
        status="ok",
        audit_attribute=audit_attribute,
        small_n_min_denominator=small_n_min_denominator,
        groups=groups,
        delta_fpr_by_group_type={group_type: delta},
        fairness_flag=flag,
    )
