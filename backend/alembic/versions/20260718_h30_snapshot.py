"""H30 — snapshot v2 registry + workflow ledger tables.

Revision ID: 20260718_h30_snapshot
Revises: 20260718_h19_dwh
Create Date: 2026-07-18

Adds dataset_source / dataset_snapshot / active_dataset_snapshot /
workflow_run / workflow_step_run. Migrates existing source_manifest rows
into dataset_snapshot as first versions (legacy_source_id preserved).
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260718_h30_snapshot"
down_revision: Union[str, None] = "20260718_h19_dwh"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = "dwh"


def upgrade() -> None:
    op.create_table(
        "dataset_source",
        sa.Column("dataset_key", sa.String(length=128), nullable=False),
        sa.Column("source_owner", sa.String(length=128), nullable=True),
        sa.Column("retention_policy", sa.String(length=128), nullable=True),
        sa.Column("usage_notes", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("dataset_key"),
        schema=SCHEMA,
    )

    op.create_table(
        "dataset_snapshot",
        sa.Column("snapshot_id", sa.String(length=128), nullable=False),
        sa.Column("dataset_key", sa.String(length=128), nullable=False),
        sa.Column("previous_snapshot_id", sa.String(length=128), nullable=True),
        sa.Column("supersedes_snapshot_id", sa.String(length=128), nullable=True),
        sa.Column("period_start", sa.String(length=32), nullable=True),
        sa.Column("period_end", sa.String(length=32), nullable=True),
        sa.Column("extracted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("schema_version", sa.String(length=64), nullable=False),
        sa.Column("pseudonym_namespace_version", sa.String(length=64), nullable=False),
        sa.Column("source_snapshot_sha256", sa.String(length=64), nullable=False),
        sa.Column("normalized_artifact_sha256", sa.String(length=64), nullable=True),
        sa.Column("dataset_content_sha256", sa.String(length=64), nullable=False),
        sa.Column("approval_id", sa.String(length=128), nullable=True),
        sa.Column("provenance_approved", sa.Boolean(), nullable=False),
        sa.Column("fixture_mode", sa.String(length=64), nullable=True),
        sa.Column("legacy_source_id", sa.String(length=128), nullable=True),
        sa.Column("row_counts_json", sa.Text(), nullable=True),
        sa.Column("quality_reason_codes", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="staged"),
        sa.ForeignKeyConstraint(
            ["dataset_key"],
            [f"{SCHEMA}.dataset_source.dataset_key"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("snapshot_id"),
        sa.UniqueConstraint(
            "dataset_key",
            "dataset_content_sha256",
            name="uq_dataset_snapshot_content_hash",
        ),
        sa.CheckConstraint(
            "char_length(source_snapshot_sha256) = 64",
            name="ck_dataset_snapshot_source_sha_len",
        ),
        sa.CheckConstraint(
            "char_length(dataset_content_sha256) = 64",
            name="ck_dataset_snapshot_content_sha_len",
        ),
        sa.CheckConstraint(
            "status IN ('staged', 'active', 'superseded', 'rejected')",
            name="ck_dataset_snapshot_status",
        ),
        schema=SCHEMA,
    )

    op.create_table(
        "active_dataset_snapshot",
        sa.Column("dataset_key", sa.String(length=128), nullable=False),
        sa.Column("snapshot_id", sa.String(length=128), nullable=False),
        sa.Column("promoted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("promoted_by_run_id", sa.String(length=128), nullable=True),
        sa.ForeignKeyConstraint(
            ["dataset_key"],
            [f"{SCHEMA}.dataset_source.dataset_key"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["snapshot_id"],
            [f"{SCHEMA}.dataset_snapshot.snapshot_id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("dataset_key"),
        schema=SCHEMA,
    )

    op.create_table(
        "workflow_run",
        sa.Column("run_id", sa.String(length=128), nullable=False),
        sa.Column("dataset_key", sa.String(length=128), nullable=False),
        sa.Column("snapshot_id", sa.String(length=128), nullable=True),
        sa.Column("trigger_kind", sa.String(length=64), nullable=False),
        sa.Column("idempotency_key", sa.String(length=256), nullable=False),
        sa.Column("workflow_version", sa.String(length=64), nullable=False),
        sa.Column("model_version", sa.String(length=64), nullable=True),
        sa.Column("threshold_config_version", sa.String(length=64), nullable=True),
        sa.Column("dataset_content_sha256", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("failure_reason_code", sa.String(length=128), nullable=True),
        sa.Column("replay_of_run_id", sa.String(length=128), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("run_id"),
        sa.UniqueConstraint(
            "dataset_content_sha256",
            "workflow_version",
            "idempotency_key",
            name="uq_workflow_run_idempotency",
        ),
        sa.CheckConstraint(
            "status IN ("
            "'queued','validating','staging','scoring','reconciling',"
            "'reporting','publishing','succeeded','failed','duplicate'"
            ")",
            name="ck_workflow_run_status",
        ),
        schema=SCHEMA,
    )

    op.create_table(
        "workflow_step_run",
        sa.Column("step_run_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("run_id", sa.String(length=128), nullable=False),
        sa.Column("step_name", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("reason_code", sa.String(length=128), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["run_id"],
            [f"{SCHEMA}.workflow_run.run_id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("step_run_id"),
        sa.UniqueConstraint("run_id", "step_name", name="uq_workflow_step_run_name"),
        sa.CheckConstraint(
            "status IN ('queued','running','succeeded','failed','skipped')",
            name="ck_workflow_step_status",
        ),
        schema=SCHEMA,
    )

    # Backfill: each existing source_manifest becomes dataset_key + first snapshot.
    conn = op.get_bind()
    rows = conn.execute(
        sa.text(
            "SELECT source_id, snapshot_sha256, provenance_approved, "
            "schema_version, record_count, extracted_at FROM dwh.source_manifest"
        )
    ).mappings().all()
    for row in rows:
        dataset_key = row["source_id"]
        snapshot_id = f"snap-v1-{dataset_key}"
        conn.execute(
            sa.text(
                "INSERT INTO dwh.dataset_source (dataset_key, source_owner, retention_policy, usage_notes) "
                "VALUES (:k, :owner, :ret, :notes) ON CONFLICT DO NOTHING"
            ),
            {
                "k": dataset_key,
                "owner": "mvp-demo",
                "ret": "90d-metadata",
                "notes": "migrated from source_manifest (H30)",
            },
        )
        conn.execute(
            sa.text(
                "INSERT INTO dwh.dataset_snapshot ("
                "snapshot_id, dataset_key, extracted_at, schema_version, "
                "pseudonym_namespace_version, source_snapshot_sha256, "
                "dataset_content_sha256, provenance_approved, legacy_source_id, "
                "fixture_mode, status, row_counts_json"
                ") VALUES ("
                ":sid, :k, :ext, :sv, :ns, :sha, :sha, :prov, :legacy, "
                "'legacy_source_manifest', 'active', :counts"
                ")"
            ),
            {
                "sid": snapshot_id,
                "k": dataset_key,
                "ext": row["extracted_at"],
                "sv": row["schema_version"],
                "ns": "approval:pending-linked-namespace",
                "sha": row["snapshot_sha256"],
                "prov": row["provenance_approved"],
                "legacy": dataset_key,
                "counts": f'{{"record_count":{int(row["record_count"])}}}',
            },
        )
        conn.execute(
            sa.text(
                "INSERT INTO dwh.active_dataset_snapshot "
                "(dataset_key, snapshot_id, promoted_at, promoted_by_run_id) "
                "VALUES (:k, :sid, :ext, NULL) ON CONFLICT DO NOTHING"
            ),
            {"k": dataset_key, "sid": snapshot_id, "ext": row["extracted_at"]},
        )


def downgrade() -> None:
    op.drop_table("workflow_step_run", schema=SCHEMA)
    op.drop_table("workflow_run", schema=SCHEMA)
    op.drop_table("active_dataset_snapshot", schema=SCHEMA)
    op.drop_table("dataset_snapshot", schema=SCHEMA)
    op.drop_table("dataset_source", schema=SCHEMA)
