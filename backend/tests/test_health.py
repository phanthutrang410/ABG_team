from app.main import health


def test_health() -> None:
    payload = health()
    assert payload["status"] == "ok"
    assert payload["service"] == "silent-shield"
