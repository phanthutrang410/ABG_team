"""Optional LangSmith tracing for agent runs — default off, redacted metadata only.

Privacy (doc 12 §6 / Ethics §8): never send raw question, prompt, context,
answer/draft, secrets, or chain-of-thought. Spans carry surface/status/route
codes and length counters only.

Activate when Settings has ``langsmith_tracing=true`` and a non-empty
``langsmith_api_key``, and the optional ``langsmith`` package is installed:
``pip install -e ".[observability]"``.
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Any, Callable, Dict, Iterator, Optional, TypeVar

F = TypeVar("F", bound=Callable[..., Any])

_CONFIGURED = False


def _secret_value(value: Any) -> str:
    if value is None:
        return ""
    if hasattr(value, "get_secret_value"):
        return str(value.get_secret_value() or "")
    return str(value or "")


def tracing_armed(settings: Any = None) -> bool:
    """True only when Settings enable tracing and an API key is present."""
    if settings is None:
        from app.config import get_settings

        settings = get_settings()
    if not bool(getattr(settings, "langsmith_tracing", False)):
        return False
    return bool(_secret_value(getattr(settings, "langsmith_api_key", "")).strip())


def configure_langsmith(settings: Any = None) -> bool:
    """Sync Settings → process env for the LangSmith SDK. Returns armed state.

    When not armed, forces ``LANGSMITH_TRACING=false`` so ambient shell env
    cannot accidentally upload traces from local/CI.
    """
    global _CONFIGURED
    if settings is None:
        from app.config import get_settings

        settings = get_settings()

    armed = tracing_armed(settings)
    if not armed:
        os.environ["LANGSMITH_TRACING"] = "false"
        os.environ["LANGCHAIN_TRACING_V2"] = "false"
        # Do not leave a previously configured key/project in the process when
        # tracing is disabled at runtime or by a test/deploy kill switch.
        for name in (
            "LANGSMITH_API_KEY",
            "LANGSMITH_PROJECT",
            "LANGSMITH_ENDPOINT",
            "LANGCHAIN_API_KEY",
            "LANGCHAIN_PROJECT",
        ):
            os.environ.pop(name, None)
        _CONFIGURED = True
        return False

    key = _secret_value(settings.langsmith_api_key).strip()
    project = str(getattr(settings, "langsmith_project", "") or "silent-shield").strip()
    endpoint = str(
        getattr(settings, "langsmith_endpoint", "") or "https://api.smith.langchain.com"
    ).strip()

    os.environ["LANGSMITH_TRACING"] = "true"
    os.environ["LANGSMITH_API_KEY"] = key
    os.environ["LANGSMITH_PROJECT"] = project or "silent-shield"
    if endpoint:
        os.environ["LANGSMITH_ENDPOINT"] = endpoint
    # Prefer LANGSMITH_*; keep legacy aliases for older SDK builds.
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = key
    os.environ["LANGCHAIN_PROJECT"] = project or "silent-shield"
    _CONFIGURED = True
    return True


def is_configured() -> bool:
    return _CONFIGURED


def _langsmith_traceable() -> Optional[Callable[..., Any]]:
    try:
        from langsmith import traceable
    except ImportError:
        return None
    return traceable


def redact_turn_inputs(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Safe metadata for ``run_turn`` / ``run_overview_graph``."""
    request = inputs.get("request")
    principal = inputs.get("principal")
    question = getattr(request, "question", None) if request is not None else None
    handle = getattr(request, "resource_handle", None) if request is not None else None
    summary = getattr(request, "thread_summary", None) if request is not None else None
    out: Dict[str, Any] = {
        "surface": getattr(request, "surface", None) if request is not None else None,
        "locale": getattr(request, "locale", None) if request is not None else None,
        "has_question": bool(question),
        "question_chars": len(question) if isinstance(question, str) else 0,
        "has_resource_handle": bool(handle),
        "has_thread_summary": bool(summary),
        "thread_summary_chars": len(summary) if isinstance(summary, str) else 0,
        "model_injected": inputs.get("model") is not None,
    }
    if principal is not None:
        out["role"] = getattr(principal, "active_role", None)
        # Pseudonymous actor id (acct:…) — no student_ref / PII.
        out["actor_id"] = getattr(principal, "actor_id", None)
    caps = inputs.get("allowed_capabilities")
    if caps is not None:
        out["allowed_capability_count"] = len(tuple(caps))
    facts = inputs.get("facts") or inputs.get("overview_facts")
    if isinstance(facts, dict):
        out["fact_keys"] = sorted(str(k) for k in facts.keys())[:24]
    return out


def redact_turn_outputs(outputs: Any) -> Dict[str, Any]:
    """Safe metadata for AgentTurnResponse — never ``answer_vi``."""
    if outputs is None:
        return {}
    status = getattr(outputs, "status", None)
    refusal = getattr(outputs, "refusal_reason", None)
    actions = getattr(outputs, "ui_actions", None) or []
    refs = getattr(outputs, "evidence_refs", None) or []
    return {
        "status": getattr(status, "value", status),
        "refusal_reason": getattr(refusal, "value", refusal),
        "selected_capability": getattr(outputs, "selected_capability", None),
        "ui_action_count": len(actions),
        "ui_action_keys": [
            getattr(a, "key", None) for a in actions if getattr(a, "key", None)
        ],
        "evidence_refs": list(refs)[:20],
        # Length only — never the prose.
        "answer_chars": len(getattr(outputs, "answer_vi", "") or ""),
    }


def redact_explanation_inputs(inputs: Dict[str, Any]) -> Dict[str, Any]:
    command = inputs.get("command")
    return {
        "case_id_present": bool(inputs.get("case_id")),
        "intent": getattr(command, "intent", None) if command is not None else None,
        "locale": getattr(command, "locale", None) if command is not None else None,
        "has_question": bool(getattr(command, "question", None))
        if command is not None
        else False,
        "question_chars": len(getattr(command, "question", "") or "")
        if command is not None
        else 0,
        "model_type": type(inputs.get("model")).__name__
        if inputs.get("model") is not None
        else None,
    }


def redact_explanation_outputs(outputs: Any) -> Dict[str, Any]:
    if outputs is None:
        return {}
    status = getattr(outputs, "status", None)
    refusal = getattr(outputs, "refusal_reason", None)
    return {
        "status": getattr(status, "value", status),
        "refusal_reason": getattr(refusal, "value", refusal),
        "model_version": getattr(outputs, "model_version", None),
        "answer_chars": len(getattr(outputs, "answer_vi", "") or ""),
        "has_draft": getattr(outputs, "draft_message", None) is not None,
    }


def redact_llm_inputs(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Never forward system/user prompt bodies."""
    return {
        "model": inputs.get("model"),
        "name": inputs.get("name"),
        "system_chars": inputs.get("system_chars"),
        "user_chars": inputs.get("user_chars"),
        "structured_json": bool(inputs.get("structured_json")),
    }


def redact_llm_outputs(outputs: Any) -> Dict[str, Any]:
    if isinstance(outputs, dict):
        return {"result_keys": sorted(str(k) for k in outputs.keys())[:24]}
    if isinstance(outputs, str):
        return {"result_chars": len(outputs)}
    return {"result_type": type(outputs).__name__}


def trace_agent_run(
    name: str,
    *,
    run_type: str = "chain",
    process_inputs: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None,
    process_outputs: Optional[Callable[[Any], Dict[str, Any]]] = None,
) -> Callable[[F], F]:
    """Apply LangSmith ``@traceable`` when the package is installed; else no-op."""

    def decorator(fn: F) -> F:
        traceable = _langsmith_traceable()
        if traceable is None:
            return fn
        return traceable(  # type: ignore[return-value]
            name=name,
            run_type=run_type,
            process_inputs=process_inputs or (lambda inputs: {}),
            process_outputs=process_outputs or (lambda outputs: {}),
        )(fn)

    return decorator


@contextmanager
def llm_span(
    *,
    name: str,
    model: str,
    system_chars: int,
    user_chars: int,
    structured_json: bool = False,
) -> Iterator[None]:
    """Child LLM span with redacted metadata — no prompt/response bodies."""
    if os.environ.get("LANGSMITH_TRACING", "").lower() not in ("1", "true", "yes"):
        yield
        return
    try:
        from langsmith import trace
    except ImportError:
        yield
        return

    with trace(
        name=name,
        run_type="llm",
        inputs=redact_llm_inputs(
            {
                "model": model,
                "name": name,
                "system_chars": system_chars,
                "user_chars": user_chars,
                "structured_json": structured_json,
            }
        ),
        outputs={"ok": True},
    ):
        yield
