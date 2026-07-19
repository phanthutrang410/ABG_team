"""OpenAI Responses API adapter (H29) — store=false, no FPT fallback.

Text-in/text-out only. Tests inject urllib mocks; live HTTP is not used in
default CI. Secrets never appear in repr/logs.
"""

from __future__ import annotations

import json
import threading
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Optional
from urllib import error, request
from urllib.parse import urlparse

from app.agent.model import ModelUnavailable

if TYPE_CHECKING:
    from app.config import Settings

ALLOWED_OPENAI_HOSTS = frozenset({"api.openai.com"})
DEFAULT_BASE_URL = "https://api.openai.com"
MAX_TIMEOUT_SECONDS = 30.0
MAX_OUTPUT_TOKENS = 512
MAX_RESPONSE_BYTES = 16 * 1024
DEFAULT_MAX_CONCURRENT = 3
# Forbidden keys that must never appear in the outbound Responses body.
_FORBIDDEN_REQUEST_KEYS = frozenset(
    {
        "student_ref",
        "student_id",
        "mssv",
        "email",
        "phone",
        "model_score",
        "raw_score",
        "question",
    }
)


def _llm_span_cm(
    *,
    name: str,
    model: str,
    system: str,
    user: str,
    structured_json: bool,
):
    """Lazy import so OpenAI transport stays usable without langsmith installed."""
    from app.agent.tracing import llm_span

    return llm_span(
        name=name,
        model=model,
        system_chars=len(system),
        user_chars=len(user),
        structured_json=structured_json,
    )


def _validate_https_allowlisted_base_url(base_url: str) -> str:
    parsed = urlparse(base_url)
    if parsed.scheme != "https":
        raise ModelUnavailable("OpenAI base URL must use HTTPS")
    host = (parsed.hostname or "").lower()
    if host not in ALLOWED_OPENAI_HOSTS:
        raise ModelUnavailable("OpenAI base URL host is not allowlisted")
    return base_url.rstrip("/")


def assert_no_forbidden_request_keys(body: dict[str, Any]) -> None:
    """Fail closed if outbound body carries forbidden application fields."""
    stack: list[Any] = [body]
    while stack:
        cur = stack.pop()
        if isinstance(cur, dict):
            for key, value in cur.items():
                if key in _FORBIDDEN_REQUEST_KEYS:
                    raise ModelUnavailable(
                        f"OpenAI request contains forbidden field: {key}"
                    )
                stack.append(value)
        elif isinstance(cur, list):
            stack.extend(cur)


@dataclass
class OpenAIResponsesClient:
    api_key: str
    base_url: str = DEFAULT_BASE_URL
    model: str = "gpt-5.4-nano"
    timeout_seconds: float = 30.0
    max_output_tokens: int = 512
    max_concurrent: int = DEFAULT_MAX_CONCURRENT
    max_response_bytes: int = MAX_RESPONSE_BYTES
    _semaphore: threading.BoundedSemaphore = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "api_key", self.api_key)
        if self.timeout_seconds <= 0 or self.timeout_seconds > MAX_TIMEOUT_SECONDS:
            raise ValueError(
                f"timeout_seconds must be in (0, {MAX_TIMEOUT_SECONDS}]"
            )
        if self.max_output_tokens <= 0 or self.max_output_tokens > MAX_OUTPUT_TOKENS:
            raise ValueError(f"max_output_tokens must be in (1, {MAX_OUTPUT_TOKENS}]")
        if self.max_concurrent < 1:
            raise ValueError("max_concurrent must be >= 1")
        if self.max_response_bytes < 1 or self.max_response_bytes > MAX_RESPONSE_BYTES:
            raise ValueError(
                f"max_response_bytes must be in (1, {MAX_RESPONSE_BYTES}]"
            )
        object.__setattr__(
            self,
            "base_url",
            _validate_https_allowlisted_base_url(self.base_url),
        )
        object.__setattr__(
            self,
            "_semaphore",
            threading.BoundedSemaphore(self.max_concurrent),
        )

    def __repr__(self) -> str:
        return (
            f"OpenAIResponsesClient(base_url={self.base_url!r}, model={self.model!r}, "
            f"timeout_seconds={self.timeout_seconds}, "
            f"max_output_tokens={self.max_output_tokens}, "
            f"api_key={'***' if self.api_key else ''!r})"
        )

    @classmethod
    def from_settings(cls, settings: "Settings") -> "OpenAIResponsesClient":
        key = settings.openai_api_key
        if hasattr(key, "get_secret_value"):
            key = key.get_secret_value()
        timeout = min(float(settings.agent_run_timeout_seconds), MAX_TIMEOUT_SECONDS)
        return cls(
            api_key=str(key or ""),
            base_url=settings.openai_base_url,
            model=settings.openai_model,
            timeout_seconds=timeout,
            max_output_tokens=min(int(settings.openai_max_output_tokens), MAX_OUTPUT_TOKENS),
            max_concurrent=int(settings.max_concurrent_agent_runs),
            max_response_bytes=min(
                int(settings.openai_max_response_bytes), MAX_RESPONSE_BYTES
            ),
        )

    def complete(self, *, system: str, user: str) -> str:
        return self._complete_raw(system=system, user=user, text_format=None)

    def complete_json(
        self,
        *,
        system: str,
        user: str,
        schema: dict[str, Any],
        name: str = "result",
    ) -> dict[str, Any]:
        """Responses API structured JSON (store=false). Returns a parsed object."""
        if not isinstance(schema, dict) or not schema:
            raise ModelUnavailable("JSON schema is required")
        text_format = {
            "format": {
                "type": "json_schema",
                "name": name[:64] or "result",
                "strict": True,
                "schema": schema,
            }
        }
        raw = self._complete_raw(system=system, user=user, text_format=text_format)
        try:
            payload = json.loads(raw)
        except (ValueError, TypeError) as exc:
            raise ModelUnavailable("OpenAI JSON response is not valid JSON") from exc
        if not isinstance(payload, dict):
            raise ModelUnavailable("OpenAI JSON response must be an object")
        return payload

    def _complete_raw(
        self,
        *,
        system: str,
        user: str,
        text_format: Optional[dict[str, Any]],
    ) -> str:
        if not self.api_key.strip():
            raise ModelUnavailable("OPENAI_API_KEY is not configured")

        body_obj: dict[str, Any] = {
            "model": self.model,
            "store": False,
            "temperature": 0,
            "max_output_tokens": self.max_output_tokens,
            "input": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        if text_format is not None:
            body_obj["text"] = text_format
        assert_no_forbidden_request_keys(body_obj)
        if body_obj.get("store") is not False:
            raise ModelUnavailable("OpenAI store must be false")

        body = json.dumps(body_obj).encode("utf-8")
        if len(body) > MAX_RESPONSE_BYTES:
            raise ModelUnavailable("OpenAI request body exceeds size limit")

        req = request.Request(
            f"{self.base_url}/v1/responses",
            data=body,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        acquired = self._semaphore.acquire(blocking=True, timeout=self.timeout_seconds)
        if not acquired:
            raise ModelUnavailable("OpenAI concurrency limit reached")
        span_name = "openai_complete_json" if text_format is not None else "openai_complete"
        format_name = "result"
        if isinstance(text_format, dict):
            fmt = text_format.get("format")
            if isinstance(fmt, dict) and isinstance(fmt.get("name"), str):
                format_name = fmt["name"]
        try:
            with _llm_span_cm(
                name=format_name if text_format is not None else span_name,
                model=self.model,
                system=system,
                user=user,
                structured_json=text_format is not None,
            ):
                return self._do_request(req)
        finally:
            self._semaphore.release()

    def _do_request(self, req: request.Request) -> str:
        try:
            with request.urlopen(req, timeout=self.timeout_seconds) as response:
                raw = response.read(self.max_response_bytes + 1)
        except error.HTTPError as exc:
            try:
                exc.read(self.max_response_bytes + 1)
            except Exception:  # noqa: BLE001
                pass
            if exc.code in (401, 429):
                raise ModelUnavailable(
                    f"OpenAI inference rejected with HTTP {exc.code}"
                ) from exc
            raise ModelUnavailable(
                f"OpenAI inference unavailable (HTTP {exc.code})"
            ) from exc
        except TimeoutError as exc:
            raise ModelUnavailable("OpenAI inference timed out") from exc
        except error.URLError as exc:
            reason = getattr(exc, "reason", None)
            if isinstance(reason, TimeoutError) or "timed out" in str(exc).lower():
                raise ModelUnavailable("OpenAI inference timed out") from exc
            raise ModelUnavailable("OpenAI inference unavailable or malformed") from exc
        except (ValueError, UnicodeError) as exc:
            raise ModelUnavailable("OpenAI inference unavailable or malformed") from exc

        if len(raw) > self.max_response_bytes:
            raise ModelUnavailable("OpenAI response exceeds size limit")

        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ModelUnavailable("OpenAI response is not valid UTF-8") from exc

        try:
            payload = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ModelUnavailable("OpenAI response is not JSON") from exc

        return self._extract_content(payload)

    @staticmethod
    def _extract_content(payload: object) -> str:
        if not isinstance(payload, dict):
            raise ModelUnavailable("OpenAI response shape is invalid")

        # Preferred: Responses API output_text convenience field.
        output_text = payload.get("output_text")
        if isinstance(output_text, str) and output_text.strip():
            return output_text.strip()

        output = payload.get("output")
        if isinstance(output, list):
            chunks: list[str] = []
            for item in output:
                if not isinstance(item, dict):
                    continue
                if item.get("type") not in (None, "message"):
                    continue
                content = item.get("content")
                if not isinstance(content, list):
                    continue
                for part in content:
                    if not isinstance(part, dict):
                        continue
                    if part.get("type") in ("output_text", "text") and isinstance(
                        part.get("text"), str
                    ):
                        text = part["text"].strip()
                        if text:
                            chunks.append(text)
            if chunks:
                return "\n".join(chunks)

        raise ModelUnavailable("OpenAI inference returned empty content")
