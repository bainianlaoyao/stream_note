from __future__ import annotations

from pathlib import Path
from typing import Optional

from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

BASELINE_REVISION = "20260221_000001"


class DatabaseRevisionError(RuntimeError):
    pass


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def get_alembic_config(database_url: Optional[str] = None) -> Config:
    root = _project_root()
    config = Config(str(root / "alembic.ini"))
    config.set_main_option("script_location", str(root / "alembic"))
    if database_url is not None and database_url != "":
        config.set_main_option("sqlalchemy.url", database_url)
    return config


def get_head_revision() -> str:
    script_directory = ScriptDirectory.from_config(get_alembic_config())
    head_revision = script_directory.get_current_head()
    if head_revision is None:
        raise RuntimeError("Alembic head revision is not configured.")
    return head_revision


def get_current_database_revision(engine: Engine) -> Optional[str]:
    inspector = inspect(engine)
    if "alembic_version" not in set(inspector.get_table_names()):
        return None

    with engine.connect() as connection:
        row = connection.execute(
            text("SELECT version_num FROM alembic_version LIMIT 1")
        ).fetchone()

    if row is None:
        return None
    return str(row[0])


def ensure_database_ready(engine: Engine) -> str:
    current_revision = get_current_database_revision(engine)
    head_revision = get_head_revision()

    if current_revision is None:
        raise DatabaseRevisionError(
            "Database revision is missing. Run "
            "`uv run --python .venv/Scripts/python.exe python scripts/migrate_db.py` "
            "before starting the API."
        )

    if current_revision != head_revision:
        raise DatabaseRevisionError(
            "Database revision mismatch: "
            f"current={current_revision}, expected={head_revision}. Run "
            "`uv run --python .venv/Scripts/python.exe python scripts/migrate_db.py` "
            "to migrate safely."
        )

    return head_revision
