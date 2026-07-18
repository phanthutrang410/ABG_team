"""H34a — weekly report materializer (backend-internal, provider-independent).

`materialize_report` only reads the already-computed `DeltaItem` list and
the durable `CaseRepository` — it never calls OpenAI/any LLM and never
recomputes scoring, so counts/newness stay deterministic and reproducible
from the same inputs (architecture doc 13 §8.1, brief `H34a`).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Literal, Optional

from app.weekly.cases_durable import CaseRepository
from app.weekly.delta import DeltaItem

ReportStatus = Literal["ok", "empty", "stale", "failed", "baseline_unavailable"]


@dataclass(frozen=True)
class WeeklyReport:
    """Report envelope — no `student_ref`/PII at this level (only aggregates)."""

    report_id: str
    snapshot_id: Optional[str]
    branch: str
    aggregates: Dict[str, int]
    limitations: List[str] = field(default_factory=list)
    status: ReportStatus = "ok"


def _zero_aggregates(total_active: int) -> Dict[str, int]:
    return {"new": 0, "ongoing": 0, "changed": 0, "total_active": total_active}


def materialize_report(
    repo: CaseRepository,
    deltas: List[DeltaItem],
    snapshot_id: Optional[str],
    branch: str,
    *,
    stale: bool = False,
    workflow_failure_reason: Optional[str] = None,
) -> WeeklyReport:
    """Exact aggregates from `deltas`; `total_active` from durable episodes.

    `stale` / `workflow_failure_reason` are caller-supplied signals from the
    surrounding weekly run (freshness / step failure) — this function does
    not infer them from the delta list, since a successful run over stale
    source data still produces a well-formed delta.
    """
    report_id = f"wr-{snapshot_id or 'none'}-{branch}"
    total_active = len(repo.list_active(branch=branch))

    if workflow_failure_reason:
        return WeeklyReport(
            report_id=report_id,
            snapshot_id=snapshot_id,
            branch=branch,
            aggregates=_zero_aggregates(total_active),
            limitations=[workflow_failure_reason],
            status="failed",
        )

    if not deltas:
        return WeeklyReport(
            report_id=report_id,
            snapshot_id=snapshot_id,
            branch=branch,
            aggregates=_zero_aggregates(total_active),
            limitations=[],
            status="empty",
        )

    new = sum(1 for d in deltas if d.delta_type in ("newly_detected", "resurfaced"))
    ongoing = sum(1 for d in deltas if d.delta_type == "ongoing")
    changed = sum(1 for d in deltas if d.delta_type == "changed")
    is_baseline = any(d.delta_type == "initial_baseline" for d in deltas)
    comparison_unavailable_n = sum(1 for d in deltas if d.delta_type == "comparison_unavailable")

    limitations: List[str] = []
    if comparison_unavailable_n:
        limitations.append("comparison_unavailable")

    if is_baseline:
        status: ReportStatus = "baseline_unavailable"
    elif stale:
        status = "stale"
        limitations.append("stale_snapshot")
    else:
        status = "ok"

    return WeeklyReport(
        report_id=report_id,
        snapshot_id=snapshot_id,
        branch=branch,
        aggregates={
            "new": new,
            "ongoing": ongoing,
            "changed": changed,
            "total_active": total_active,
        },
        limitations=limitations,
        status=status,
    )
