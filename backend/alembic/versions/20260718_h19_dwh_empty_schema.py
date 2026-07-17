"""Create empty MVP dwh schema tables (H19).

Revision ID: 20260718_h19_dwh
Revises:
Create Date: 2026-07-18

Creates seven domain tables only. No case-state or ML prediction tables.
No seed/import of rows (H20).
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260718_h19_dwh"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = "dwh"


def upgrade() -> None:
    op.execute(sa.text(f'CREATE SCHEMA IF NOT EXISTS "{SCHEMA}"'))

    op.create_table(
        "source_manifest",
        sa.Column("source_id", sa.String(length=128), nullable=False),
        sa.Column("snapshot_sha256", sa.String(length=64), nullable=False),
        sa.Column("provenance_approved", sa.Boolean(), nullable=False),
        sa.Column("schema_version", sa.String(length=64), nullable=False),
        sa.Column("record_count", sa.Integer(), nullable=False),
        sa.Column("extracted_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("record_count >= 0", name="ck_source_manifest_record_count_nonneg"),
        sa.CheckConstraint(
            "char_length(snapshot_sha256) = 64",
            name="ck_source_manifest_sha256_len",
        ),
        sa.PrimaryKeyConstraint("source_id"),
        sa.UniqueConstraint("snapshot_sha256", name="uq_source_manifest_snapshot_sha256"),
        schema=SCHEMA,
    )

    op.create_table(
        "student_dimension",
        sa.Column("source_id", sa.String(length=128), nullable=False),
        sa.Column("student_ref", sa.String(length=128), nullable=False),
        sa.Column("cohort", sa.String(length=64), nullable=True),
        sa.Column("department", sa.String(length=128), nullable=True),
        sa.Column("program", sa.String(length=128), nullable=True),
        sa.Column("major", sa.String(length=128), nullable=True),
        sa.Column("class_code", sa.String(length=64), nullable=True),
        sa.ForeignKeyConstraint(
            ["source_id"],
            [f"{SCHEMA}.source_manifest.source_id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("source_id", "student_ref"),
        schema=SCHEMA,
    )

    op.create_table(
        "term_grade",
        sa.Column("source_id", sa.String(length=128), nullable=False),
        sa.Column("student_ref", sa.String(length=128), nullable=False),
        sa.Column("term_code", sa.String(length=32), nullable=False),
        sa.Column("course_ref", sa.String(length=128), nullable=False),
        sa.Column("credits", sa.Numeric(6, 2), nullable=True),
        sa.Column("final_grade", sa.Numeric(5, 2), nullable=True),
        sa.Column("grade_status", sa.String(length=64), nullable=True),
        sa.ForeignKeyConstraint(
            ["source_id", "student_ref"],
            [f"{SCHEMA}.student_dimension.source_id", f"{SCHEMA}.student_dimension.student_ref"],
            name="fk_term_grade_student",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("source_id", "student_ref", "term_code", "course_ref"),
        schema=SCHEMA,
    )

    op.create_table(
        "attendance_event",
        sa.Column("source_id", sa.String(length=128), nullable=False),
        sa.Column("student_ref", sa.String(length=128), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("course_ref", sa.String(length=128), nullable=False, server_default=""),
        sa.Column("presence_status", sa.String(length=32), nullable=True),
        sa.Column("excused", sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(
            ["source_id", "student_ref"],
            [f"{SCHEMA}.student_dimension.source_id", f"{SCHEMA}.student_dimension.student_ref"],
            name="fk_attendance_event_student",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("source_id", "student_ref", "observed_at", "course_ref"),
        schema=SCHEMA,
    )

    op.create_table(
        "academic_status",
        sa.Column("source_id", sa.String(length=128), nullable=False),
        sa.Column("student_ref", sa.String(length=128), nullable=False),
        sa.Column("status_code", sa.String(length=64), nullable=True),
        sa.Column("status_observed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "is_dropout_outcome",
            sa.String(length=16),
            nullable=False,
            server_default="unknown",
        ),
        sa.CheckConstraint(
            "is_dropout_outcome IN ('true', 'false', 'unknown')",
            name="ck_academic_status_dropout_outcome",
        ),
        sa.ForeignKeyConstraint(
            ["source_id", "student_ref"],
            [f"{SCHEMA}.student_dimension.source_id", f"{SCHEMA}.student_dimension.student_ref"],
            name="fk_academic_status_student",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("source_id", "student_ref"),
        schema=SCHEMA,
    )

    op.create_table(
        "advisor_assignment",
        sa.Column("source_id", sa.String(length=128), nullable=False),
        sa.Column("student_ref", sa.String(length=128), nullable=False),
        sa.Column("advisor_ref", sa.String(length=128), nullable=True),
        sa.Column("scope_source", sa.String(length=128), nullable=True),
        sa.ForeignKeyConstraint(
            ["source_id", "student_ref"],
            [f"{SCHEMA}.student_dimension.source_id", f"{SCHEMA}.student_dimension.student_ref"],
            name="fk_advisor_assignment_student",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("source_id", "student_ref"),
        schema=SCHEMA,
    )

    op.create_table(
        "data_quality_report",
        sa.Column("report_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("source_id", sa.String(length=128), nullable=False),
        sa.Column("report_version", sa.String(length=64), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("row_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("reject_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("missingness_summary", sa.Text(), nullable=True),
        sa.Column("term_coverage_summary", sa.Text(), nullable=True),
        sa.Column("freshness_summary", sa.Text(), nullable=True),
        sa.Column("reason_codes", sa.Text(), nullable=True),
        sa.CheckConstraint("row_count >= 0", name="ck_dqr_row_count_nonneg"),
        sa.CheckConstraint("reject_count >= 0", name="ck_dqr_reject_count_nonneg"),
        sa.ForeignKeyConstraint(
            ["source_id"],
            [f"{SCHEMA}.source_manifest.source_id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("report_id"),
        sa.UniqueConstraint(
            "source_id",
            "report_version",
            "generated_at",
            name="uq_data_quality_report_version_ts",
        ),
        schema=SCHEMA,
    )


def downgrade() -> None:
    op.drop_table("data_quality_report", schema=SCHEMA)
    op.drop_table("advisor_assignment", schema=SCHEMA)
    op.drop_table("academic_status", schema=SCHEMA)
    op.drop_table("attendance_event", schema=SCHEMA)
    op.drop_table("term_grade", schema=SCHEMA)
    op.drop_table("student_dimension", schema=SCHEMA)
    op.drop_table("source_manifest", schema=SCHEMA)
    # Keep schema `dwh` (also hosts alembic_version); do not DROP SCHEMA here.
