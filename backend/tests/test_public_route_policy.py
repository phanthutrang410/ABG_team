"""Cross-router regression checks for the public HTTP surface."""

from app.main import app


CRITICAL_ROUTE_METHODS = {
    "/health": {"get"},
    "/review-cases": {"get"},
    "/review-cases/{case_id}": {"get"},
    "/review-cases/{case_id}/explanation": {"post"},
    "/cases/{case_id}/transitions": {"post"},
    "/config/thresholds": {"get"},
    "/config/thresholds/impact": {"get"},
    "/fairness/report": {"get"},
    "/advisor-handoff-drafts": {"get"},
}


def _documented_methods(path_item: dict[str, object]) -> set[str]:
    return set(path_item) & {"get", "post", "put", "patch", "delete"}


def test_critical_public_routes_keep_their_documented_methods() -> None:
    paths = app.openapi()["paths"]

    for path, expected_methods in CRITICAL_ROUTE_METHODS.items():
        assert path in paths, f"Missing critical public route: {path}"
        assert _documented_methods(paths[path]) == expected_methods


def test_draft_and_explanation_surfaces_cannot_mutate_or_send() -> None:
    paths = app.openapi()["paths"]
    draft_methods = _documented_methods(paths["/advisor-handoff-drafts"])
    explanation_methods = _documented_methods(paths["/review-cases/{case_id}/explanation"])

    assert draft_methods == {"get"}
    assert explanation_methods == {"post"}
    assert not any("send" in path.lower() or "smtp" in path.lower() for path in paths)
