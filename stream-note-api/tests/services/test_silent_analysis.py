from datetime import UTC, datetime, timedelta
from typing import Any, Dict

import pytest
from fastapi import Response
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.api.v1.endpoints.documents import DocumentUpdate, upsert_current_document
from app.models.block import Block
from app.models.database import Base
from app.models.document import Document
from app.models.silent_analysis_job import SilentAnalysisJob
from app.models.task import TaskCache
from app.services.ai_service import AIServiceError
from app.services.silent_analysis import (
    SilentAnalysisSettings,
    _hash_document_content,
    enqueue_silent_analysis,
    process_one_silent_analysis_job,
)


class DummyUser:
    def __init__(self, user_id: str):
        self.id = user_id


@pytest.fixture
def testing_session_factory(monkeypatch: pytest.MonkeyPatch):
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    monkeypatch.setattr("app.services.silent_analysis.SessionLocal", TestingSessionLocal)
    monkeypatch.setenv("SILENT_ANALYSIS_ENABLED", "1")
    monkeypatch.setenv("SILENT_ANALYSIS_IDLE_SECONDS", "0")
    monkeypatch.setenv("SILENT_ANALYSIS_POLL_SECONDS", "0.1")
    monkeypatch.setenv("SILENT_ANALYSIS_BATCH_SIZE", "20")
    monkeypatch.setenv("SILENT_ANALYSIS_MAX_RETRY", "3")
    monkeypatch.setenv("SILENT_ANALYSIS_RETRY_BASE_SECONDS", "1")

    try:
        yield TestingSessionLocal
    finally:
        Base.metadata.drop_all(bind=engine)


def _make_doc_content(*paragraphs: str) -> Dict[str, Any]:
    return {
        "type": "doc",
        "content": [
            {
                "type": "paragraph",
                "content": [{"type": "text", "text": text}],
            }
            for text in paragraphs
        ],
    }


def test_upsert_document_enqueues_silent_analysis_job(
    testing_session_factory,
) -> None:
    db: Session = testing_session_factory()
    try:
        current_user = DummyUser("user-1")
        content = _make_doc_content("todo read docs")
        response = Response()

        upsert_current_document(
            data=DocumentUpdate(content=content),
            response=response,
            db=db,
            current_user=current_user,  # type: ignore[arg-type]
        )

        job = db.query(SilentAnalysisJob).first()
        assert job is not None
        assert job.status == "pending"
        assert job.user_id == "user-1"
        assert job.document_id != ""
        assert job.content_hash == _hash_document_content(content)
    finally:
        db.close()


def test_enqueue_silent_analysis_coalesces_latest_snapshot(
    testing_session_factory,
) -> None:
    settings = SilentAnalysisSettings(
        enabled=True,
        idle_seconds=3,
        poll_seconds=0.1,
        batch_size=20,
        max_retry_attempts=3,
        retry_base_seconds=1,
    )

    setup_db: Session = testing_session_factory()
    try:
        document = Document(
            id="doc-coalesce",
            user_id="user-1",
            content=_make_doc_content("alpha"),
        )
        setup_db.add(document)
        setup_db.commit()
    finally:
        setup_db.close()

    first_content = _make_doc_content("alpha")
    second_content = _make_doc_content("beta")

    enqueue_silent_analysis("doc-coalesce", "user-1", first_content, settings=settings)
    enqueue_silent_analysis("doc-coalesce", "user-1", second_content, settings=settings)

    verify_db: Session = testing_session_factory()
    try:
        jobs = verify_db.query(SilentAnalysisJob).all()
        assert len(jobs) == 1
        job = jobs[0]
        assert job.user_id == "user-1"
        assert job.document_id == "doc-coalesce"
        assert job.status == "pending"
        assert job.content_hash == _hash_document_content(second_content)
    finally:
        verify_db.close()


def test_process_one_silent_analysis_job_batches_until_done(
    testing_session_factory,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeAIService:
        def __init__(self, config: Any = None):
            del config

        def extract_tasks(self, text: str):
            return [{"text": f"task:{text}", "time_expr": None}]

    monkeypatch.setattr("app.services.silent_analysis.AIService", FakeAIService)

    settings = SilentAnalysisSettings(
        enabled=True,
        idle_seconds=0,
        poll_seconds=0.1,
        batch_size=1,
        max_retry_attempts=3,
        retry_base_seconds=1,
    )

    setup_db: Session = testing_session_factory()
    try:
        content = _make_doc_content("todo A", "todo B")
        setup_db.add(Document(id="doc-batch", user_id="user-1", content=content))
        setup_db.commit()
        enqueue_silent_analysis("doc-batch", "user-1", content, settings=settings)
    finally:
        setup_db.close()

    assert process_one_silent_analysis_job(settings=settings) is True

    mid_db: Session = testing_session_factory()
    try:
        job = (
            mid_db.query(SilentAnalysisJob)
            .filter(SilentAnalysisJob.document_id == "doc-batch")
            .first()
        )
        assert job is not None
        assert job.status == "pending"

        task_count = mid_db.query(TaskCache).count()
        assert task_count == 1
    finally:
        mid_db.close()

    assert process_one_silent_analysis_job(settings=settings) is True

    verify_db: Session = testing_session_factory()
    try:
        job = (
            verify_db.query(SilentAnalysisJob)
            .filter(SilentAnalysisJob.document_id == "doc-batch")
            .first()
        )
        assert job is not None
        assert job.status == "done"
        assert job.attempts == 0

        task_count = verify_db.query(TaskCache).count()
        assert task_count == 2

        unanalyzed_count = (
            verify_db.query(Block)
            .filter(
                Block.document_id == "doc-batch",
                Block.is_analyzed.is_(False),
            )
            .count()
        )
        assert unanalyzed_count == 0
    finally:
        verify_db.close()


def test_process_one_silent_analysis_job_sets_retry_on_ai_error(
    testing_session_factory,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FailingAIService:
        def __init__(self, config: Any = None):
            del config

        def extract_tasks(self, text: str):
            del text
            raise AIServiceError("provider unavailable")

    monkeypatch.setattr("app.services.silent_analysis.AIService", FailingAIService)

    settings = SilentAnalysisSettings(
        enabled=True,
        idle_seconds=0,
        poll_seconds=0.1,
        batch_size=20,
        max_retry_attempts=3,
        retry_base_seconds=2,
    )

    setup_db: Session = testing_session_factory()
    try:
        content = _make_doc_content("todo unstable")
        setup_db.add(Document(id="doc-error", user_id="user-1", content=content))
        setup_db.commit()
        enqueue_silent_analysis("doc-error", "user-1", content, settings=settings)
    finally:
        setup_db.close()

    assert process_one_silent_analysis_job(settings=settings) is True

    verify_db: Session = testing_session_factory()
    try:
        job = (
            verify_db.query(SilentAnalysisJob)
            .filter(SilentAnalysisJob.document_id == "doc-error")
            .first()
        )
        assert job is not None
        assert job.status == "failed"
        assert job.attempts == 1
        assert job.last_error is not None
        assert "provider unavailable" in job.last_error
        assert job.next_retry_at is not None
        assert job.next_retry_at > datetime.now(UTC).replace(tzinfo=None) - timedelta(
            seconds=1
        )
    finally:
        verify_db.close()
