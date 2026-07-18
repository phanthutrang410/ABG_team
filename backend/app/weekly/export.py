"""H38 — safe report export: aggregate CSV (no identifiers) or one-case CSV.

BRD §9 / Ethics data-minimization boundary: there is no bulk-identifiable
export anywhere in this module. `export_aggregate_csv` only ever reads
`WeeklyReport.aggregates` (counts). `export_case` resolves exactly one
durable episode, gated by `can_access_case` (server-side scope only), and
always stamps a watermark (`actor_id` + timestamp) plus one
`record_access_event` — never a background/email delivery path.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional

from app.auth.principal import Principal, record_access_event
from app.auth.scope import can_access_case
from app.weekly.cases_durable import CaseRepository
from app.weekly.report import WeeklyReport

#: Aggregate export never exposes anything beyond these deterministic counts.
_AGGREGATE_FIELDS = ("new", "ongoing", "changed", "total_active")

#: Leading characters a spreadsheet app may interpret as a formula/command.
_CSV_INJECTION_LEADS = ("=", "+", "-", "@", "\t", "\r")


class ExportError(Exception):
    """Rejected export request — caller maps this to an HTTP error."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def _csv_escape(value: str) -> str:
    """Defense-in-depth CSV/formula-injection escaping for one cell value."""
    text = str(value)
    needs_quotes = any(ch in text for ch in (",", '"', "\n", "\r"))
    if text and text[0] in _CSV_INJECTION_LEADS:
        text = "'" + text
        needs_quotes = True
    if needs_quotes:
        text = '"' + text.replace('"', '""') + '"'
    return text


def _csv_row(*cells: str) -> str:
    return ",".join(_csv_escape(c) for c in cells)


def export_aggregate_csv(report: WeeklyReport) -> str:
    """CSV with counts only — never a student ref/identifier column."""
    lines: List[str] = [_csv_row("report_id", "branch", "status", "metric", "count")]
    for field in _AGGREGATE_FIELDS:
        lines.append(
            _csv_row(
                report.report_id,
                report.branch,
                report.status,
                field,
                str(report.aggregates.get(field, 0)),
            )
        )
    return "\r\n".join(lines) + "\r\n"


@dataclass(frozen=True)
class CaseExportWatermark:
    """Who exported this one-case projection, and when — audit-visible."""

    actor_id: str
    exported_at: datetime


@dataclass(frozen=True)
class CaseExportResult:
    """One episode's safe projection — no name/email/phone/model_score."""

    episode_id: str
    student_ref: str
    branch: str
    case_state: str
    advisor_ref: Optional[str]
    watermark: CaseExportWatermark


def export_case(
    repo: CaseRepository,
    episode_id: str,
    principal: Principal,
) -> CaseExportResult:
    """Resolve exactly one episode, scope-gated, with a fresh watermark+audit."""
    episode = repo.get(episode_id)
    if episode is None:
        raise ExportError("not_found", f"no episode {episode_id}")
    if not can_access_case(principal, episode.advisor_ref, episode.org_scope or ""):
        raise ExportError("forbidden", "principal not authorized for this case")

    now = datetime.now(timezone.utc)
    record_access_event(
        actor_id=principal.actor_id,
        role=principal.active_role,
        action="export_case",
        resource_handle=episode_id,
    )
    return CaseExportResult(
        episode_id=episode.episode_id,
        student_ref=episode.student_ref,
        branch=episode.branch,
        case_state=episode.state,
        advisor_ref=episode.advisor_ref,
        watermark=CaseExportWatermark(actor_id=principal.actor_id, exported_at=now),
    )


def export_case_csv(result: CaseExportResult) -> str:
    lines = [
        _csv_row("field", "value"),
        _csv_row("episode_id", result.episode_id),
        _csv_row("student_ref", result.student_ref),
        _csv_row("branch", result.branch),
        _csv_row("case_state", result.case_state),
        _csv_row("advisor_ref", result.advisor_ref or ""),
        _csv_row("watermark_actor_id", result.watermark.actor_id),
        _csv_row("watermark_exported_at", result.watermark.exported_at.isoformat()),
    ]
    return "\r\n".join(lines) + "\r\n"


#: Any export `kind` outside this set — including any bulk/identifiable
#: alias — must be rejected with 400 before touching the repository.
ALLOWED_EXPORT_KINDS = frozenset({"aggregate", "case"})

_BULK_ALIAS_PATTERN = re.compile(r"(?i)bulk|all[_-]?students|full[_-]?list")


def validate_export_kind(kind: str, *, episode_id: Optional[str]) -> None:
    """Fail closed on bulk/unknown kinds or a case export missing its handle."""
    normalized = (kind or "").strip().lower()
    if normalized not in ALLOWED_EXPORT_KINDS or _BULK_ALIAS_PATTERN.search(normalized):
        raise ExportError("invalid_kind", "kind must be 'aggregate' or 'case'")
    if normalized == "case" and not (episode_id or "").strip():
        raise ExportError("missing_episode_id", "kind=case requires episode_id")
