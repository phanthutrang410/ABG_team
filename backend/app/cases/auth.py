"""Care deploy-blocker: seed create gate + server-derived actor (H06b harden)."""

from __future__ import annotations

from typing import Optional, Tuple

from app.cases.domain import (
    AGENT_ACTOR_KINDS,
    TransitionError,
    TransitionErrorCode,
)
from app.config import Settings, get_settings

# Local/dev/test may seed cases; Live/production must not expose open create.
_SEED_CREATE_ENVS = frozenset({"local", "dev", "development", "test"})


def seed_create_allowed(settings: Optional[Settings] = None) -> bool:
    """True only for seed/local-style envs (or explicit CASES_SEED_CREATE=true)."""
    cfg = settings or get_settings()
    if cfg.cases_seed_create is not None:
        return cfg.cases_seed_create
    return cfg.app_env.strip().lower() in _SEED_CREATE_ENVS


def resolve_trusted_actor(
    client_actor: Optional[str],
    client_actor_kind: Optional[str],
    *,
    settings: Optional[Settings] = None,
) -> Tuple[str, str]:
    """
    Derive actor from server settings. Do not trust client identity.

    - Agent/LLM kinds from the client are always rejected.
    - Any non-empty client actor/kind that differs from the trusted demo
      identity is rejected as spoofing.
    """
    cfg = settings or get_settings()
    trusted_actor = cfg.cases_trusted_actor.strip()
    trusted_kind = (cfg.cases_trusted_actor_kind or "human").strip().lower()

    if not trusted_actor:
        raise TransitionError(
            TransitionErrorCode.MISSING_ACTOR,
            "server trusted actor is not configured",
        )

    if client_actor_kind is not None and client_actor_kind.strip():
        kind = client_actor_kind.strip().lower()
        if kind in AGENT_ACTOR_KINDS:
            raise TransitionError(
                TransitionErrorCode.AGENT_FORBIDDEN,
                "Agent/LLM must not change case state (Process §4.3 / Ethics §8)",
            )
        if kind != trusted_kind:
            raise TransitionError(
                TransitionErrorCode.UNTRUSTED_ACTOR,
                "actor_kind from client does not match server identity",
            )

    if client_actor is not None and client_actor.strip():
        if client_actor.strip() != trusted_actor:
            raise TransitionError(
                TransitionErrorCode.UNTRUSTED_ACTOR,
                "actor from client does not match server identity",
            )

    return trusted_actor, trusted_kind
