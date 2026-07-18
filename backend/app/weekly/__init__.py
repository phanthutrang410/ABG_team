"""Weekly workflow core — H32/H33a/H33b/H34a/H34b (Mode B only, Decision #23).

Combined semester+attendance namespace is not approved yet, so every module
in this package stays inside one branch (`semester` | `attendance`) at a
time; there is no fuzzy/heuristic cross-source join anywhere here.
"""

from __future__ import annotations

from app.weekly.briefing import (
    Briefing,
    BriefingReceipt,
    BriefingStore,
    get_or_create_briefing,
    mark_ack,
    mark_shown,
)
from app.weekly.cases_durable import CaseEpisode, CaseRepository
from app.weekly.delta import DeltaItem, DeltaType, RunVersions, compute_delta, reconcile
from app.weekly.observations import (
    NamespaceMismatchError,
    SignalObservation,
    build_observations_mode_b,
)
from app.weekly.report import WeeklyReport, materialize_report

__all__ = [
    "Briefing",
    "BriefingReceipt",
    "BriefingStore",
    "CaseEpisode",
    "CaseRepository",
    "DeltaItem",
    "DeltaType",
    "NamespaceMismatchError",
    "RunVersions",
    "SignalObservation",
    "WeeklyReport",
    "build_observations_mode_b",
    "compute_delta",
    "get_or_create_briefing",
    "mark_ack",
    "mark_shown",
    "materialize_report",
    "reconcile",
]
