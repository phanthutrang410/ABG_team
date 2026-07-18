"""Minimal FPT AI chat-completions adapter (T02).

The adapter intentionally exposes one text-in/text-out operation.  It has no
case, scoring, transition or notification tools.  Tests inject a fake client;
the real HTTP path is only used when explicitly configured with an API key.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Protocol
from urllib import error, request


class ModelUnavailable(RuntimeError):
    """The inference service did not return a usable response."""


class TextModel(Protocol):
    def complete(self, *, system: str, user: str) -> str: ...


@dataclass(frozen=True)
class FPTChatClient:
    api_key: str
    base_url: str = "https://mkp-api.fptcloud.com"
    model: str = "Qwen/Qwen3-32B"
    timeout_seconds: float = 30.0

    def complete(self, *, system: str, user: str) -> str:
        if not self.api_key.strip():
            raise ModelUnavailable("FPT_API_KEY is not configured")
        body = json.dumps(
            {
                "model": self.model,
                "temperature": 0,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            }
        ).encode("utf-8")
        req = request.Request(
            f"{self.base_url.rstrip('/')}/v1/chat/completions",
            data=body,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=self.timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8"))
            content = payload["choices"][0]["message"]["content"]
        except (error.URLError, TimeoutError, ValueError, KeyError, IndexError) as exc:
            raise ModelUnavailable("FPT inference unavailable or malformed") from exc
        if not isinstance(content, str) or not content.strip():
            raise ModelUnavailable("FPT inference returned empty content")
        return content.strip()
