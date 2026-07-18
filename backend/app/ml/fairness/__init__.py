"""M03 — fairness gate: FPR / ΔFPR / N (Data-ML §6)."""

from __future__ import annotations

from app.ml.fairness.gate import (
    APPROVED_AUDIT_ATTRIBUTES,
    DEFAULT_DELTA_FPR_THRESHOLD,
    AuditRecord,
    build_fairness_report,
    compute_delta_fpr,
    compute_fairness_flag,
    compute_group_metrics,
)

__all__ = [
    "APPROVED_AUDIT_ATTRIBUTES",
    "DEFAULT_DELTA_FPR_THRESHOLD",
    "AuditRecord",
    "build_fairness_report",
    "compute_delta_fpr",
    "compute_fairness_flag",
    "compute_group_metrics",
]
