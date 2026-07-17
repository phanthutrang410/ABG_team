"""Application settings."""

from __future__ import annotations

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = (
        "postgresql+psycopg://silentshield:silentshield@localhost:5432/silentshield"
    )
    fpt_api_key: str = ""
    fpt_base_url: str = "https://mkp-api.fptcloud.com"
    fpt_model: str = "Qwen/Qwen3-32B"
    max_concurrent_agent_runs: int = 3
    agent_run_timeout_seconds: int = 120
    langchain_tracing_v2: bool = False
    langchain_api_key: str = ""
    langchain_project: str = "silent-shield"

    # Care /cases harden (H06b deploy-blocker)
    app_env: str = "local"
    # None = derive from app_env (local/dev/test only); explicit bool overrides.
    cases_seed_create: Optional[bool] = None
    cases_trusted_actor: str = "leader:demo"
    cases_trusted_actor_kind: str = "human"

    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
