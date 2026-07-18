"""Shared in-memory weekly state (MVP) — one `CaseRepository`/report/briefing.

`app.weekly.router` (H34 light wiring), `app.weekly.export` (H38) and
`app.weekly.advisor_draft_v2` (H35) all need to see the *same* durable
episode ledger and the same "latest materialized report" pointer per
branch. A real deployment swaps this module's internals for the DB-backed
repository/report store from H30/H31/H33a without changing the public
surface any of those callers use (`case_repository`, `get_report`,
`put_report`, `get_latest_report`).
"""

from __future__ import annotations

from threading import Lock
from typing import Dict, Optional

from app.weekly.briefing import BriefingStore
from app.weekly.cases_durable import CaseRepository
from app.weekly.report import WeeklyReport

#: Process-wide durable episode ledger (H33a) shared by every weekly consumer.
case_repository = CaseRepository()

#: Process-wide briefing/receipt store (H34b).
briefing_store = BriefingStore()

_reports: Dict[str, WeeklyReport] = {}
_latest_report_id_by_branch: Dict[str, str] = {}
_lock = Lock()


def put_report(report: WeeklyReport) -> WeeklyReport:
    """Register/replace the latest materialized report for its branch."""
    with _lock:
        _reports[report.report_id] = report
        _latest_report_id_by_branch[report.branch] = report.report_id
    return report


def get_report(report_id: str) -> Optional[WeeklyReport]:
    with _lock:
        return _reports.get(report_id)


def get_latest_report(branch: str) -> Optional[WeeklyReport]:
    with _lock:
        report_id = _latest_report_id_by_branch.get(branch)
        if report_id is None:
            return None
        return _reports.get(report_id)


def clear() -> None:
    """Test-only helper to reset all shared module state between tests."""
    with _lock:
        _reports.clear()
        _latest_report_id_by_branch.clear()
    case_repository.clear()
    briefing_store.clear()
