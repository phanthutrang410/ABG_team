"""Silent Shield API entrypoint."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.agent.router import router as agent_explanation_router
from app.agent.turns_router import router as agent_turns_router
from app.auth.router import router as auth_router
from app.cases.advisor_draft_router import router as advisor_handoff_draft_router
from app.cases.advisor_roster_router import router as advisor_roster_router
from app.cases.router import router as cases_router
from app.cases.review_router import router as review_cases_router
from app.config_api.router import router as config_router
from app.cases.store import try_enable_postgres_case_store
from app.database import check_db, init_schemas
from app.weekly.export_router import router as weekly_export_router
from app.weekly.router import router as weekly_router


def _cors_allow_origins() -> list[str]:
    """Local UI plus optional Live FE origins (comma-separated CORS_ORIGINS)."""
    origins = ["http://localhost:3000"]
    extra = os.environ.get("CORS_ORIGINS", "").strip()
    if extra:
        for origin in extra.split(","):
            origin = origin.strip()
            if origin and origin not in origins:
                origins.append(origin)
    return origins


@asynccontextmanager
async def lifespan(_app: FastAPI):
    try:
        init_schemas()
        try_enable_postgres_case_store()
    except Exception:
        pass
    yield


app = FastAPI(
    title="Silent Shield",
    description="Early-warning support system for schools (VAIC 2026)",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_allow_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(cases_router)
app.include_router(review_cases_router)
app.include_router(agent_explanation_router)
app.include_router(agent_turns_router)
app.include_router(advisor_handoff_draft_router)
app.include_router(advisor_roster_router)
app.include_router(config_router)
app.include_router(weekly_router)
app.include_router(weekly_export_router)


@app.get("/health")
def health() -> dict[str, str | bool]:
    return {
        "status": "ok",
        "service": "silent-shield",
        "database": check_db(),
    }
