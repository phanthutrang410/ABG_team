"""D460-08 — durable care CaseStore tables in app schema.

Revision ID: 20260719_care_case_store
Revises: 20260719_ml_attendance_week
Create Date: 2026-07-19

Creates ``app.review_case`` (CaseSnapshot current state) and append-only
``app.case_event``. Does not modify ``dwh`` domain tables.
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260719_care_case_store"
down_revision: Union[str, None] = "20260719_ml_attendance_week"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = "app"

_STATE_CHECK = (
    "state IN ("
    "'new_signal', 'pending_review', 'approved_for_follow_up', 'dismissed', "
    "'assigned', 'follow_up_in_progress', 'resolved', 'monitoring'"
    ")"
)


def upgrade() -> None:
    op.execute(sa.text(f'CREATE SCHEMA IF NOT EXISTS "{SCHEMA}"'))

    op.create_table(
        "review_case",
        sa.Column("case_id", sa.String(length=128), nullable=False),
        sa.Column("state", sa.String(length=64), nullable=False),
        sa.Column("student_ref", sa.String(length=128), nullable=True),
        sa.Column("source_id", sa.String(length=128), nullable=True),
        sa.Column("advisor_ref", sa.String(length=128), nullable=True),
        sa.Column("review_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reason_code", sa.String(length=128), nullable=True),
        sa.Column("monitoring_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "mapping_repair_queued",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("case_id"),
        sa.CheckConstraint(_STATE_CHECK, name="ck_review_case_state"),
        schema=SCHEMA,
    )
    op.create_index(
        "ix_review_case_student_ref",
        "review_case",
        ["student_ref"],
        schema=SCHEMA,
    )
    op.create_index(
        "ix_review_case_advisor_ref",
        "review_case",
        ["advisor_ref"],
        schema=SCHEMA,
    )
    op.create_index(
        "ix_review_case_state",
        "review_case",
        ["state"],
        schema=SCHEMA,
    )

    op.create_table(
        "case_event",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("case_id", sa.String(length=128), nullable=False),
        sa.Column("kind", sa.String(length=64), nullable=False),
        sa.Column("actor", sa.String(length=128), nullable=False),
        sa.Column(
            "actor_kind",
            sa.String(length=32),
            nullable=False,
            server_default="human",
        ),
        sa.Column("action", sa.String(length=64), nullable=True),
        sa.Column("from_state", sa.String(length=64), nullable=True),
        sa.Column("to_state", sa.String(length=64), nullable=True),
        sa.Column("detail_json", sa.Text(), nullable=True),
        sa.Column(
            "occurred_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(
            ["case_id"],
            [f"{SCHEMA}.review_case.case_id"],
            name="fk_case_event_review_case",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        schema=SCHEMA,
    )
    op.create_index(
        "ix_case_event_case_id",
        "case_event",
        ["case_id"],
        schema=SCHEMA,
    )
    op.create_index(
        "ix_case_event_occurred_at",
        "case_event",
        ["occurred_at"],
        schema=SCHEMA,
    )


def downgrade() -> None:
    op.drop_index("ix_case_event_occurred_at", table_name="case_event", schema=SCHEMA)
    op.drop_index("ix_case_event_case_id", table_name="case_event", schema=SCHEMA)
    op.drop_table("case_event", schema=SCHEMA)
    op.drop_index("ix_review_case_state", table_name="review_case", schema=SCHEMA)
    op.drop_index("ix_review_case_advisor_ref", table_name="review_case", schema=SCHEMA)
    op.drop_index("ix_review_case_student_ref", table_name="review_case", schema=SCHEMA)
    op.drop_table("review_case", schema=SCHEMA)
