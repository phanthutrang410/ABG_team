"""H25 FPT transport hardening — mocked urllib only; no live calls."""

from __future__ import annotations

import json
from io import BytesIO
from typing import Any, Callable, Optional
from urllib import error

import pytest
from pydantic import ValidationError

from app.agent.fpt_client import (
    ALLOWED_FPT_HOSTS,
    MAX_RESPONSE_BYTES,
    MAX_TIMEOUT_SECONDS,
    MAX_TOKENS,
    FPTChatClient,
    ModelUnavailable,
)
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


def _client(**kwargs: Any) -> FPTChatClient:
    defaults = {
        "api_key": "test-secret-key-do-not-log",
        "base_url": "https://mkp-api.fptcloud.com",
        "timeout_seconds": 5.0,
        "max_tokens": 128,
        "max_concurrent": 2,
    }
    defaults.update(kwargs)
    return FPTChatClient(**defaults)


def test_host_allowlist_rejects_http_and_foreign_host() -> None:
    with pytest.raises(ModelUnavailable, match="HTTPS"):
        FPTChatClient(api_key="k", base_url="http://mkp-api.fptcloud.com")
    with pytest.raises(ModelUnavailable, match="allowlisted"):
        FPTChatClient(api_key="k", base_url="https://evil.example.com")
    assert "mkp-api.fptcloud.com" in ALLOWED_FPT_HOSTS


def test_settings_fpt_url_and_bounds() -> None:
    ok = Settings(
        fpt_base_url="https://mkp-api.fptcloud.com",
        agent_run_timeout_seconds=30,
        fpt_max_tokens=512,
    )
    assert ok.agent_run_timeout_seconds <= 30
    assert ok.fpt_max_tokens <= 512
    with pytest.raises(ValidationError):
        Settings(fpt_base_url="https://evil.example.com")
    # Legacy env values above the cap are clamped, not rejected.
    clamped = Settings(agent_run_timeout_seconds=120, fpt_max_tokens=2048)
    assert clamped.agent_run_timeout_seconds == 30
    assert clamped.fpt_max_tokens == 512


def test_api_key_not_in_repr() -> None:
    client = _client()
    text = repr(client)
    assert "test-secret-key-do-not-log" not in text
    assert "***" in text
    settings = Settings(fpt_api_key="super-secret-fpt")
    assert "super-secret-fpt" not in repr(settings)
    assert "super-secret-fpt" not in str(settings.fpt_api_key)


def test_request_uses_temperature_zero_and_max_tokens(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    def handler(req: Any, timeout: Optional[float] = None) -> _FakeHTTPResponse:
        captured["timeout"] = timeout
        captured["url"] = req.full_url
        captured["body"] = json.loads(req.data.decode("utf-8"))
        auth = req.get_header("Authorization")
        assert auth == "Bearer test-secret-key-do-not-log"
        payload = {
            "choices": [{"message": {"content": '{"ok":true}'}}],
        }
        return _FakeHTTPResponse(json.dumps(payload).encode("utf-8"))

    _patch_urlopen(monkeypatch, handler)
    out = _client(max_tokens=64).complete(system="sys", user="usr")
    assert out == '{"ok":true}'
    assert captured["timeout"] <= MAX_TIMEOUT_SECONDS
    assert captured["body"]["temperature"] == 0
    assert captured["body"]["max_tokens"] == 64
    assert captured["body"]["max_tokens"] <= MAX_TOKENS
    assert captured["url"].startswith("https://mkp-api.fptcloud.com/")


@pytest.mark.parametrize(
    "status",
    [401, 429, 500],
)
def test_http_errors_map_to_model_unavailable(
    monkeypatch: pytest.MonkeyPatch, status: int
) -> None:
    def handler(req: Any, timeout: Optional[float] = None) -> Any:
        raise error.HTTPError(
            url=req.full_url,
            code=status,
            msg="nope",
            hdrs=None,
            fp=BytesIO(b"error-body"),
        )

    _patch_urlopen(monkeypatch, handler)
    with pytest.raises(ModelUnavailable):
        _client().complete(system="s", user="u")


def test_timeout_maps_to_model_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    def handler(req: Any, timeout: Optional[float] = None) -> Any:
        raise TimeoutError("slow")

    _patch_urlopen(monkeypatch, handler)
    with pytest.raises(ModelUnavailable, match="timed out"):
        _client().complete(system="s", user="u")


def test_null_choices_maps_to_model_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def handler(req: Any, timeout: Optional[float] = None) -> _FakeHTTPResponse:
        return _FakeHTTPResponse(b'{"choices":null}')

    _patch_urlopen(monkeypatch, handler)
    with pytest.raises(ModelUnavailable, match="null"):
        _client().complete(system="s", user="u")


def test_malformed_json_maps_to_model_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def handler(req: Any, timeout: Optional[float] = None) -> _FakeHTTPResponse:
        return _FakeHTTPResponse(b"not-json{")

    _patch_urlopen(monkeypatch, handler)
    with pytest.raises(ModelUnavailable):
        _client().complete(system="s", user="u")


def test_oversize_response_maps_to_model_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    huge = b"x" * (MAX_RESPONSE_BYTES + 8)

    def handler(req: Any, timeout: Optional[float] = None) -> _FakeHTTPResponse:
        return _FakeHTTPResponse(huge)

    _patch_urlopen(monkeypatch, handler)
    with pytest.raises(ModelUnavailable, match="size limit"):
        _client(max_response_bytes=MAX_RESPONSE_BYTES).complete(system="s", user="u")


def test_missing_api_key_fails_closed() -> None:
    with pytest.raises(ModelUnavailable, match="not configured"):
        _client(api_key="  ").complete(system="s", user="u")


def test_from_settings_builds_hardened_client() -> None:
    settings = Settings(
        fpt_api_key="from-settings-key",
        fpt_base_url="https://mkp-api.fptcloud.com",
        fpt_model="Qwen/Qwen3-32B",
        agent_run_timeout_seconds=30,
        max_concurrent_agent_runs=3,
        fpt_max_tokens=256,
        fpt_max_response_bytes=8192,
    )
    client = FPTChatClient.from_settings(settings)
    assert client.timeout_seconds == 30
    assert client.max_tokens == 256
    assert client.max_concurrent == 3
    assert "from-settings-key" not in repr(client)


def test_construction_rejects_over_limit_timeout_and_tokens() -> None:
    with pytest.raises(ValueError):
        FPTChatClient(api_key="k", timeout_seconds=60)
    with pytest.raises(ValueError):
        FPTChatClient(api_key="k", max_tokens=2048)
