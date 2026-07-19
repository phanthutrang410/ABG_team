"""Add M10 model artifact provenance to ML snapshots.

Revision ID: 20260719_m10_model_artifact
Revises: 20260719_care_case_viewed
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260719_m10_model_artifact"
down_revision = "20260719_care_case_viewed"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "ml_term_snapshot",
        sa.Column("artifact_sha256", sa.String(length=64), nullable=True),
        schema="dwh",
    )


def downgrade() -> None:
    op.drop_column("ml_term_snapshot", "artifact_sha256", schema="dwh")
