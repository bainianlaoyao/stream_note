from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, declarative_base, sessionmaker
from typing import Generator
import os
from app.core.env import load_env_file

load_env_file()
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./stream_note.db")
IS_SQLITE = "sqlite" in DATABASE_URL
SQLITE_TIMEOUT_SECONDS = float(os.getenv("SQLITE_TIMEOUT_SECONDS", "30"))

connect_args = {}
if IS_SQLITE:
    connect_args = {
        "check_same_thread": False,
        "timeout": SQLITE_TIMEOUT_SECONDS,
    }

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
)

if IS_SQLITE:

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, _connection_record) -> None:
        cursor = dbapi_connection.cursor()
        busy_timeout_ms = int(SQLITE_TIMEOUT_SECONDS * 1000)
        cursor.execute(f"PRAGMA busy_timeout={busy_timeout_ms}")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
