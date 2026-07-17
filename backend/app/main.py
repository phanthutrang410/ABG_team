"""Silent Shield API entrypoint."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.cases.router import router as cases_router
from app.database import check_db, init_schemas


@asynccontextmanager
async def lifespan(_app: FastAPI):
    try:
        init_schemas()
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
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cases_router)


@app.get("/health")
def health() -> dict[str, str | bool]:
    return {
        "status": "ok",
        "service": "silent-shield",
        "database": check_db(),
    }
