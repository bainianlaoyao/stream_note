from __future__ import annotations

import hashlib
import json
import logging
import os
import threading
import time
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Dict, List, Optional, Sequence

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.ai_provider_setting import AIProviderSetting
from app.models.block import Block
from app.models.database import SessionLocal
from app.models.document import Document
from app.models.silent_analysis_job import SilentAnalysisJob
from app.models.task import TaskCache
from app.services.ai_service import AIProviderConfig, AIService, AIServiceError
from app.services.time_parser import TimeParser

logger = logging.getLogger(__name__)

JOB_STATUS_PENDING = "pending"
JOB_STATUS_RUNNING = "running"
JOB_STATUS_DONE = "done"
JOB_STATUS_FAILED = "failed"


def _is_truthy(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _utcnow_naive() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def _hash_document_content(content: Dict[str, Any]) -> str:
    canonical = json.dumps(content, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class SilentAnalysisSettings:
    enabled: bool
    idle_seconds: float
    poll_seconds: float
    batch_size: int
    max_retry_attempts: int
    retry_base_seconds: float

    @classmethod
    def from_env(cls) -> "SilentAnalysisSettings":
        enabled = _is_truthy(os.getenv("SILENT_ANALYSIS_ENABLED", "1"))

        def parse_float(key: str, default: float) -> float:
            raw = os.getenv(key)
            if raw is None:
                return default
            try:
                return float(raw)
            except ValueError:
                return default

        def parse_int(key: str, default: int) -> int:
            raw = os.getenv(key)
            if raw is None:
                return default
            try:
                return int(raw)
            except ValueError:
                return default

        idle_seconds = max(0.0, parse_float("SILENT_ANALYSIS_IDLE_SECONDS", 6.0))
        poll_seconds = max(0.1, parse_float("SILENT_ANALYSIS_POLL_SECONDS", 0.8))
        batch_size = max(1, parse_int("SILENT_ANALYSIS_BATCH_SIZE", 20))
        max_retry_attempts = max(1, parse_int("SILENT_ANALYSIS_MAX_RETRY", 3))
        retry_base_seconds = max(0.2, parse_float("SILENT_ANALYSIS_RETRY_BASE_SECONDS", 4.0))

        return cls(
            enabled=enabled,
            idle_seconds=idle_seconds,
            poll_seconds=poll_seconds,
            batch_size=batch_size,
            max_retry_attempts=max_retry_attempts,
            retry_base_seconds=retry_base_seconds,
        )


def _extract_text_from_tiptap(doc: Dict[str, Any]) -> List[str]:
    blocks: List[str] = []

    def traverse(node: Any) -> None:
        if isinstance(node, dict):
            if node.get("type") == "paragraph":
                node_content = node.get("content", [])
                if isinstance(node_content, list):
                    paragraph = "".join(
                        c.get("text", "") for c in node_content if isinstance(c, dict)
                    ).strip()
                    if paragraph:
                        blocks.append(paragraph)
                elif isinstance(node_content, str):
                    paragraph = node_content.strip()
                    if paragraph:
                        blocks.append(paragraph)
            if "content" in node:
                traverse(node["content"])
        elif isinstance(node, list):
            for item in node:
                traverse(item)

    if "content" in doc:
        traverse(doc["content"])
    return blocks


def _to_provider_config(setting: AIProviderSetting) -> AIProviderConfig:
    return AIProviderConfig(
        provider=setting.provider,
        api_base=setting.api_base,
        api_key=setting.api_key,
        model=setting.model,
        timeout_seconds=setting.timeout_seconds,
        max_attempts=setting.max_attempts,
        disable_thinking=setting.disable_thinking,
    )


def _load_provider_config(db: Session, user_id: Optional[str]) -> AIProviderConfig:
    query = db.query(AIProviderSetting)
    if user_id is None:
        setting = query.filter(AIProviderSetting.user_id.is_(None)).first()
    else:
        setting = query.filter(AIProviderSetting.user_id == user_id).first()
    if setting is None:
        return AIProviderConfig.from_env()
    return _to_provider_config(setting)


def _set_block_content(db_block: Block, text: str) -> None:
    if db_block.content == text:
        return

    db_block.content = text
    db_block.is_task = False
    db_block.is_completed = False
    db_block.is_analyzed = False


def _delete_tasks_for_blocks(
    db: Session,
    user_id: Optional[str],
    block_ids: Sequence[str],
) -> None:
    if len(block_ids) == 0:
        return

    query = db.query(TaskCache).filter(TaskCache.block_id.in_(block_ids))
    if user_id is None:
        query = query.filter(TaskCache.user_id.is_(None))
    else:
        query = query.filter(TaskCache.user_id == user_id)
    query.delete(synchronize_session=False)


def _analyze_document_once(
    db: Session,
    document: Document,
    user_id: Optional[str],
    batch_size: int,
) -> int:
    doc_content: Dict[str, Any] = (
        document.content if document.content else {"type": "doc", "content": []}
    )
    text_blocks = _extract_text_from_tiptap(doc_content)

    stale_blocks = (
        db.query(Block)
        .filter(
            Block.document_id == str(document.id),
            Block.position >= len(text_blocks),
            (
                Block.user_id.is_(None)
                if user_id is None
                else Block.user_id == user_id
            ),
        )
        .all()
    )
    stale_ids = [str(block.id) for block in stale_blocks]
    _delete_tasks_for_blocks(db, user_id, stale_ids)
    for stale_block in stale_blocks:
        db.delete(stale_block)

    ai_service = AIService(config=_load_provider_config(db, user_id))
    time_parser = TimeParser()
    analyzed_count = 0

    for position, text in enumerate(text_blocks):
        db_block = (
            db.query(Block)
            .filter(
                Block.document_id == str(document.id),
                Block.position == position,
                (
                    Block.user_id.is_(None)
                    if user_id is None
                    else Block.user_id == user_id
                ),
            )
            .first()
        )
        if db_block is None:
            db_block = Block(
                id=str(uuid.uuid4()),
                user_id=user_id,
                document_id=str(document.id),
                content=text,
                position=position,
                is_analyzed=False,
            )
            db.add(db_block)
            db.flush()
        else:
            _set_block_content(db_block, text)

        if db_block.is_analyzed:
            continue
        if analyzed_count >= batch_size:
            break

        extracted = ai_service.extract_tasks(text)
        task_query = db.query(TaskCache).filter(TaskCache.block_id == str(db_block.id))
        if user_id is None:
            task_query = task_query.filter(TaskCache.user_id.is_(None))
        else:
            task_query = task_query.filter(TaskCache.user_id == user_id)
        task_query.delete(synchronize_session=False)

        has_task = False
        for task_data in extracted:
            task_text = str(task_data.get("text", "")).strip()
            if task_text == "":
                continue

            raw_time_expr = task_data.get("time_expr")
            time_expr = str(raw_time_expr).strip() if raw_time_expr else None
            due_date = time_parser.parse(time_expr) if time_expr else None

            db.add(
                TaskCache(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    block_id=str(db_block.id),
                    text=task_text,
                    status="pending",
                    due_date=due_date,
                    raw_time_expr=time_expr,
                )
            )
            has_task = True

        db_block.is_task = has_task
        db_block.is_completed = False
        db_block.is_analyzed = True
        analyzed_count += 1

    return analyzed_count


def enqueue_silent_analysis(
    document_id: str,
    user_id: str,
    content: Dict[str, Any],
    *,
    settings: Optional[SilentAnalysisSettings] = None,
) -> None:
    resolved_settings = settings or SilentAnalysisSettings.from_env()
    if not resolved_settings.enabled:
        return

    now = _utcnow_naive()
    next_retry = now + timedelta(seconds=resolved_settings.idle_seconds)
    content_hash = _hash_document_content(content)

    db = SessionLocal()
    try:
        job = (
            db.query(SilentAnalysisJob)
            .filter(
                SilentAnalysisJob.document_id == document_id,
                SilentAnalysisJob.user_id == user_id,
            )
            .first()
        )

        if job is None:
            db.add(
                SilentAnalysisJob(
                    user_id=user_id,
                    document_id=document_id,
                    content_hash=content_hash,
                    status=JOB_STATUS_PENDING,
                    attempts=0,
                    next_retry_at=next_retry,
                    last_error=None,
                )
            )
        else:
            job.user_id = user_id
            job.content_hash = content_hash
            job.status = JOB_STATUS_PENDING
            job.next_retry_at = next_retry
            job.last_error = None
            job.attempts = 0

        db.commit()
    except Exception:
        db.rollback()
        logger.exception(
            "failed to enqueue silent analysis job for user_id=%s document_id=%s",
            user_id,
            document_id,
        )
    finally:
        db.close()


def process_one_silent_analysis_job(
    *,
    settings: Optional[SilentAnalysisSettings] = None,
) -> bool:
    resolved_settings = settings or SilentAnalysisSettings.from_env()
    if not resolved_settings.enabled:
        return False

    now = _utcnow_naive()
    db = SessionLocal()

    try:
        due_job = (
            db.query(SilentAnalysisJob)
            .filter(
                SilentAnalysisJob.status.in_([JOB_STATUS_PENDING, JOB_STATUS_FAILED]),
                or_(
                    SilentAnalysisJob.next_retry_at.is_(None),
                    SilentAnalysisJob.next_retry_at <= now,
                ),
            )
            .order_by(SilentAnalysisJob.updated_at.asc(), SilentAnalysisJob.id.asc())
            .first()
        )

        if due_job is None:
            return False

        job_id = due_job.id
        processing_hash = due_job.content_hash
        updated_rows = (
            db.query(SilentAnalysisJob)
            .filter(
                SilentAnalysisJob.id == job_id,
                SilentAnalysisJob.status.in_([JOB_STATUS_PENDING, JOB_STATUS_FAILED]),
            )
            .update(
                {
                    SilentAnalysisJob.status: JOB_STATUS_RUNNING,
                    SilentAnalysisJob.attempts: SilentAnalysisJob.attempts + 1,
                    SilentAnalysisJob.next_retry_at: None,
                    SilentAnalysisJob.last_error: None,
                },
                synchronize_session=False,
            )
        )
        if updated_rows == 0:
            db.rollback()
            return False

        db.commit()

        claimed = db.query(SilentAnalysisJob).filter(SilentAnalysisJob.id == job_id).first()
        if claimed is None:
            return False

        document_id = claimed.document_id
        user_id = claimed.user_id
        current_attempt = claimed.attempts
    except Exception:
        db.rollback()
        logger.exception("failed to claim silent analysis job")
        return False
    finally:
        db.close()

    analysis_error: Optional[str] = None
    has_remaining_unanalyzed = False

    work_db = SessionLocal()
    try:
        document = (
            work_db.query(Document)
            .filter(
                Document.id == document_id,
                (
                    Document.user_id.is_(None)
                    if user_id is None
                    else Document.user_id == user_id
                ),
            )
            .first()
        )
        if document is None:
            has_remaining_unanalyzed = False
        else:
            _analyze_document_once(
                db=work_db,
                document=document,
                user_id=user_id,
                batch_size=resolved_settings.batch_size,
            )
            work_db.flush()
            remaining = (
                work_db.query(Block)
                .filter(
                    Block.document_id == document_id,
                    Block.is_analyzed.is_(False),
                    (
                        Block.user_id.is_(None)
                        if user_id is None
                        else Block.user_id == user_id
                    ),
                )
                .count()
            )
            has_remaining_unanalyzed = remaining > 0

        work_db.commit()
    except AIServiceError as error:
        work_db.rollback()
        analysis_error = str(error)
    except Exception as error:
        work_db.rollback()
        analysis_error = str(error)
        logger.exception(
            "silent analysis worker crashed on user_id=%s document_id=%s",
            user_id,
            document_id,
        )
    finally:
        work_db.close()

    finalize_db = SessionLocal()
    try:
        job = finalize_db.query(SilentAnalysisJob).filter(SilentAnalysisJob.id == job_id).first()
        if job is None:
            return True

        if analysis_error is not None:
            has_newer_snapshot = job.content_hash != processing_hash
            if has_newer_snapshot:
                job.status = JOB_STATUS_PENDING
                job.next_retry_at = _utcnow_naive() + timedelta(
                    seconds=resolved_settings.idle_seconds
                )
                job.last_error = None
                finalize_db.commit()
                return True

            should_retry = current_attempt < resolved_settings.max_retry_attempts
            if should_retry:
                delay_seconds = resolved_settings.retry_base_seconds * (
                    2 ** max(0, current_attempt - 1)
                )
                job.status = JOB_STATUS_FAILED
                job.next_retry_at = _utcnow_naive() + timedelta(seconds=delay_seconds)
            else:
                job.status = JOB_STATUS_FAILED
                job.next_retry_at = None
            job.last_error = analysis_error
            finalize_db.commit()
            return True

        has_newer_snapshot = job.content_hash != processing_hash
        if has_newer_snapshot or has_remaining_unanalyzed:
            job.status = JOB_STATUS_PENDING
            if has_remaining_unanalyzed:
                job.next_retry_at = _utcnow_naive()
            else:
                job.next_retry_at = _utcnow_naive() + timedelta(
                    seconds=resolved_settings.idle_seconds
                )
            job.last_error = None
            finalize_db.commit()
            return True

        job.status = JOB_STATUS_DONE
        job.attempts = 0
        job.next_retry_at = None
        job.last_error = None
        finalize_db.commit()
        return True
    except Exception:
        finalize_db.rollback()
        logger.exception("failed to finalize silent analysis job id=%s", job_id)
        return True
    finally:
        finalize_db.close()


class SilentAnalysisWorker:
    def __init__(self) -> None:
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()

    def start(self) -> None:
        settings = SilentAnalysisSettings.from_env()
        if not settings.enabled:
            logger.info("silent analysis worker disabled by env")
            return

        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                return
            self._stop_event.clear()
            self._thread = threading.Thread(
                target=self._run_loop,
                name="silent-analysis-worker",
                daemon=True,
            )
            self._thread.start()
            logger.info("silent analysis worker started")

    def stop(self) -> None:
        thread: Optional[threading.Thread]
        with self._lock:
            thread = self._thread
            if thread is None:
                return
            self._stop_event.set()

        thread.join(timeout=2.0)

        with self._lock:
            self._thread = None
            self._stop_event.clear()
        logger.info("silent analysis worker stopped")

    def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            settings = SilentAnalysisSettings.from_env()
            did_work = process_one_silent_analysis_job(settings=settings)
            if did_work:
                continue
            self._stop_event.wait(settings.poll_seconds)


silent_analysis_worker = SilentAnalysisWorker()
