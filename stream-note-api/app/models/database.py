from sqlalchemy import create_engine, event
from sqlalchemy.engine.url import make_url
from sqlalchemy.orm import Session, declarative_base, sessionmaker
from typing import Generator
import os
from app.core.env import load_env_file

load_env_file()
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./stream_note.db")


def _is_sqlite_url(database_url: str) -> bool:
    return make_url(database_url).get_backend_name() == "sqlite"


IS_SQLITE = _is_sqlite_url(DATABASE_URL)
SQLITE_TIMEOUT_SECONDS = float(os.getenv("SQLITE_TIMEOUT_SECONDS", "30"))

connect_args = {}
if IS_SQLITE:
    connect_args = {
        "check_same_thread": False,
        "timeout": SQLITE_TIMEOUT_SECONDS,
    }

engine_options: dict[str, object] = {"connect_args": connect_args}
if not IS_SQLITE:
    engine_options["pool_pre_ping"] = True
    pool_recycle_seconds = int(os.getenv("DB_POOL_RECYCLE_SECONDS", "1800"))
    if pool_recycle_seconds > 0:
        engine_options["pool_recycle"] = pool_recycle_seconds

engine = create_engine(DATABASE_URL, **engine_options)

if IS_SQLITE:

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, _connection_record) -> None:
        cursor = dbapi_connection.cursor()
        busy_timeout_ms = int(SQLITE_TIMEOUT_SECONDS * 1000)
        cursor.execute(f"PRAGMA busy_timeout={busy_timeout_ms}")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
