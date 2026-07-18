"""D6 — ops stubs: kill switches, scheduler-tick wrapper, rollback runbook."""

from __future__ import annotations

from typing import Any, Dict, Optional

import pytest

from app.dwh.weekly_workflow import WorkflowResult
from app.weekly.ops import KillSwitchConfig, rollback_active_pointer, scheduler_tick


class _FakeRunFn:
    """Mimics H31's idempotent `run_weekly_from_bytes` without touching Postgres."""

    def __init__(self) -> None:
        self.calls = 0
        self._seen: Dict[str, str] = {}

    def __call__(
        self,
        database_url: str,
        *,
        dataset_key: str,
        content_bytes: bytes,
        approval_id: str,
        idempotency_key: Optional[str] = None,
        provenance_approved: bool = True,
    ) -> WorkflowResult:
        self.calls += 1
        key = idempotency_key or f"{dataset_key}:{content_bytes!r}"
        if key in self._seen:
            return WorkflowResult(
                status="duplicate",
                run_id=self._seen[key],
                snapshot_id=f"snap-{key}",
                reason_codes=["idempotent_replay"],
            )
        run_id = f"run-{len(self._seen) + 1}"
        self._seen[key] = run_id
        return WorkflowResult(status="succeeded", run_id=run_id, snapshot_id=f"snap-{key}")


def _config(**overrides: Any) -> KillSwitchConfig:
    return KillSwitchConfig(**overrides)


# --- kill switch blocks ingestion --------------------------------------------


def test_kill_switch_blocks_ingestion_with_zero_effect() -> None:
    fake = _FakeRunFn()
    result = scheduler_tick(
        "postgresql://unused",
        b"{}",
        dataset_key="epu-care-signals",
        approval_id="approval:1",
        config=_config(ingestion=False),
        run_fn=fake,
    )
    assert result.status == "blocked"
    assert "ingestion_kill_switch_enabled" in result.reason_codes
    assert fake.calls == 0  # zero effect: underlying workflow never invoked


def test_default_kill_switch_config_is_all_enabled() -> None:
    config = KillSwitchConfig()
    assert config.ingestion is True
    assert config.case_materialization is True
    assert config.briefing_publish is True
    assert config.openai_calls is True


# --- openai kill switch does not block workflow ------------------------------


def test_openai_kill_switch_does_not_block_workflow() -> None:
    fake = _FakeRunFn()
    result = scheduler_tick(
        "postgresql://unused",
        b"{}",
        dataset_key="epu-care-signals",
        approval_id="approval:1",
        config=_config(openai_calls=False),
        idempotency_key="k1",
        run_fn=fake,
    )
    assert result.status == "succeeded"
    assert fake.calls == 1


def test_openai_and_other_switches_independent_of_ingestion() -> None:
    fake = _FakeRunFn()
    # openai/case_materialization/briefing_publish all off — ingestion still runs.
    result = scheduler_tick(
        "postgresql://unused",
        b"{}",
        dataset_key="epu-care-signals",
        approval_id="approval:1",
        config=_config(openai_calls=False, case_materialization=False, briefing_publish=False),
        idempotency_key="k-indep",
        run_fn=fake,
    )
    assert result.status == "succeeded"
    assert fake.calls == 1


# --- duplicate schedule no-op via existing idempotency -----------------------


def test_duplicate_schedule_is_no_op_via_existing_idempotency() -> None:
    fake = _FakeRunFn()
    first = scheduler_tick(
        "postgresql://unused",
        b'{"n": 1}',
        dataset_key="epu-care-signals",
        approval_id="approval:1",
        config=_config(),
        idempotency_key="same-key",
        run_fn=fake,
    )
    second = scheduler_tick(
        "postgresql://unused",
        b'{"n": 1}',
        dataset_key="epu-care-signals",
        approval_id="approval:1",
        config=_config(),
        idempotency_key="same-key",
        run_fn=fake,
    )
    assert first.status == "succeeded"
    assert second.status == "duplicate"
    assert first.snapshot_id == second.snapshot_id
    assert fake.calls == 2  # scheduler called twice, but no duplicate effect was applied


def test_ingestion_disabled_prevents_even_a_would_be_duplicate_call() -> None:
    fake = _FakeRunFn()
    scheduler_tick(
        "postgresql://unused",
        b"{}",
        dataset_key="epu-x",
        approval_id="approval:1",
        config=_config(),
        idempotency_key="k2",
        run_fn=fake,
    )
    blocked = scheduler_tick(
        "postgresql://unused",
        b"{}",
        dataset_key="epu-x",
        approval_id="approval:1",
        config=_config(ingestion=False),
        idempotency_key="k2",
        run_fn=fake,
    )
    assert blocked.status == "blocked"
    assert fake.calls == 1  # the disabled tick never reaches run_fn


# --- rollback runbook stub ----------------------------------------------------


def test_rollback_active_pointer_returns_not_implemented_reason_codes() -> None:
    result = rollback_active_pointer("epu-care-signals", "snap-target")
    assert result.status == "not_implemented"
    assert "manual_runbook_required" in result.reason_codes


def test_rollback_active_pointer_docstring_documents_runbook_steps() -> None:
    doc = rollback_active_pointer.__doc__ or ""
    for keyword in ("dataset_snapshot", "active_dataset_snapshot", "materialize_report", "access-audit"):
        assert keyword in doc


@pytest.mark.parametrize("ingestion", [True, False])
def test_scheduler_tick_never_calls_run_fn_with_mutated_manifest(ingestion: bool) -> None:
    captured: Dict[str, Any] = {}

    def spy_run_fn(database_url: str, **kwargs: Any) -> WorkflowResult:
        captured.update(kwargs)
        return WorkflowResult(status="succeeded", run_id="run-x", snapshot_id="snap-x")

    manifest = b'{"exact": "bytes"}'
    scheduler_tick(
        "postgresql://unused",
        manifest,
        dataset_key="epu-y",
        approval_id="approval:2",
        config=_config(ingestion=ingestion),
        idempotency_key="k3",
        run_fn=spy_run_fn,
    )
    if ingestion:
        assert captured["content_bytes"] == manifest
    else:
        assert captured == {}
