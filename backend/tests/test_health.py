from unittest.mock import patch

from app.main import health


def test_health() -> None:
    with patch("app.main.check_db", return_value=False):
        payload = health()
    assert payload["status"] == "ok"
    assert payload["service"] == "silent-shield"
    assert payload["database"] is False


def test_health_db_flag() -> None:
    with patch("app.main.check_db", return_value=True):
        assert health()["database"] is True
