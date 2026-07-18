"""SQLAlchemy models for the MVP `dwh` schema (H19+).

Constraints follow docs/04-engineering/07-mvp-persistence-schema.md,
docs/04-engineering/14-database-schema-erd.md, and
docs/04-engineering/04-epu-data-integration-contract.md §2.

Case-state / care ReviewCase tables remain out of scope. ML term snapshot and
attendance week rollup are materialization targets (empty until a writer task).
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    MetaData,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

DWH_SCHEMA = "dwh"

DWH_TABLE_NAMES = (
    "source_manifest",
    "student_dimension",
    "term_grade",
    "attendance_event",
    "academic_status",
    "advisor_assignment",
    "data_quality_report",
    # H30 weekly snapshot registry / workflow ledger
    "dataset_source",
    "dataset_snapshot",
    "active_dataset_snapshot",
    "workflow_run",
    "workflow_step_run",
    # ML + attendance week materializations
    "ml_term_snapshot",
    "attendance_week",
)


class Base(DeclarativeBase):
    metadata = MetaData(schema=DWH_SCHEMA)


class SourceManifest(Base):
    __tablename__ = "source_manifest"

    source_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    snapshot_sha256: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    provenance_approved: Mapped[bool] = mapped_column(Boolean, nullable=False)
    schema_version: Mapped[str] = mapped_column(String(64), nullable=False)
    record_count: Mapped[int] = mapped_column(Integer, nullable=False)
    extracted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        CheckConstraint("record_count >= 0", name="ck_source_manifest_record_count_nonneg"),
        CheckConstraint(
            "char_length(snapshot_sha256) = 64",
            name="ck_source_manifest_sha256_len",
        ),
    )


class StudentDimension(Base):
    __tablename__ = "student_dimension"

    source_id: Mapped[str] = mapped_column(
        String(128),
        ForeignKey(f"{DWH_SCHEMA}.source_manifest.source_id", ondelete="CASCADE"),
        primary_key=True,
    )
    student_ref: Mapped[str] = mapped_column(String(128), primary_key=True)
    cohort: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    department: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    program: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    major: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    class_code: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)


class TermGrade(Base):
    __tablename__ = "term_grade"

    source_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    student_ref: Mapped[str] = mapped_column(String(128), primary_key=True)
    term_code: Mapped[str] = mapped_column(String(32), primary_key=True)
    course_ref: Mapped[str] = mapped_column(String(128), primary_key=True)
    credits: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2), nullable=True)
    final_grade: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    grade_status: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    __table_args__ = (
        ForeignKeyConstraint(
            ["source_id", "student_ref"],
            [
                f"{DWH_SCHEMA}.student_dimension.source_id",
                f"{DWH_SCHEMA}.student_dimension.student_ref",
            ],
            ondelete="CASCADE",
            name="fk_term_grade_student",
        ),
    )


class AttendanceEvent(Base):
    """Empty table OK until H15-approved attendance export is available."""

    __tablename__ = "attendance_event"

    source_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    student_ref: Mapped[str] = mapped_column(String(128), primary_key=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    # Empty string when course grain is absent — keeps unique key stable (H15 may refine).
    course_ref: Mapped[str] = mapped_column(String(128), primary_key=True, default="")
    presence_status: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    excused: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)

    __table_args__ = (
        ForeignKeyConstraint(
            ["source_id", "student_ref"],
            [
                f"{DWH_SCHEMA}.student_dimension.source_id",
                f"{DWH_SCHEMA}.student_dimension.student_ref",
            ],
            ondelete="CASCADE",
            name="fk_attendance_event_student",
        ),
    )


class AcademicStatus(Base):
    __tablename__ = "academic_status"

    source_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    student_ref: Mapped[str] = mapped_column(String(128), primary_key=True)
    status_code: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    status_observed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # Internal evaluation only: true | false | unknown (EPU §3 / decision #17).
    is_dropout_outcome: Mapped[str] = mapped_column(String(16), nullable=False, default="unknown")

    __table_args__ = (
        ForeignKeyConstraint(
            ["source_id", "student_ref"],
            [
                f"{DWH_SCHEMA}.student_dimension.source_id",
                f"{DWH_SCHEMA}.student_dimension.student_ref",
            ],
            ondelete="CASCADE",
            name="fk_academic_status_student",
        ),
        CheckConstraint(
            "is_dropout_outcome IN ('true', 'false', 'unknown')",
            name="ck_academic_status_dropout_outcome",
        ),
    )


class AdvisorAssignment(Base):
    __tablename__ = "advisor_assignment"

    source_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    student_ref: Mapped[str] = mapped_column(String(128), primary_key=True)
    advisor_ref: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    scope_source: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)

    __table_args__ = (
        ForeignKeyConstraint(
            ["source_id", "student_ref"],
            [
                f"{DWH_SCHEMA}.student_dimension.source_id",
                f"{DWH_SCHEMA}.student_dimension.student_ref",
            ],
            ondelete="CASCADE",
            name="fk_advisor_assignment_student",
        ),
    )


class DataQualityReport(Base):
    __tablename__ = "data_quality_report"

    report_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_id: Mapped[str] = mapped_column(
        String(128),
        ForeignKey(f"{DWH_SCHEMA}.source_manifest.source_id", ondelete="CASCADE"),
        nullable=False,
    )
    report_version: Mapped[str] = mapped_column(String(64), nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    row_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reject_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    missingness_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    term_coverage_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    freshness_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reason_codes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "source_id",
            "report_version",
            "generated_at",
            name="uq_data_quality_report_version_ts",
        ),
        CheckConstraint("row_count >= 0", name="ck_dqr_row_count_nonneg"),
        CheckConstraint("reject_count >= 0", name="ck_dqr_reject_count_nonneg"),
    )


class DatasetSource(Base):
    """Registry for a logical dataset_key (H30)."""

    __tablename__ = "dataset_source"

    dataset_key: Mapped[str] = mapped_column(String(128), primary_key=True)
    source_owner: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    retention_policy: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    usage_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class DatasetSnapshot(Base):
    """Immutable multi-version snapshot of a dataset (H30)."""

    __tablename__ = "dataset_snapshot"

    snapshot_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    dataset_key: Mapped[str] = mapped_column(
        String(128),
        ForeignKey(f"{DWH_SCHEMA}.dataset_source.dataset_key", ondelete="CASCADE"),
        nullable=False,
    )
    previous_snapshot_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    supersedes_snapshot_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    period_start: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    period_end: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    extracted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    delivered_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    schema_version: Mapped[str] = mapped_column(String(64), nullable=False)
    pseudonym_namespace_version: Mapped[str] = mapped_column(String(64), nullable=False)
    source_snapshot_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    normalized_artifact_sha256: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    dataset_content_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    approval_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    provenance_approved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    fixture_mode: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    legacy_source_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    row_counts_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    quality_reason_codes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="staged")

    __table_args__ = (
        UniqueConstraint(
            "dataset_key",
            "dataset_content_sha256",
            name="uq_dataset_snapshot_content_hash",
        ),
        CheckConstraint(
            "char_length(source_snapshot_sha256) = 64",
            name="ck_dataset_snapshot_source_sha_len",
        ),
        CheckConstraint(
            "char_length(dataset_content_sha256) = 64",
            name="ck_dataset_snapshot_content_sha_len",
        ),
        CheckConstraint(
            "status IN ('staged', 'active', 'superseded', 'rejected')",
            name="ck_dataset_snapshot_status",
        ),
    )


class ActiveDatasetSnapshot(Base):
    """Atomic pointer to the currently active snapshot per dataset_key (H30)."""

    __tablename__ = "active_dataset_snapshot"

    dataset_key: Mapped[str] = mapped_column(
        String(128),
        ForeignKey(f"{DWH_SCHEMA}.dataset_source.dataset_key", ondelete="CASCADE"),
        primary_key=True,
    )
    snapshot_id: Mapped[str] = mapped_column(
        String(128),
        ForeignKey(f"{DWH_SCHEMA}.dataset_snapshot.snapshot_id", ondelete="RESTRICT"),
        nullable=False,
    )
    promoted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    promoted_by_run_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)


class WorkflowRun(Base):
    """Weekly workflow run ledger (H30)."""

    __tablename__ = "workflow_run"

    run_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    dataset_key: Mapped[str] = mapped_column(String(128), nullable=False)
    snapshot_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    trigger_kind: Mapped[str] = mapped_column(String(64), nullable=False, default="cli")
    idempotency_key: Mapped[str] = mapped_column(String(256), nullable=False)
    workflow_version: Mapped[str] = mapped_column(String(64), nullable=False)
    model_version: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    threshold_config_version: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    dataset_content_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="queued")
    failure_reason_code: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    replay_of_run_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    finished_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        UniqueConstraint(
            "dataset_content_sha256",
            "workflow_version",
            "idempotency_key",
            name="uq_workflow_run_idempotency",
        ),
        CheckConstraint(
            "status IN ("
            "'queued','validating','staging','scoring','reconciling',"
            "'reporting','publishing','succeeded','failed','duplicate'"
            ")",
            name="ck_workflow_run_status",
        ),
    )


class WorkflowStepRun(Base):
    """Per-step ledger for a workflow run (H30)."""

    __tablename__ = "workflow_step_run"

    step_run_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(
        String(128),
        ForeignKey(f"{DWH_SCHEMA}.workflow_run.run_id", ondelete="CASCADE"),
        nullable=False,
    )
    step_name: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="queued")
    reason_code: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    finished_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        UniqueConstraint("run_id", "step_name", name="uq_workflow_step_run_name"),
        CheckConstraint(
            "status IN ('queued','running','succeeded','failed','skipped')",
            name="ck_workflow_step_status",
        ),
    )


class MlTermSnapshot(Base):
    """Per-student ML feature + review-band materialization for a semester source.

    Grain: one row per ``(source_id, student_ref)`` (upsert on re-score).
    ``model_score`` is internal-only; public/agent consumers must use
    ``review_priority_band``, factor codes, coverage, and ``agent_explain_json``.
    """

    __tablename__ = "ml_term_snapshot"

    source_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    student_ref: Mapped[str] = mapped_column(String(128), primary_key=True)
    dataset_version: Mapped[str] = mapped_column(String(128), nullable=False)
    model_version: Mapped[str] = mapped_column(String(64), nullable=False)
    threshold_config_version: Mapped[str] = mapped_column(String(64), nullable=False)
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_term_code: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)

    latest_term_gpa: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    grade_trend_slope: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 6), nullable=True)
    grade_volatility: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 6), nullable=True)
    failed_credits: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 2), nullable=True)
    attendance_rate_window: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(6, 4), nullable=True
    )
    attendance_trend_slope: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 6), nullable=True
    )

    coverage_status: Mapped[str] = mapped_column(String(32), nullable=False)
    coverage_json: Mapped[str] = mapped_column(Text, nullable=False)
    # Null when below tau_case (no public review band).
    review_priority_band: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    contributing_factors_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    # Internal only — never project to public API / agent context.
    model_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 4), nullable=True)
    explain_schema_version: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    agent_explain_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    evidence_fingerprint: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)

    __table_args__ = (
        ForeignKeyConstraint(
            ["source_id", "student_ref"],
            [
                f"{DWH_SCHEMA}.student_dimension.source_id",
                f"{DWH_SCHEMA}.student_dimension.student_ref",
            ],
            ondelete="CASCADE",
            name="fk_ml_term_snapshot_student",
        ),
        CheckConstraint(
            "coverage_status IN ('ok', 'partial', 'insufficient')",
            name="ck_ml_term_snapshot_coverage_status",
        ),
        CheckConstraint(
            "review_priority_band IS NULL OR "
            "review_priority_band IN ('uu_tien_som', 'can_ra_soat')",
            name="ck_ml_term_snapshot_band",
        ),
        CheckConstraint(
            "model_score IS NULL OR (model_score >= 0 AND model_score <= 1)",
            name="ck_ml_term_snapshot_model_score",
        ),
        CheckConstraint(
            "latest_term_gpa IS NULL OR (latest_term_gpa >= 0 AND latest_term_gpa <= 10)",
            name="ck_ml_term_snapshot_gpa",
        ),
        CheckConstraint(
            "attendance_rate_window IS NULL OR "
            "(attendance_rate_window >= 0 AND attendance_rate_window <= 1)",
            name="ck_ml_term_snapshot_att_rate",
        ),
        CheckConstraint(
            "failed_credits IS NULL OR failed_credits >= 0",
            name="ck_ml_term_snapshot_failed_credits",
        ),
    )


class AttendanceWeek(Base):
    """Student × ISO-week attendance rollup derived from ``attendance_event``.

    Grain: ``(source_id, student_ref, week_start_date)`` where ``week_start_date``
    is the Monday of the ISO week. Excused rows are counted separately and
    excluded from the rate denominator (Data-ML §2.2).
    """

    __tablename__ = "attendance_week"

    source_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    student_ref: Mapped[str] = mapped_column(String(128), primary_key=True)
    week_start_date: Mapped[date] = mapped_column(Date, primary_key=True)
    week_end_date: Mapped[date] = mapped_column(Date, nullable=False)
    n_events: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    n_in_denominator: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    n_present: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    n_absent: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    n_excused_excluded: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    attendance_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 4), nullable=True)
    first_observed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_observed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        ForeignKeyConstraint(
            ["source_id", "student_ref"],
            [
                f"{DWH_SCHEMA}.student_dimension.source_id",
                f"{DWH_SCHEMA}.student_dimension.student_ref",
            ],
            ondelete="CASCADE",
            name="fk_attendance_week_student",
        ),
        CheckConstraint("n_events >= 0", name="ck_attendance_week_n_events"),
        CheckConstraint("n_in_denominator >= 0", name="ck_attendance_week_n_denom"),
        CheckConstraint("n_present >= 0", name="ck_attendance_week_n_present"),
        CheckConstraint("n_absent >= 0", name="ck_attendance_week_n_absent"),
        CheckConstraint("n_excused_excluded >= 0", name="ck_attendance_week_n_excused"),
        CheckConstraint(
            "attendance_rate IS NULL OR (attendance_rate >= 0 AND attendance_rate <= 1)",
            name="ck_attendance_week_rate",
        ),
        CheckConstraint(
            "week_end_date >= week_start_date",
            name="ck_attendance_week_range",
        ),
        CheckConstraint(
            "(n_in_denominator = 0 AND attendance_rate IS NULL) OR "
            "(n_in_denominator > 0 AND attendance_rate IS NOT NULL)",
            name="ck_attendance_week_rate_null_when_empty",
        ),
    )
