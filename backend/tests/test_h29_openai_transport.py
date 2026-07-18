"""H29 OpenAI Responses transport — mocked urllib only; no live calls."""

from __future__ import annotations

import json
from io import BytesIO
from typing import Any, Callable, Optional
from urllib import error

import pytest
from pydantic import ValidationError

from app.agent.openai_client import (
    ALLOWED_OPENAI_HOSTS,
    MAX_OUTPUT_TOKENS,
    MAX_RESPONSE_BYTES,
    MAX_TIMEOUT_SECONDS,
    OpenAIResponsesClient,
)
from app.agent.model import ModelUnavailable
from app.agent.runtime import get_text_model
from app.config import Settings


class _FakeHTTPResponse:
    def __init__(self, body: bytes, status: int = 200) -> None:
        self._body = body
        self.status = status

    def read(self, n: int = -1) -> bytes:
        if n < 0:
            data, self._body = self._body, b""
            return data
        data, self._body = self._body[:n], self._body[n:]
        return data

    def __enter__(self) -> "_FakeHTTPResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None


def _patch_urlopen(
    monkeypatch: pytest.MonkeyPatch,
    handler: Callable[..., Any],
) -> None:
    monkeypatch.setattr("urllib.request.urlopen", handler)


def _client(**kwargs: Any) -> OpenAIResponsesClient:
    defaults = {
        "api_key": "test-secret-key-do-not-log",
        "base_url": "https://api.openai.com",
        "timeout_seconds": 5.0,
        "max_output_tokens": 128,
        "max_concurrent": 2,
    }
    defaults.update(kwargs)
    return OpenAIResponsesClient(**defaults)


def _ok_payload(text: str = '{"ok":true}') -> bytes:
    payload = {
        "output": [
            {
                "type": "message",
                "content": [{"type": "output_text", "text": text}],
            }
        ]
    }
    return json.dumps(payload).encode("utf-8")


def test_host_allowlist_rejects_http_and_foreign_host() -> None:
    with pytest.raises(ModelUnavailable, match="HTTPS"):
        OpenAIResponsesClient(api_key="k", base_url="http://api.openai.com")
    with pytest.raises(ModelUnavailable, match="allowlisted"):
        OpenAIResponsesClient(api_key="k", base_url="https://evil.example.com")
    assert "api.openai.com" in ALLOWED_OPENAI_HOSTS


def test_settings_openai_url_and_bounds() -> None:
    ok = Settings(
        openai_base_url="https://api.openai.com",
        agent_run_timeout_seconds=30,
        openai_max_output_tokens=512,
    )
    assert ok.agent_run_timeout_seconds <= 30
    assert ok.openai_max_output_tokens <= 512
    with pytest.raises(ValidationError):
        Settings(openai_base_url="https://evil.example.com")
    clamped = Settings(openai_max_output_tokens=2048)
    assert clamped.openai_max_output_tokens == 512


def test_api_key_not_in_repr() -> None:
    client = _client()
    text = repr(client)
    assert "test-secret-key-do-not-log" not in text
    assert "***" in text
    settings = Settings(openai_api_key="super-secret-openai")
    assert "super-secret-openai" not in repr(settings)


def test_request_store_false_and_no_forbidden_fields(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    def handler(req: Any, timeout: Optional[float] = None) -> _FakeHTTPResponse:
        captured["timeout"] = timeout
        captured["url"] = req.full_url
        captured["body"] = json.loads(req.data.decode("utf-8"))
        auth = req.get_header("Authorization")
        assert auth == "Bearer test-secret-key-do-not-log"
        return _FakeHTTPResponse(_ok_payload())

    _patch_urlopen(monkeypatch, handler)
    out = _client(max_output_tokens=64).complete(system="sys", user="usr")
    assert out == '{"ok":true}'
    assert captured["timeout"] <= MAX_TIMEOUT_SECONDS
    assert captured["body"]["store"] is False
    assert captured["body"]["temperature"] == 0
    assert captured["body"]["max_output_tokens"] == 64
    assert captured["body"]["max_output_tokens"] <= MAX_OUTPUT_TOKENS
    assert "question" not in json.dumps(captured["body"])
    assert "student_ref" not in json.dumps(captured["body"])
    assert captured["url"].startswith("https://api.openai.com/v1/responses")


def test_missing_key_zero_network(monkeypatch: pytest.MonkeyPatch) -> None:
    called = {"n": 0}

    def handler(*args: Any, **kwargs: Any) -> _FakeHTTPResponse:
        called["n"] += 1
        return _FakeHTTPResponse(_ok_payload())

    _patch_urlopen(monkeypatch, handler)
    with pytest.raises(ModelUnavailable, match="not configured"):
        _client(api_key="").complete(system="s", user="u")
    assert called["n"] == 0

    settings = Settings(openai_api_key="")
    model = get_text_model(settings)
    with pytest.raises(ModelUnavailable, match="OPENAI_API_KEY"):
        model.complete(system="s", user="u")
    assert called["n"] == 0
    assert type(model).__name__ == "_MissingKeyModel"


def test_factory_uses_openai_not_fpt() -> None:
    settings = Settings(openai_api_key="k", fpt_api_key="fpt-should-not-win")
    model = get_text_model(settings)
    assert type(model).__name__ == "OpenAIResponsesClient"


def test_http_401_429_timeout_malformed(monkeypatch: pytest.MonkeyPatch) -> None:
    def http_err(code: int):
        def handler(*args: Any, **kwargs: Any) -> Any:
            raise error.HTTPError(
                "https://api.openai.com/v1/responses",
                code,
                "err",
                hdrs=None,  # type: ignore[arg-type]
                fp=BytesIO(b"{}"),
            )

        return handler

    _patch_urlopen(monkeypatch, http_err(401))
    with pytest.raises(ModelUnavailable, match="401"):
        _client().complete(system="s", user="u")

    _patch_urlopen(monkeypatch, http_err(429))
    with pytest.raises(ModelUnavailable, match="429"):
        _client().complete(system="s", user="u")

    def timeout_handler(*args: Any, **kwargs: Any) -> Any:
        raise TimeoutError("timed out")

    _patch_urlopen(monkeypatch, timeout_handler)
    with pytest.raises(ModelUnavailable, match="timed out"):
        _client().complete(system="s", user="u")

    def bad_json(*args: Any, **kwargs: Any) -> _FakeHTTPResponse:
        return _FakeHTTPResponse(b"not-json")

    _patch_urlopen(monkeypatch, bad_json)
    with pytest.raises(ModelUnavailable, match="not JSON"):
        _client().complete(system="s", user="u")


def test_oversize_response(monkeypatch: pytest.MonkeyPatch) -> None:
    def handler(*args: Any, **kwargs: Any) -> _FakeHTTPResponse:
        return _FakeHTTPResponse(b"x" * (MAX_RESPONSE_BYTES + 2))

    _patch_urlopen(monkeypatch, handler)
    with pytest.raises(ModelUnavailable, match="size limit"):
        _client(max_response_bytes=MAX_RESPONSE_BYTES).complete(system="s", user="u")


def test_from_settings_bounds() -> None:
    settings = Settings(
        openai_api_key="k",
        openai_model="gpt-4.1-mini",
        agent_run_timeout_seconds=30,
        openai_max_output_tokens=128,
    )
    client = OpenAIResponsesClient.from_settings(settings)
    assert client.model == "gpt-4.1-mini"
    assert client.max_output_tokens == 128

    with pytest.raises(ValueError):
        OpenAIResponsesClient(api_key="k", timeout_seconds=60)
    with pytest.raises(ValueError):
        OpenAIResponsesClient(api_key="k", max_output_tokens=2048)
