"""H36a — add viewed_at receipt to app.review_case.

Revision ID: 20260719_care_case_viewed
Revises: 20260719_care_case_store
Create Date: 2026-07-19

Adds ``viewed_at`` (nullable timestamp): the first time the assigned GVCN opened
the secured student detail ("đã xem"). Separate from acceptance, which is the
``assigned → follow_up_in_progress`` state transition. Idempotent add.
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260719_care_case_viewed"
down_revision: Union[str, None] = "20260719_care_case_store"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = "app"


def upgrade() -> None:
    op.add_column(
        "review_case",
        sa.Column("viewed_at", sa.DateTime(timezone=True), nullable=True),
        schema=SCHEMA,
    )


def downgrade() -> None:
    op.drop_column("review_case", "viewed_at", schema=SCHEMA)
