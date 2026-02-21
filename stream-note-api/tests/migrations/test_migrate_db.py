from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.models.block import Block
from app.models.database import Base
from app.models.document import Document
from app.models.migrations import run_startup_migrations
from app.models.schema_version import get_current_database_revision, get_head_revision
from app.models.task import TaskCache
from scripts.migrate_db import migrate_database
import app.models  # noqa: F401


def _build_sqlite_url(path: Path) -> str:
    return f"sqlite:///{path.as_posix()}"


def _create_legacy_database(database_url: str) -> None:
    engine = create_engine(database_url, connect_args={"check_same_thread": False})
    try:
        Base.metadata.create_all(bind=engine)
        run_startup_migrations(engine)

        with Session(engine) as session:
            document = Document(
                id="doc-legacy",
                user_id="user-1",
                content={"type": "doc", "content": []},
            )
            session.add(document)
            session.flush()

            block = Block(
                id="block-legacy",
                user_id="user-1",
                document_id="doc-legacy",
                content="legacy task",
                position=0,
                is_task=True,
                is_completed=False,
                is_analyzed=True,
            )
            session.add(block)
            session.flush()

            session.add(
                TaskCache(
                    id="task-legacy",
                    user_id="user-1",
                    block_id="block-legacy",
                    text="legacy task",
                    status="pending",
                    due_date=None,
                    raw_time_expr=None,
                )
            )
            session.commit()
    finally:
        engine.dispose()


def test_migrate_database_stamps_baseline_and_preserves_data(tmp_path: Path) -> None:
    database_path = tmp_path / "legacy.db"
    database_url = _build_sqlite_url(database_path)
    _create_legacy_database(database_url)

    backup_dir = tmp_path / "backups"
    result = migrate_database(database_url=database_url, backup_dir=backup_dir)

    assert result.backup_path is not None
    assert result.backup_path.exists()
    assert result.current_revision == get_head_revision()

    engine = create_engine(database_url, connect_args={"check_same_thread": False})
    try:
        assert get_current_database_revision(engine) == get_head_revision()

        with Session(engine) as session:
            assert session.query(Document).filter(Document.id == "doc-legacy").count() == 1
            assert session.query(Block).filter(Block.id == "block-legacy").count() == 1
            assert session.query(TaskCache).filter(TaskCache.id == "task-legacy").count() == 1
    finally:
        engine.dispose()
