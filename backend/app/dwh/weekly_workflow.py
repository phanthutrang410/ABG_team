"""H31 — WeeklyWorkflowService: register → validate → stage → promote.

Same entry point for CLI and (later) external scheduler/worker.
Exact-byte replay is idempotent; failures do not promote active pointer.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session, sessionmaker

from app.dwh.models import (
    ActiveDatasetSnapshot,
    DatasetSnapshot,
    DatasetSource,
    WorkflowRun,
    WorkflowStepRun,
)

WORKFLOW_VERSION = "weekly-v1"
STEPS = ("register", "validate", "stage", "promote")


@dataclass
class WeeklyManifest:
    dataset_key: str
    content_bytes: bytes
    approval_id: str
    schema_version: str = "weekly-snapshot-v2"
    pseudonym_namespace_version: str = "approval:pending-linked-namespace"
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    extracted_at: Optional[datetime] = None
    provenance_approved: bool = True
    fixture_mode: str = "approved_replay"

    @property
    def content_sha256(self) -> str:
        return hashlib.sha256(self.content_bytes).hexdigest()


@dataclass
class WorkflowResult:
    status: str
    run_id: str
    snapshot_id: Optional[str] = None
    reason_codes: list[str] = field(default_factory=list)
    detail: dict[str, Any] = field(default_factory=dict)


class WeeklyWorkflowService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def run(
        self,
        manifest: WeeklyManifest,
        *,
        idempotency_key: Optional[str] = None,
        trigger_kind: str = "cli",
        replay_of_run_id: Optional[str] = None,
    ) -> WorkflowResult:
        key = idempotency_key or f"{manifest.dataset_key}:{manifest.content_sha256}"
        existing = self.session.scalar(
            select(WorkflowRun).where(
                WorkflowRun.dataset_content_sha256 == manifest.content_sha256,
                WorkflowRun.workflow_version == WORKFLOW_VERSION,
                WorkflowRun.idempotency_key == key,
            )
        )
        if existing is not None:
            if existing.status == "succeeded":
                return WorkflowResult(
                    status="duplicate",
                    run_id=existing.run_id,
                    snapshot_id=existing.snapshot_id,
                    reason_codes=["idempotent_replay"],
                    detail={"prior_status": existing.status},
                )
            if existing.status == "duplicate":
                return WorkflowResult(
                    status="duplicate",
                    run_id=existing.run_id,
                    snapshot_id=existing.snapshot_id,
                    reason_codes=["idempotent_replay"],
                )

        run_id = f"run-{uuid.uuid4().hex[:16]}"
        now = datetime.now(timezone.utc)
        run = WorkflowRun(
            run_id=run_id,
            dataset_key=manifest.dataset_key,
            trigger_kind=trigger_kind,
            idempotency_key=key,
            workflow_version=WORKFLOW_VERSION,
            dataset_content_sha256=manifest.content_sha256,
            status="queued",
            replay_of_run_id=replay_of_run_id,
            started_at=now,
        )
        self.session.add(run)
        self.session.flush()

        try:
            self._step(run_id, "register", lambda: self._register(manifest))
            self._step(run_id, "validate", lambda: self._validate(manifest))
            snapshot_id = self._step(
                run_id, "stage", lambda: self._stage(manifest, run_id)
            )
            self._step(
                run_id,
                "promote",
                lambda: self._promote(manifest.dataset_key, snapshot_id, run_id),
            )
            run.status = "succeeded"
            run.snapshot_id = snapshot_id
            run.finished_at = datetime.now(timezone.utc)
            self.session.flush()
            return WorkflowResult(
                status="succeeded",
                run_id=run_id,
                snapshot_id=snapshot_id,
                reason_codes=[],
            )
        except WorkflowStepError as exc:
            run.status = "failed"
            run.failure_reason_code = exc.reason_code
            run.finished_at = datetime.now(timezone.utc)
            self.session.flush()
            return WorkflowResult(
                status="failed",
                run_id=run_id,
                reason_codes=[exc.reason_code],
                detail={"step": exc.step},
            )


    def _step(self, run_id: str, name: str, fn):  # type: ignore[no-untyped-def]
        now = datetime.now(timezone.utc)
        step = WorkflowStepRun(
            run_id=run_id,
            step_name=name,
            status="running",
            started_at=now,
        )
        self.session.add(step)
        self.session.flush()
        try:
            result = fn()
            step.status = "succeeded"
            step.finished_at = datetime.now(timezone.utc)
            self.session.flush()
            return result
        except WorkflowStepError as exc:
            step.status = "failed"
            step.reason_code = exc.reason_code
            step.finished_at = datetime.now(timezone.utc)
            self.session.flush()
            raise


    def _register(self, manifest: WeeklyManifest) -> None:
        src = self.session.get(DatasetSource, manifest.dataset_key)
        if src is None:
            self.session.add(
                DatasetSource(
                    dataset_key=manifest.dataset_key,
                    source_owner="workflow",
                    retention_policy="90d-metadata",
                    usage_notes="registered by WeeklyWorkflowService",
                )
            )
            self.session.flush()


    def _validate(self, manifest: WeeklyManifest) -> None:
        if not manifest.provenance_approved:
            raise WorkflowStepError("validate", "approval_missing")
        if not manifest.approval_id.strip():
            raise WorkflowStepError("validate", "approval_id_missing")
        if len(manifest.content_sha256) != 64:
            raise WorkflowStepError("validate", "hash_invalid")
        if not manifest.content_bytes:
            raise WorkflowStepError("validate", "empty_artifact")
        # Schema gate: must be JSON object for approved replay fixtures.
        try:
            payload = json.loads(manifest.content_bytes.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise WorkflowStepError("validate", "schema_invalid") from exc
        if not isinstance(payload, dict):
            raise WorkflowStepError("validate", "schema_invalid")


    def _stage(self, manifest: WeeklyManifest, run_id: str) -> str:
        existing = self.session.scalar(
            select(DatasetSnapshot).where(
                DatasetSnapshot.dataset_key == manifest.dataset_key,
                DatasetSnapshot.dataset_content_sha256 == manifest.content_sha256,
            )
        )
        if existing is not None:
            return existing.snapshot_id

        snapshot_id = f"snap-{uuid.uuid4().hex[:16]}"
        extracted = manifest.extracted_at or datetime.now(timezone.utc)
        self.session.add(
            DatasetSnapshot(
                snapshot_id=snapshot_id,
                dataset_key=manifest.dataset_key,
                extracted_at=extracted,
                schema_version=manifest.schema_version,
                pseudonym_namespace_version=manifest.pseudonym_namespace_version,
                source_snapshot_sha256=manifest.content_sha256,
                dataset_content_sha256=manifest.content_sha256,
                approval_id=manifest.approval_id,
                provenance_approved=manifest.provenance_approved,
                fixture_mode=manifest.fixture_mode,
                period_start=manifest.period_start,
                period_end=manifest.period_end,
                status="staged",
            )
        )
        self.session.flush()
        return snapshot_id


    def _promote(self, dataset_key: str, snapshot_id: str, run_id: str) -> None:
        snap = self.session.get(DatasetSnapshot, snapshot_id)
        if snap is None:
            raise WorkflowStepError("promote", "snapshot_missing")
        active = self.session.get(ActiveDatasetSnapshot, dataset_key)
        now = datetime.now(timezone.utc)
        if active is None:
            self.session.add(
                ActiveDatasetSnapshot(
                    dataset_key=dataset_key,
                    snapshot_id=snapshot_id,
                    promoted_at=now,
                    promoted_by_run_id=run_id,
                )
            )
        else:
            if active.snapshot_id != snapshot_id:
                prev = self.session.get(DatasetSnapshot, active.snapshot_id)
                if prev is not None and prev.status == "active":
                    prev.status = "superseded"
            active.snapshot_id = snapshot_id
            active.promoted_at = now
            active.promoted_by_run_id = run_id
        snap.status = "active"
        self.session.flush()


class WorkflowStepError(RuntimeError):
    def __init__(self, step: str, reason_code: str) -> None:
        super().__init__(f"{step}:{reason_code}")
        self.step = step
        self.reason_code = reason_code


def run_weekly_from_bytes(
    database_url: str,
    *,
    dataset_key: str,
    content_bytes: bytes,
    approval_id: str,
    idempotency_key: Optional[str] = None,
    provenance_approved: bool = True,
) -> WorkflowResult:
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    session = SessionLocal()
    try:
        # Advisory lock to serialize concurrent duplicate triggers.
        lock_key = int(hashlib.sha256(dataset_key.encode()).hexdigest()[:15], 16)
        session.execute(text("SELECT pg_advisory_xact_lock(:k)"), {"k": lock_key})
        service = WeeklyWorkflowService(session)
        result = service.run(
            WeeklyManifest(
                dataset_key=dataset_key,
                content_bytes=content_bytes,
                approval_id=approval_id,
                provenance_approved=provenance_approved,
            ),
            idempotency_key=idempotency_key,
        )
        session.commit()
        return result
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
        engine.dispose()
