"""SQLAlchemy models for the MVP `dwh` schema (H19).

Constraints follow docs/04-engineering/07-mvp-persistence-schema.md and
docs/04-engineering/04-epu-data-integration-contract.md §2.
No case-state or ML prediction tables in this revision.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
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
