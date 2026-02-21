from datetime import UTC, datetime

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.api.v1.endpoints.auth import UserCredentials, login, me, register
from app.api.v1.endpoints.documents import get_document
from app.api.v1.endpoints.tasks import get_tasks
from app.models.ai_provider_setting import AIProviderSetting
from app.models.block import Block
from app.models.database import Base
from app.models.document import Document
from app.models.silent_analysis_job import SilentAnalysisJob
from app.models.task import TaskCache
from app.models.user import User


@pytest.fixture
def db_session() -> Session:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    testing_session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    session = testing_session_local()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def _credentials(username: str, password: str = "secret123") -> UserCredentials:
    return UserCredentials(username=username, password=password)


def _user_by_username(db: Session, username: str) -> User:
    user = db.query(User).filter(User.username == username).first()
    assert user is not None
    return user


def test_register_login_and_me_flow(db_session: Session) -> None:
    register_result = register(credentials=_credentials("alice"), db=db_session)
    assert register_result.token_type == "bearer"
    assert register_result.access_token != ""
    assert register_result.user.username == "alice"

    login_result = login(credentials=_credentials("alice"), db=db_session)
    assert login_result.token_type == "bearer"
    assert login_result.access_token != ""
    assert login_result.user.username == "alice"

    user = _user_by_username(db_session, "alice")
    me_result = me(current_user=user)
    assert me_result.username == "alice"


def test_first_registered_user_claims_orphan_records(db_session: Session) -> None:
    now = datetime.now(UTC).replace(tzinfo=None)
    document = Document(id="doc-1", user_id=None, content={"type": "doc", "content": []})
    db_session.add(document)
    db_session.flush()

    block = Block(
        id="block-1",
        user_id=None,
        document_id="doc-1",
        content="todo",
        position=0,
        is_task=True,
        is_completed=False,
        is_analyzed=True,
    )
    db_session.add(block)

    task = TaskCache(
        id="task-1",
        user_id=None,
        block_id="block-1",
        text="todo",
        status="pending",
        due_date=None,
        raw_time_expr=None,
        created_at=now,
        updated_at=now,
    )
    db_session.add(task)
    db_session.add(
        AIProviderSetting(
            user_id=None,
            provider="openai_compatible",
            api_base="http://localhost:11434/v1",
            api_key="dummy-key",
            model="llama3.2",
            timeout_seconds=20.0,
            max_attempts=2,
            disable_thinking=True,
        )
    )
    db_session.add(
        SilentAnalysisJob(
            user_id=None,
            document_id="doc-1",
            content_hash="h",
            status="pending",
            attempts=0,
            next_retry_at=None,
            last_error=None,
        )
    )
    db_session.commit()

    register(credentials=_credentials("first_user"), db=db_session)
    user = _user_by_username(db_session, "first_user")

    assert db_session.query(Document).filter(Document.id == "doc-1").first().user_id == str(user.id)
    assert db_session.query(Block).filter(Block.id == "block-1").first().user_id == str(user.id)
    assert db_session.query(TaskCache).filter(TaskCache.id == "task-1").first().user_id == str(user.id)
    assert db_session.query(AIProviderSetting).first().user_id == str(user.id)
    assert db_session.query(SilentAnalysisJob).first().user_id == str(user.id)


def test_document_and_task_queries_are_user_isolated(db_session: Session) -> None:
    register(credentials=_credentials("alice"), db=db_session)
    register(credentials=_credentials("bob"), db=db_session)

    alice = _user_by_username(db_session, "alice")
    bob = _user_by_username(db_session, "bob")

    db_session.add(
        Document(
            id="doc-alice",
            user_id=str(alice.id),
            content={"type": "doc", "content": [{"type": "paragraph"}]},
        )
    )
    db_session.add(
        Document(
            id="doc-bob",
            user_id=str(bob.id),
            content={"type": "doc", "content": [{"type": "paragraph"}]},
        )
    )
    db_session.flush()

    db_session.add(
        Block(
            id="block-alice",
            user_id=str(alice.id),
            document_id="doc-alice",
            content="todo alice",
            position=0,
            is_task=True,
            is_completed=False,
            is_analyzed=True,
        )
    )
    db_session.add(
        Block(
            id="block-bob",
            user_id=str(bob.id),
            document_id="doc-bob",
            content="todo bob",
            position=0,
            is_task=True,
            is_completed=False,
            is_analyzed=True,
        )
    )
    db_session.flush()

    now = datetime.now(UTC).replace(tzinfo=None)
    db_session.add(
        TaskCache(
            id="task-alice",
            user_id=str(alice.id),
            block_id="block-alice",
            text="alice task",
            status="pending",
            due_date=None,
            raw_time_expr=None,
            created_at=now,
            updated_at=now,
        )
    )
    db_session.add(
        TaskCache(
            id="task-bob",
            user_id=str(bob.id),
            block_id="block-bob",
            text="bob task",
            status="pending",
            due_date=None,
            raw_time_expr=None,
            created_at=now,
            updated_at=now,
        )
    )
    db_session.commit()

    alice_document = get_document(db=db_session, current_user=alice)  # type: ignore[arg-type]
    assert alice_document.id == "doc-alice"

    bob_document = get_document(db=db_session, current_user=bob)  # type: ignore[arg-type]
    assert bob_document.id == "doc-bob"

    alice_tasks = get_tasks(
        status=None,
        include_hidden=True,
        db=db_session,
        current_user=alice,  # type: ignore[arg-type]
    )
    assert [task.id for task in alice_tasks] == ["task-alice"]

    bob_tasks = get_tasks(
        status=None,
        include_hidden=True,
        db=db_session,
        current_user=bob,  # type: ignore[arg-type]
    )
    assert [task.id for task in bob_tasks] == ["task-bob"]


def test_login_rejects_wrong_password(db_session: Session) -> None:
    register(credentials=_credentials("alice"), db=db_session)

    with pytest.raises(HTTPException) as error_info:
        login(credentials=_credentials("alice", "wrongpass"), db=db_session)

    assert error_info.value.status_code == 401
