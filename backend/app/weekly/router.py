"""H34 — light wiring for `GET /weekly-reports/latest` + briefing shown/ack.

This router only *reads* the shared in-memory state (`app.weekly.state`) and
records one-time shown/ack receipts (H34b) — it never runs scoring/DWH
observations itself. A real deployment points `app.weekly.state` at the
DB-backed H30/H31/H33a/H33b pipeline; this module's routes do not change.

If no run has materialized a report yet for a branch, an `empty` fixture is
seeded deterministically (H34a `materialize_report` with zero deltas) so the
API and G08 fixtures stay usable without requiring a live weekly workflow —
this is a demo/test convenience, never a claim that a real weekly run
happened.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.auth.principal import Principal, get_principal
from app.weekly import state as weekly_state
from app.weekly.briefing import Briefing, BriefingReceipt, get_or_create_briefing, mark_ack, mark_shown
from app.weekly.report import WeeklyReport, materialize_report

router = APIRouter(tags=["weekly-reports"])

_KNOWN_BRANCHES = frozenset({"semester", "attendance"})


def _reject_unknown_branch(branch: str) -> None:
    if branch not in _KNOWN_BRANCHES:
        raise HTTPException(
            status_code=400,
            detail={"code": "unknown_branch", "message": "branch must be semester|attendance"},
        )


def _seed_report_if_missing(branch: str) -> WeeklyReport:
    existing = weekly_state.get_latest_report(branch)
    if existing is not None:
        return existing
    report = materialize_report(weekly_state.case_repository, [], None, branch)
    return weekly_state.put_report(report)


def _role_for_principal(principal: Principal) -> str:
    return "advisor" if principal.active_role == "advisor" else "leader"


@router.get("/weekly-reports/latest", response_model=WeeklyReport)
def get_latest_weekly_report(
    branch: str = "semester",
    principal: Principal = Depends(get_principal),
) -> WeeklyReport:
    _reject_unknown_branch(branch)
    _ = principal  # authenticated read; no per-role filtering at aggregate level
    return _seed_report_if_missing(branch)


@router.get("/weekly-briefings/latest", response_model=Briefing)
def get_latest_weekly_briefing(
    branch: str = "semester",
    principal: Principal = Depends(get_principal),
) -> Briefing:
    _reject_unknown_branch(branch)
    report = _seed_report_if_missing(branch)
    role = _role_for_principal(principal)
    return get_or_create_briefing(weekly_state.briefing_store, report, role)


@router.post("/weekly-briefings/{briefing_id}/shown", response_model=BriefingReceipt)
def mark_weekly_briefing_shown(
    briefing_id: str,
    principal: Principal = Depends(get_principal),
) -> BriefingReceipt:
    role = _role_for_principal(principal)
    return mark_shown(weekly_state.briefing_store, principal.actor_id, role, briefing_id)


@router.post("/weekly-briefings/{briefing_id}/ack", response_model=BriefingReceipt)
def ack_weekly_briefing(
    briefing_id: str,
    principal: Principal = Depends(get_principal),
) -> BriefingReceipt:
    role = _role_for_principal(principal)
    return mark_ack(weekly_state.briefing_store, principal.actor_id, role, briefing_id)
