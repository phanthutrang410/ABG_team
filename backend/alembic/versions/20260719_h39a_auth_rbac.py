"""H39a — app schema auth RBAC tables (accounts, sessions, audit).

Revision ID: 20260719_h39a_auth_rbac
Revises: 20260718_h30_snapshot
Create Date: 2026-07-19

Creates schema ``app`` and four tables. No seed data in this migration.
Does not modify ``dwh`` domain tables.
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260719_h39a_auth_rbac"
down_revision: Union[str, None] = "20260718_h30_snapshot"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = "app"
_ROLE_CHECK = "role IN ('ban_quan_ly', 'gvcn')"
_ACTIVE_ROLE_CHECK = "active_role IS NULL OR active_role IN ('ban_quan_ly', 'gvcn')"
_DECISION_CHECK = "decision IN ('allowed', 'denied')"


def upgrade() -> None:
    op.execute(sa.text(f'CREATE SCHEMA IF NOT EXISTS "{SCHEMA}"'))

    op.create_table(
        "auth_account",
        sa.Column("actor_id", sa.String(length=128), nullable=False),
        sa.Column("username", sa.String(length=64), nullable=False),
        sa.Column("display_name", sa.String(length=256), nullable=False),
        sa.Column("password_hash", sa.String(length=512), nullable=False),
        sa.Column("org_scope", sa.String(length=128), nullable=False),
        sa.Column("advisor_scope", sa.String(length=128), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
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
        sa.PrimaryKeyConstraint("actor_id"),
        sa.UniqueConstraint("username", name="uq_auth_account_username"),
        schema=SCHEMA,
    )

    op.create_table(
        "auth_account_role",
        sa.Column("actor_id", sa.String(length=128), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.ForeignKeyConstraint(
            ["actor_id"],
            [f"{SCHEMA}.auth_account.actor_id"],
            name="fk_auth_account_role_account",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("actor_id", "role"),
        sa.CheckConstraint(_ROLE_CHECK, name="ck_auth_account_role_valid"),
        schema=SCHEMA,
    )

    op.create_table(
        "auth_session",
        sa.Column("session_id", sa.String(length=64), nullable=False),
        sa.Column("actor_id", sa.String(length=128), nullable=False),
        sa.Column("token_hash", sa.String(length=128), nullable=False),
        sa.Column("active_role", sa.String(length=32), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(
            ["actor_id"],
            [f"{SCHEMA}.auth_account.actor_id"],
            name="fk_auth_session_account",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("session_id"),
        sa.UniqueConstraint("token_hash", name="uq_auth_session_token_hash"),
        sa.CheckConstraint(_ACTIVE_ROLE_CHECK, name="ck_auth_session_active_role"),
        schema=SCHEMA,
    )
    op.create_index(
        "ix_auth_session_actor_id",
        "auth_session",
        ["actor_id"],
        schema=SCHEMA,
    )

    op.create_table(
        "access_audit_event",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("actor_id", sa.String(length=128), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("action", sa.String(length=128), nullable=False),
        sa.Column("resource_handle", sa.String(length=256), nullable=False),
        sa.Column("decision", sa.String(length=16), nullable=False),
        sa.Column(
            "at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(_DECISION_CHECK, name="ck_access_audit_decision"),
        schema=SCHEMA,
    )
    op.create_index(
        "ix_access_audit_event_at",
        "access_audit_event",
        ["at"],
        schema=SCHEMA,
    )


def downgrade() -> None:
    op.drop_index("ix_access_audit_event_at", table_name="access_audit_event", schema=SCHEMA)
    op.drop_table("access_audit_event", schema=SCHEMA)
    op.drop_index("ix_auth_session_actor_id", table_name="auth_session", schema=SCHEMA)
    op.drop_table("auth_session", schema=SCHEMA)
    op.drop_table("auth_account_role", schema=SCHEMA)
    op.drop_table("auth_account", schema=SCHEMA)
    op.execute(sa.text(f'DROP SCHEMA IF EXISTS "{SCHEMA}" CASCADE'))
