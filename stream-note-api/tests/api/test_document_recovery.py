from datetime import UTC, datetime, timedelta

import pytest
from fastapi import Response
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.api.v1.endpoints.auth import UserCredentials, register
from app.api.v1.endpoints.documents import (
    DocumentRecoveryCandidatesResponse,
    DocumentUpdate,
    get_recovery_candidates,
    restore_recovery_revision,
    upsert_current_document,
)
from app.models.database import Base
from app.models.document import Document
from app.models.document_revision import DocumentRevision
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


def _register_user(db: Session, username: str) -> User:
    register(
        credentials=UserCredentials(username=username, password="secret123"),
        db=db,
    )
    user = db.query(User).filter(User.username == username).first()
    assert user is not None
    return user


def _content_with_text(text: str) -> dict:
    return {
        "type": "doc",
        "content": [
            {
                "type": "paragraph",
                "content": [{"type": "text", "text": text}],
            }
        ],
    }


def test_recovery_candidates_are_simple_and_limited(db_session: Session) -> None:
    user = _register_user(db_session, "alice")

    upsert_current_document(
        data=DocumentUpdate(content=_content_with_text("A" * 220)),
        response=Response(),
        db=db_session,
        current_user=user,  # type: ignore[arg-type]
    )
    upsert_current_document(
        data=DocumentUpdate(content=_content_with_text("B" * 420)),
        response=Response(),
        db=db_session,
        current_user=user,  # type: ignore[arg-type]
    )
    upsert_current_document(
        data=DocumentUpdate(content=_content_with_text("short")),
        response=Response(),
        db=db_session,
        current_user=user,  # type: ignore[arg-type]
    )

    oldest_revision = (
        db_session.query(DocumentRevision)
        .filter(DocumentRevision.user_id == str(user.id))
        .order_by(DocumentRevision.created_at.asc())
        .first()
    )
    assert oldest_revision is not None
    oldest_revision.created_at = datetime.now(UTC).replace(tzinfo=None) - timedelta(days=2)
    db_session.commit()

    result: DocumentRecoveryCandidatesResponse = get_recovery_candidates(
        db=db_session,
        current_user=user,  # type: ignore[arg-type]
    )
    assert 1 <= len(result.candidates) <= 3
    assert result.candidates[0].kind == "latest"
    assert any(candidate.kind == "stable" for candidate in result.candidates)
    assert any(candidate.kind == "yesterday" for candidate in result.candidates)


def test_restore_supports_immediate_undo(db_session: Session) -> None:
    user = _register_user(db_session, "bob")

    content_a = _content_with_text("alpha " * 80)
    content_b = _content_with_text("beta " * 120)

    upsert_current_document(
        data=DocumentUpdate(content=content_a),
        response=Response(),
        db=db_session,
        current_user=user,  # type: ignore[arg-type]
    )
    revision_a = (
        db_session.query(DocumentRevision)
        .filter(DocumentRevision.user_id == str(user.id))
        .order_by(DocumentRevision.revision_no.desc())
        .first()
    )
    assert revision_a is not None

    upsert_current_document(
        data=DocumentUpdate(content=content_b),
        response=Response(),
        db=db_session,
        current_user=user,  # type: ignore[arg-type]
    )
    revision_b = (
        db_session.query(DocumentRevision)
        .filter(DocumentRevision.user_id == str(user.id))
        .order_by(DocumentRevision.revision_no.desc())
        .first()
    )
    assert revision_b is not None
    assert str(revision_b.id) != str(revision_a.id)

    restore_result = restore_recovery_revision(
        revision_id=str(revision_a.id),
        response=Response(),
        db=db_session,
        current_user=user,  # type: ignore[arg-type]
    )
    assert restore_result.document.content == content_a
    assert restore_result.undo_revision_id is not None

    undo_result = restore_recovery_revision(
        revision_id=restore_result.undo_revision_id,
        response=Response(),
        db=db_session,
        current_user=user,  # type: ignore[arg-type]
    )
    assert undo_result.document.content == content_b

    saved_doc = db_session.query(Document).filter(Document.user_id == str(user.id)).first()
    assert saved_doc is not None
    assert saved_doc.content == content_b
