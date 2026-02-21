import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.router import api_router
from app.core.env import load_env_file
from app.models.database import engine, Base
from app.models.migrations import run_startup_migrations
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
    Base.metadata.create_all(bind=engine)
    run_startup_migrations(engine)
    silent_analysis_worker.start()


@app.on_event("shutdown")
async def shutdown():
    silent_analysis_worker.stop()


@app.get("/api/v1/health")
async def health_check():
    return {"status": "ok"}
