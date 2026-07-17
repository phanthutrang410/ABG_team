"""Silent Shield API entrypoint."""

from fastapi import FastAPI

app = FastAPI(
    title="Silent Shield",
    description="Early-warning support system for schools (VAIC 2026)",
    version="0.1.0",
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "silent-shield"}
