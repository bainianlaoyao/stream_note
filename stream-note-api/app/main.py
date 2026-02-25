import os

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.api.v1.router import api_router
from app.core.env import load_env_file
from app.models.database import engine
from app.models.schema_version import (
    DatabaseRevisionError,
    ensure_database_ready,
    get_current_database_revision,
    get_head_revision,
)
import app.models  # noqa: F401
from app.services.silent_analysis import silent_analysis_worker

load_env_file()


def _resolve_cors_allow_origins() -> list[str]:
    raw_value = os.getenv("CORS_ALLOW_ORIGINS", "").strip()
    if raw_value == "":
        return [
            "http://localhost",
            "https://localhost",
            "http://127.0.0.1",
            "https://127.0.0.1",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "capacitor://localhost",
            "ionic://localhost",
        ]

    if raw_value == "*":
        return ["*"]

    return [origin.strip() for origin in raw_value.split(",") if origin.strip() != ""]


cors_allow_origins = _resolve_cors_allow_origins()
allow_all_origins = len(cors_allow_origins) == 1 and cors_allow_origins[0] == "*"

app = FastAPI(title="Stream Note API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_allow_origins,
    allow_credentials=not allow_all_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.on_event("startup")
async def startup():
    try:
        ensure_database_ready(engine)
    except DatabaseRevisionError as error:
        raise RuntimeError(str(error)) from error
    silent_analysis_worker.start()


@app.on_event("shutdown")
async def shutdown():
    silent_analysis_worker.stop()


@app.get("/api/v1/health")
async def health_check():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        current_revision = get_current_database_revision(engine)
        head_revision = get_head_revision()
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable",
        ) from error

    return {
        "status": "ok",
        "db_connection": "ok",
        "db_revision": current_revision,
        "db_head_revision": head_revision,
    }
