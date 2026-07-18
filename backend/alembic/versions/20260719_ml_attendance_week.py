"""Add ml_term_snapshot + attendance_week materialization tables.

Revision ID: 20260719_ml_attendance_week
Revises: 20260719_h39a_auth_rbac
Create Date: 2026-07-19

Empty tables only — writers (score materializer / week rollup) are separate tasks.
Does not add care case-state tables.
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260719_ml_attendance_week"
down_revision: Union[str, None] = "20260719_h39a_auth_rbac"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = "dwh"


def upgrade() -> None:
    op.create_table(
        "ml_term_snapshot",
        sa.Column("source_id", sa.String(length=128), nullable=False),
        sa.Column("student_ref", sa.String(length=128), nullable=False),
        sa.Column("dataset_version", sa.String(length=128), nullable=False),
        sa.Column("model_version", sa.String(length=64), nullable=False),
        sa.Column("threshold_config_version", sa.String(length=64), nullable=False),
        sa.Column("calculated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_term_code", sa.String(length=32), nullable=True),
        sa.Column("latest_term_gpa", sa.Numeric(5, 2), nullable=True),
        sa.Column("grade_trend_slope", sa.Numeric(12, 6), nullable=True),
        sa.Column("grade_volatility", sa.Numeric(12, 6), nullable=True),
        sa.Column("failed_credits", sa.Numeric(8, 2), nullable=True),
        sa.Column("attendance_rate_window", sa.Numeric(6, 4), nullable=True),
        sa.Column("attendance_trend_slope", sa.Numeric(12, 6), nullable=True),
        sa.Column("coverage_status", sa.String(length=32), nullable=False),
        sa.Column("coverage_json", sa.Text(), nullable=False),
        sa.Column("review_priority_band", sa.String(length=32), nullable=True),
        sa.Column(
            "contributing_factors_json",
            sa.Text(),
            nullable=False,
            server_default="[]",
        ),
        sa.Column("model_score", sa.Numeric(6, 4), nullable=True),
        sa.Column("explain_schema_version", sa.String(length=64), nullable=True),
        sa.Column("agent_explain_json", sa.Text(), nullable=True),
        sa.Column("evidence_fingerprint", sa.String(length=128), nullable=True),
        sa.ForeignKeyConstraint(
            ["source_id", "student_ref"],
            [
                f"{SCHEMA}.student_dimension.source_id",
                f"{SCHEMA}.student_dimension.student_ref",
            ],
            name="fk_ml_term_snapshot_student",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("source_id", "student_ref"),
        sa.CheckConstraint(
            "coverage_status IN ('ok', 'partial', 'insufficient')",
            name="ck_ml_term_snapshot_coverage_status",
        ),
        sa.CheckConstraint(
            "review_priority_band IS NULL OR "
            "review_priority_band IN ('uu_tien_som', 'can_ra_soat')",
            name="ck_ml_term_snapshot_band",
        ),
        sa.CheckConstraint(
            "model_score IS NULL OR (model_score >= 0 AND model_score <= 1)",
            name="ck_ml_term_snapshot_model_score",
        ),
        sa.CheckConstraint(
            "latest_term_gpa IS NULL OR (latest_term_gpa >= 0 AND latest_term_gpa <= 10)",
            name="ck_ml_term_snapshot_gpa",
        ),
        sa.CheckConstraint(
            "attendance_rate_window IS NULL OR "
            "(attendance_rate_window >= 0 AND attendance_rate_window <= 1)",
            name="ck_ml_term_snapshot_att_rate",
        ),
        sa.CheckConstraint(
            "failed_credits IS NULL OR failed_credits >= 0",
            name="ck_ml_term_snapshot_failed_credits",
        ),
        schema=SCHEMA,
    )

    op.create_table(
        "attendance_week",
        sa.Column("source_id", sa.String(length=128), nullable=False),
        sa.Column("student_ref", sa.String(length=128), nullable=False),
        sa.Column("week_start_date", sa.Date(), nullable=False),
        sa.Column("week_end_date", sa.Date(), nullable=False),
        sa.Column("n_events", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("n_in_denominator", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("n_present", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("n_absent", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("n_excused_excluded", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("attendance_rate", sa.Numeric(6, 4), nullable=True),
        sa.Column("first_observed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_observed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["source_id", "student_ref"],
            [
                f"{SCHEMA}.student_dimension.source_id",
                f"{SCHEMA}.student_dimension.student_ref",
            ],
            name="fk_attendance_week_student",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("source_id", "student_ref", "week_start_date"),
        sa.CheckConstraint("n_events >= 0", name="ck_attendance_week_n_events"),
        sa.CheckConstraint("n_in_denominator >= 0", name="ck_attendance_week_n_denom"),
        sa.CheckConstraint("n_present >= 0", name="ck_attendance_week_n_present"),
        sa.CheckConstraint("n_absent >= 0", name="ck_attendance_week_n_absent"),
        sa.CheckConstraint("n_excused_excluded >= 0", name="ck_attendance_week_n_excused"),
        sa.CheckConstraint(
            "attendance_rate IS NULL OR (attendance_rate >= 0 AND attendance_rate <= 1)",
            name="ck_attendance_week_rate",
        ),
        sa.CheckConstraint(
            "week_end_date >= week_start_date",
            name="ck_attendance_week_range",
        ),
        sa.CheckConstraint(
            "(n_in_denominator = 0 AND attendance_rate IS NULL) OR "
            "(n_in_denominator > 0 AND attendance_rate IS NOT NULL)",
            name="ck_attendance_week_rate_null_when_empty",
        ),
        schema=SCHEMA,
    )


def downgrade() -> None:
    op.drop_table("attendance_week", schema=SCHEMA)
    op.drop_table("ml_term_snapshot", schema=SCHEMA)
