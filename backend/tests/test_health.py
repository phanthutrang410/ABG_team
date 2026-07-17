from unittest.mock import patch

from app.main import _cors_allow_origins, health


def test_health() -> None:
    with patch("app.main.check_db", return_value=False):
        payload = health()
    assert payload["status"] == "ok"
    assert payload["service"] == "silent-shield"
    assert payload["database"] is False


def test_health_db_flag() -> None:
    with patch("app.main.check_db", return_value=True):
        assert health()["database"] is True


def test_cors_origins_default_localhost(monkeypatch) -> None:
    monkeypatch.delenv("CORS_ORIGINS", raising=False)
    assert _cors_allow_origins() == ["http://localhost:3000"]


def test_cors_origins_appends_live(monkeypatch) -> None:
    monkeypatch.setenv("CORS_ORIGINS", "http://52.74.255.88:3000")
    assert _cors_allow_origins() == [
        "http://localhost:3000",
        "http://52.74.255.88:3000",
    ]
