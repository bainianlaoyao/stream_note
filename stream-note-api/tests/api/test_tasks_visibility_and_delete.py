from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.api.v1.endpoints.tasks import delete_task, get_tasks, get_tasks_summary
from app.models.block import Block
from app.models.database import Base
from app.models.document import Document
from app.models.task import TaskCache


class DummyUser:
    def __init__(self, user_id: str):
        self.id = user_id


@pytest.fixture
def db_session() -> Session:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def _create_document_and_block(
    db: Session,
    *,
    user_id: str,
    block_id: str,
    is_task: bool = True,
    is_completed: bool = False,
) -> Block:
    document = Document(id="doc-1", user_id=user_id)
    db.add(document)
    db.flush()

    block = Block(
        id=block_id,
        user_id=user_id,
        document_id=str(document.id),
        content="block-content",
        position=0,
        is_task=is_task,
        is_completed=is_completed,
    )
    db.add(block)
    db.flush()
    return block


def _create_task(
    db: Session,
    *,
    task_id: str,
    user_id: str,
    block_id: str,
    status: str,
    created_at: datetime,
    updated_at: datetime,
) -> None:
    db.add(
        TaskCache(
            id=task_id,
            user_id=user_id,
            block_id=block_id,
            text=f"task-{task_id}",
            status=status,
            due_date=None,
            raw_time_expr=None,
            created_at=created_at,
            updated_at=updated_at,
        )
    )


def test_get_tasks_hides_completed_tasks_after_24_hours_by_default(
    db_session: Session,
) -> None:
    current_user = DummyUser("user-1")
    now = datetime.now(UTC).replace(tzinfo=None)
    block = _create_document_and_block(db_session, user_id=str(current_user.id), block_id="block-1")

    _create_task(
        db_session,
        task_id="pending-1",
        user_id=str(current_user.id),
        block_id=str(block.id),
        status="pending",
        created_at=now - timedelta(hours=5),
        updated_at=now - timedelta(hours=5),
    )
    _create_task(
        db_session,
        task_id="completed-recent",
        user_id=str(current_user.id),
        block_id=str(block.id),
        status="completed",
        created_at=now - timedelta(hours=12),
        updated_at=now - timedelta(hours=12),
    )
    _create_task(
        db_session,
        task_id="completed-hidden",
        user_id=str(current_user.id),
        block_id=str(block.id),
        status="completed",
        created_at=now - timedelta(hours=30),
        updated_at=now - timedelta(hours=30),
    )
    db_session.commit()

    tasks = get_tasks(
        status=None,
        include_hidden=False,
        db=db_session,
        current_user=current_user,  # type: ignore[arg-type]
    )
    task_ids = {task.id for task in tasks}

    assert task_ids == {"pending-1", "completed-recent"}


def test_get_tasks_include_hidden_returns_hidden_tasks(db_session: Session) -> None:
    current_user = DummyUser("user-1")
    now = datetime.now(UTC).replace(tzinfo=None)
    block = _create_document_and_block(db_session, user_id=str(current_user.id), block_id="block-1")

    _create_task(
        db_session,
        task_id="completed-hidden",
        user_id=str(current_user.id),
        block_id=str(block.id),
        status="completed",
        created_at=now - timedelta(hours=48),
        updated_at=now - timedelta(hours=48),
    )
    db_session.commit()

    tasks = get_tasks(
        status=None,
        include_hidden=True,
        db=db_session,
        current_user=current_user,  # type: ignore[arg-type]
    )

    assert [task.id for task in tasks] == ["completed-hidden"]


def test_get_tasks_summary_respects_hidden_filter(db_session: Session) -> None:
    current_user = DummyUser("user-1")
    now = datetime.now(UTC).replace(tzinfo=None)
    block = _create_document_and_block(db_session, user_id=str(current_user.id), block_id="block-1")

    _create_task(
        db_session,
        task_id="pending-1",
        user_id=str(current_user.id),
        block_id=str(block.id),
        status="pending",
        created_at=now - timedelta(hours=2),
        updated_at=now - timedelta(hours=2),
    )
    _create_task(
        db_session,
        task_id="completed-hidden",
        user_id=str(current_user.id),
        block_id=str(block.id),
        status="completed",
        created_at=now - timedelta(hours=40),
        updated_at=now - timedelta(hours=40),
    )
    db_session.commit()

    default_summary = get_tasks_summary(
        include_hidden=False,
        db=db_session,
        current_user=current_user,  # type: ignore[arg-type]
    )
    full_summary = get_tasks_summary(
        include_hidden=True,
        db=db_session,
        current_user=current_user,  # type: ignore[arg-type]
    )

    assert default_summary.pending_count == 1
    assert default_summary.completed_count == 0
    assert default_summary.total_count == 1

    assert full_summary.pending_count == 1
    assert full_summary.completed_count == 1
    assert full_summary.total_count == 2


def test_delete_task_clears_block_flags_when_last_task_removed(db_session: Session) -> None:
    current_user = DummyUser("user-1")
    now = datetime.now(UTC).replace(tzinfo=None)
    block = _create_document_and_block(
        db_session,
        user_id=str(current_user.id),
        block_id="block-1",
        is_task=True,
        is_completed=True,
    )

    _create_task(
        db_session,
        task_id="completed-1",
        user_id=str(current_user.id),
        block_id=str(block.id),
        status="completed",
        created_at=now - timedelta(hours=1),
        updated_at=now - timedelta(hours=1),
    )
    db_session.commit()

    result = delete_task(
        task_id="completed-1",
        include_hidden=False,
        db=db_session,
        current_user=current_user,  # type: ignore[arg-type]
    )

    assert result.deleted_task_id == "completed-1"
    assert result.summary.total_count == 0

    deleted_task = db_session.query(TaskCache).filter(TaskCache.id == "completed-1").first()
    assert deleted_task is None

    reloaded_block = db_session.query(Block).filter(Block.id == str(block.id)).first()
    assert reloaded_block is not None
    assert reloaded_block.is_task is False
    assert reloaded_block.is_completed is False
