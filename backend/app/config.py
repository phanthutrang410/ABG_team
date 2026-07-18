"""Application settings."""

from __future__ import annotations

from functools import lru_cache
from typing import Optional
from urllib.parse import urlparse

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_ALLOWED_FPT_HOSTS = frozenset({"mkp-api.fptcloud.com"})
_ALLOWED_OPENAI_HOSTS = frozenset({"api.openai.com"})


class Settings(BaseSettings):
    database_url: str = (
        "postgresql+psycopg://silentshield:silentshield@localhost:5432/silentshield"
    )
    # H29 target provider
    openai_api_key: SecretStr = SecretStr("")
    openai_base_url: str = "https://api.openai.com"
    openai_model: str = "gpt-4.1-mini"
    openai_max_output_tokens: int = Field(default=512, ge=1, le=512)
    openai_max_response_bytes: int = Field(default=16 * 1024, ge=1, le=16 * 1024)
    # Legacy H23–H26 FPT settings (inactive path after H29; kept for historical tests)
    fpt_api_key: SecretStr = SecretStr("")
    fpt_base_url: str = "https://mkp-api.fptcloud.com"
    fpt_model: str = "Qwen/Qwen3-32B"
    fpt_max_tokens: int = Field(default=512, ge=1, le=512)
    fpt_max_response_bytes: int = Field(default=16 * 1024, ge=1, le=16 * 1024)
    max_concurrent_agent_runs: int = Field(default=3, ge=1)
    agent_run_timeout_seconds: int = Field(default=30, ge=1, le=30)

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

    @field_validator("agent_run_timeout_seconds", mode="before")
    @classmethod
    def _cap_agent_timeout(cls, value: object) -> object:
        """Inference timeout is hard-capped at 30s (doc 12 §6); clamp legacy env."""
        if value is None or value == "":
            return 30
        try:
            number = int(value)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return value
        return min(max(number, 1), 30)

    @field_validator("fpt_max_tokens", mode="before")
    @classmethod
    def _cap_fpt_max_tokens(cls, value: object) -> object:
        if value is None or value == "":
            return 512
        try:
            number = int(value)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return value
        return min(max(number, 1), 512)

    @field_validator("fpt_base_url")
    @classmethod
    def _fpt_base_url_https_allowlist(cls, value: str) -> str:
        parsed = urlparse(value)
        if parsed.scheme != "https":
            raise ValueError("fpt_base_url must use HTTPS")
        host = (parsed.hostname or "").lower()
        if host not in _ALLOWED_FPT_HOSTS:
            raise ValueError(
                "fpt_base_url host must be mkp-api.fptcloud.com"
            )
        return value.rstrip("/")

    @field_validator("openai_base_url")
    @classmethod
    def _openai_base_url_https_allowlist(cls, value: str) -> str:
        parsed = urlparse(value)
        if parsed.scheme != "https":
            raise ValueError("openai_base_url must use HTTPS")
        host = (parsed.hostname or "").lower()
        if host not in _ALLOWED_OPENAI_HOSTS:
            raise ValueError("openai_base_url host must be api.openai.com")
        return value.rstrip("/")

    @field_validator("openai_max_output_tokens", mode="before")
    @classmethod
    def _cap_openai_max_output_tokens(cls, value: object) -> object:
        if value is None or value == "":
            return 512
        try:
            number = int(value)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return value
        return min(max(number, 1), 512)


@lru_cache
def get_settings() -> Settings:
    return Settings()
