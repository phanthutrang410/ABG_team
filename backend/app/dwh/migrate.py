"""Helpers to run Alembic against a given database URL (H19 tests / CLI)."""

from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config

BACKEND_ROOT = Path(__file__).resolve().parents[2]
ALEMBIC_INI = BACKEND_ROOT / "alembic.ini"
HEAD_REVISION = "20260719_m10_model_artifact"


def make_alembic_config(database_url: str) -> Config:
    cfg = Config(str(ALEMBIC_INI))
    cfg.set_main_option("script_location", str(BACKEND_ROOT / "alembic"))
    cfg.set_main_option("sqlalchemy.url", database_url)
    return cfg


def upgrade_head(database_url: str) -> None:
    command.upgrade(make_alembic_config(database_url), "head")


def downgrade_base(database_url: str) -> None:
    command.downgrade(make_alembic_config(database_url), "base")


def current_revision(database_url: str) -> str | None:
    from sqlalchemy import create_engine, text

    engine = create_engine(database_url)
    with engine.connect() as conn:
        exists = conn.execute(
            text(
                "SELECT 1 FROM information_schema.tables "
                "WHERE table_schema = 'dwh' AND table_name = 'alembic_version'"
            )
        ).scalar()
        if not exists:
            return None
        return conn.execute(text("SELECT version_num FROM dwh.alembic_version")).scalar_one()
