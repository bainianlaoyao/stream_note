import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.api.v1.endpoints.ai import _get_or_create_block
from app.models.block import Block
from app.models.database import Base
from app.models.document import Document


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


def test_get_or_create_block_matches_by_position_and_resets_on_content_change(
    db_session: Session,
) -> None:
    document = Document(
        id="doc-1", user_id="user-1", content={"type": "doc", "content": []}
    )
    db_session.add(document)
    db_session.flush()

    block_at_position_zero = _get_or_create_block(
        db=db_session,
        user_id="user-1",
        document_id="doc-1",
        text="alpha",
        position=0,
    )
    block_at_position_one = _get_or_create_block(
        db=db_session,
        user_id="user-1",
        document_id="doc-1",
        text="alpha",
        position=1,
    )

    assert str(block_at_position_zero.id) != str(block_at_position_one.id)

    block_at_position_zero.is_task = True
    block_at_position_zero.is_completed = True
    block_at_position_zero.is_analyzed = True
    db_session.flush()

    reloaded_position_zero = _get_or_create_block(
        db=db_session,
        user_id="user-1",
        document_id="doc-1",
        text="alpha-updated",
        position=0,
    )

    assert str(reloaded_position_zero.id) == str(block_at_position_zero.id)
    assert reloaded_position_zero.content == "alpha-updated"
    assert reloaded_position_zero.is_task is False
    assert reloaded_position_zero.is_completed is False
    assert reloaded_position_zero.is_analyzed is False

    all_blocks = db_session.query(Block).filter(Block.document_id == "doc-1").all()
    assert len(all_blocks) == 2
