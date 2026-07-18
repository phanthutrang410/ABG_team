"""D6 — ops stubs: kill switches, scheduler-tick wrapper, rollback runbook.

Scope is intentionally narrow (per brief): `scheduler_tick` only wraps H31's
`run_weekly_from_bytes` (register/validate/stage/promote) with a kill-switch
gate; it does not itself run H32 observations, H33b delta/reconcile or
H34 report/briefing materialization — those stages are triggered separately
downstream of a successful ingestion run in the target architecture (doc 13
§13). `case_materialization` / `briefing_publish` are reserved switches for
that downstream wiring so a future scheduler-tick can gate those stages too
without a breaking change to this dataclass; they are documented here, not
silently implemented as a no-op that would overclaim coverage.

`openai_calls` never gates this path: the H31 workflow makes zero provider
calls on its own (register/validate/stage/promote), so disabling OpenAI
must never block ingestion (target architecture §13 — "provider down does
not break the weekly workflow").
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List, Optional

from app.dwh.weekly_workflow import WorkflowResult, run_weekly_from_bytes

RunWeeklyFn = Callable[..., WorkflowResult]


@dataclass(frozen=True)
class KillSwitchConfig:
    """Independent on/off switches for weekly-pipeline stages — default enabled.

    Setting a switch to ``False`` disables that stage; it never implicitly
    disables an unrelated stage (e.g. `openai_calls=False` must not block
    `ingestion`).
    """

    ingestion: bool = True
    case_materialization: bool = True
    briefing_publish: bool = True
    openai_calls: bool = True


@dataclass(frozen=True)
class SchedulerTickResult:
    """Outcome of one scheduler-triggered tick — mirrors `WorkflowResult`."""

    status: str  # "blocked" | "succeeded" | "duplicate" | "failed"
    reason_codes: List[str] = field(default_factory=list)
    run_id: Optional[str] = None
    snapshot_id: Optional[str] = None


def scheduler_tick(
    database_url: str,
    manifest_bytes: bytes,
    *,
    dataset_key: str,
    approval_id: str,
    config: KillSwitchConfig,
    idempotency_key: Optional[str] = None,
    provenance_approved: bool = True,
    run_fn: RunWeeklyFn = run_weekly_from_bytes,
) -> SchedulerTickResult:
    """Kill-switch-gated wrapper around `run_weekly_from_bytes` (H31).

    When `config.ingestion` is `False`, `run_fn` is never called — zero
    side effects, `status="blocked"`. Exact-byte replay stays idempotent
    because the underlying `run_fn` (H31) owns that guarantee; this wrapper
    neither retries nor mutates the manifest/idempotency key it is given.
    """
    if not config.ingestion:
        return SchedulerTickResult(status="blocked", reason_codes=["ingestion_kill_switch_enabled"])

    result = run_fn(
        database_url,
        dataset_key=dataset_key,
        content_bytes=manifest_bytes,
        approval_id=approval_id,
        idempotency_key=idempotency_key,
        provenance_approved=provenance_approved,
    )
    return SchedulerTickResult(
        status=result.status,
        reason_codes=list(result.reason_codes),
        run_id=result.run_id,
        snapshot_id=result.snapshot_id,
    )


@dataclass(frozen=True)
class RollbackResult:
    """Reason-code envelope — this stub performs no database write itself."""

    status: str  # always "not_implemented" in this MVP wave
    reason_codes: List[str] = field(default_factory=list)


def rollback_active_pointer(dataset_key: str, target_snapshot_id: str) -> RollbackResult:
    """Manual rollback runbook (documented here; not executed by this stub).

    Runbook — human-executed until a real rollback service ships:

    1. Confirm ``target_snapshot_id`` exists in ``dwh.dataset_snapshot`` for
       ``dataset_key`` and has ``status`` in ``{"active", "superseded"}`` —
       never roll back onto a ``staged``/never-promoted snapshot.
    2. Confirm no in-flight ``workflow_run`` for ``dataset_key`` is
       ``queued``/``running``; wait for it to finish or fail first.
    3. In one transaction: set the currently active
       ``dwh.dataset_snapshot.status`` to ``"superseded"``, then set
       ``dwh.active_dataset_snapshot.snapshot_id`` to ``target_snapshot_id``
       and its ``status`` back to ``"active"``; update ``promoted_at`` /
       ``promoted_by_run_id`` to record the manual-rollback actor/run.
    4. Re-run H34a ``materialize_report`` for the affected branch(es) so the
       weekly report/briefing reflect the rolled-back snapshot — never edit
       report/briefing rows directly.
    5. Record an access-audit event (``action="rollback_active_pointer"``)
       with the operator actor id and ``target_snapshot_id`` as the
       resource handle — never log raw snapshot bytes/PII.
    6. Verify ``GET /weekly-reports/latest`` and ``GET /health`` after the
       rollback before closing the incident.

    This function performs none of the above; it only returns a
    reason-code envelope so callers/tests can assert the runbook contract
    exists without this MVP wave writing directly to the ``dwh`` schema.
    """
    _ = (dataset_key, target_snapshot_id)
    return RollbackResult(status="not_implemented", reason_codes=["manual_runbook_required"])
