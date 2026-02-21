from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.router import api_router
from app.models.database import engine, Base
from app.models.migrations import run_startup_migrations
import app.models  # noqa: F401
from app.services.silent_analysis import silent_analysis_worker

app = FastAPI(title="Stream Note API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
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
