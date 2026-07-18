"""Hardened FPT AI chat-completions adapter (H25).

Text-in/text-out only. No case, scoring, transition or notification tools.
Tests inject a fake client; live HTTP is never used in the mocked gate.
"""

from __future__ import annotations

import json
import threading
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Protocol
from urllib import error, request
from urllib.parse import urlparse

if TYPE_CHECKING:
    from app.config import Settings

ALLOWED_FPT_HOSTS = frozenset({"mkp-api.fptcloud.com"})
MAX_TIMEOUT_SECONDS = 30.0
MAX_TOKENS = 512
MAX_RESPONSE_BYTES = 16 * 1024
DEFAULT_MAX_CONCURRENT = 3


class ModelUnavailable(RuntimeError):
    """The inference service did not return a usable response."""


class TextModel(Protocol):
    def complete(self, *, system: str, user: str) -> str: ...


def _validate_https_allowlisted_base_url(base_url: str) -> str:
    parsed = urlparse(base_url)
    if parsed.scheme != "https":
        raise ModelUnavailable("FPT base URL must use HTTPS")
    host = (parsed.hostname or "").lower()
    if host not in ALLOWED_FPT_HOSTS:
        raise ModelUnavailable("FPT base URL host is not allowlisted")
    return base_url.rstrip("/")


@dataclass
class FPTChatClient:
    api_key: str
    base_url: str = "https://mkp-api.fptcloud.com"
    model: str = "Qwen/Qwen3-32B"
    timeout_seconds: float = 30.0
    max_tokens: int = 512
    max_concurrent: int = DEFAULT_MAX_CONCURRENT
    max_response_bytes: int = MAX_RESPONSE_BYTES
    _semaphore: threading.BoundedSemaphore = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        # Keep secrets out of default dataclass repr/str.
        object.__setattr__(self, "api_key", self.api_key)
        if self.timeout_seconds <= 0 or self.timeout_seconds > MAX_TIMEOUT_SECONDS:
            raise ValueError(
                f"timeout_seconds must be in (0, {MAX_TIMEOUT_SECONDS}]"
            )
        if self.max_tokens <= 0 or self.max_tokens > MAX_TOKENS:
            raise ValueError(f"max_tokens must be in (1, {MAX_TOKENS}]")
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
            f"FPTChatClient(base_url={self.base_url!r}, model={self.model!r}, "
            f"timeout_seconds={self.timeout_seconds}, max_tokens={self.max_tokens}, "
            f"api_key={'***' if self.api_key else ''!r})"
        )

    @classmethod
    def from_settings(cls, settings: "Settings") -> "FPTChatClient":
        key = settings.fpt_api_key
        if hasattr(key, "get_secret_value"):
            key = key.get_secret_value()
        timeout = min(float(settings.agent_run_timeout_seconds), MAX_TIMEOUT_SECONDS)
        return cls(
            api_key=str(key or ""),
            base_url=settings.fpt_base_url,
            model=settings.fpt_model,
            timeout_seconds=timeout,
            max_tokens=min(int(settings.fpt_max_tokens), MAX_TOKENS),
            max_concurrent=int(settings.max_concurrent_agent_runs),
            max_response_bytes=min(
                int(settings.fpt_max_response_bytes), MAX_RESPONSE_BYTES
            ),
        )

    def complete(self, *, system: str, user: str) -> str:
        if not self.api_key.strip():
            raise ModelUnavailable("FPT_API_KEY is not configured")

        body_obj = {
            "model": self.model,
            "temperature": 0,
            "max_tokens": self.max_tokens,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        body = json.dumps(body_obj).encode("utf-8")
        if len(body) > MAX_RESPONSE_BYTES:
            raise ModelUnavailable("FPT request body exceeds size limit")

        req = request.Request(
            f"{self.base_url}/v1/chat/completions",
            data=body,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        acquired = self._semaphore.acquire(blocking=True, timeout=self.timeout_seconds)
        if not acquired:
            raise ModelUnavailable("FPT concurrency limit reached")
        try:
            return self._do_request(req)
        finally:
            self._semaphore.release()

    def _do_request(self, req: request.Request) -> str:
        try:
            with request.urlopen(req, timeout=self.timeout_seconds) as response:
                raw = response.read(self.max_response_bytes + 1)
        except error.HTTPError as exc:
            # Drain/limit error body so oversized error pages cannot blow memory.
            try:
                exc.read(self.max_response_bytes + 1)
            except Exception:  # noqa: BLE001
                pass
            if exc.code in (401, 429):
                raise ModelUnavailable(
                    f"FPT inference rejected with HTTP {exc.code}"
                ) from exc
            raise ModelUnavailable(
                f"FPT inference unavailable (HTTP {exc.code})"
            ) from exc
        except TimeoutError as exc:
            raise ModelUnavailable("FPT inference timed out") from exc
        except error.URLError as exc:
            reason = getattr(exc, "reason", None)
            if isinstance(reason, TimeoutError) or "timed out" in str(exc).lower():
                raise ModelUnavailable("FPT inference timed out") from exc
            raise ModelUnavailable("FPT inference unavailable or malformed") from exc
        except (ValueError, UnicodeError) as exc:
            raise ModelUnavailable("FPT inference unavailable or malformed") from exc

        if len(raw) > self.max_response_bytes:
            raise ModelUnavailable("FPT response exceeds size limit")

        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ModelUnavailable("FPT response is not valid UTF-8") from exc

        try:
            payload = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ModelUnavailable("FPT response is not JSON") from exc

        return self._extract_content(payload)

    @staticmethod
    def _extract_content(payload: object) -> str:
        if not isinstance(payload, dict):
            raise ModelUnavailable("FPT response shape is invalid")
        choices = payload.get("choices")
        if choices is None:
            raise ModelUnavailable("FPT response choices is null")
        if not isinstance(choices, list) or not choices:
            raise ModelUnavailable("FPT response choices is empty or invalid")
        first = choices[0]
        if not isinstance(first, dict):
            raise ModelUnavailable("FPT response choice shape is invalid")
        message = first.get("message")
        if not isinstance(message, dict):
            raise ModelUnavailable("FPT response message is missing")
        content = message.get("content")
        if not isinstance(content, str) or not content.strip():
            raise ModelUnavailable("FPT inference returned empty content")
        return content.strip()
