from __future__ import annotations

import pytest
from sqlalchemy import create_engine, text

from app.models.database import Base
from app.models.migrations import run_startup_migrations
from app.models.schema_version import (
    BASELINE_REVISION,
    DatabaseRevisionError,
    ensure_database_ready,
    get_current_database_revision,
)
import app.models  # noqa: F401


def test_get_current_database_revision_returns_none_without_version_table() -> None:
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    try:
        Base.metadata.create_all(bind=engine)
        run_startup_migrations(engine)

        assert get_current_database_revision(engine) is None
    finally:
        engine.dispose()


def test_get_current_database_revision_reads_alembic_version_table() -> None:
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    try:
        with engine.begin() as connection:
            connection.execute(
                text("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)")
            )
            connection.execute(
                text("INSERT INTO alembic_version (version_num) VALUES (:revision)"),
                {"revision": BASELINE_REVISION},
            )

        assert get_current_database_revision(engine) == BASELINE_REVISION
    finally:
        engine.dispose()


def test_ensure_database_ready_rejects_unversioned_database() -> None:
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    try:
        Base.metadata.create_all(bind=engine)
        run_startup_migrations(engine)

        with pytest.raises(DatabaseRevisionError):
            ensure_database_ready(engine)
    finally:
        engine.dispose()
