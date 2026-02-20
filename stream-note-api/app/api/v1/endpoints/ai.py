import uuid
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError

from app.models.ai_provider_setting import AIProviderSetting
from app.models.block import Block
from app.models.database import get_db
from app.models.document import Document
from app.models.task import TaskCache
from app.services.ai_service import (
    AIProviderConfig,
    AIService,
    AIServiceError,
    SUPPORTED_AI_PROVIDERS,
)
from app.services.time_parser import TimeParser

router = APIRouter()


class ExtractRequest(BaseModel):
    content: Dict[str, Any]


class TaskExtractResult(BaseModel):
    text: str
    due_date: Optional[str]
    time_expr: Optional[str]
    block_content: Optional[str] = None


class ExtractResponse(BaseModel):
    tasks_found: int
    tasks: List[TaskExtractResult]


class AnalyzePendingResponse(BaseModel):
    analyzed_count: int
    tasks_found: int
    tasks: List[TaskExtractResult]


class ResetDebugStateResponse(BaseModel):
    deleted_tasks: int
    reset_blocks: int


class AIProviderSettingsPayload(BaseModel):
    provider: str = Field(default="openai_compatible")
    api_base: str = Field(default="http://localhost:11434/v1")
    api_key: str = Field(default="dummy-key")
    model: str = Field(default="llama3.2")
    timeout_seconds: float = Field(default=20.0, ge=1.0, le=120.0)
    max_attempts: int = Field(default=2, ge=1, le=5)
    disable_thinking: bool = True

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, provider: str) -> str:
        normalized = provider.strip().lower()
        if normalized not in SUPPORTED_AI_PROVIDERS:
            allowed = ", ".join(sorted(SUPPORTED_AI_PROVIDERS))
            raise ValueError(
                f"Unsupported provider: {provider}. Allowed values: {allowed}"
            )
        return normalized

    @field_validator("api_base", "model")
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        cleaned = value.strip()
        if cleaned == "":
            raise ValueError("This field is required")
        return cleaned

    @field_validator("api_key")
    @classmethod
    def normalize_api_key(cls, value: str) -> str:
        return value.strip()


class AIProviderSettingsResponse(AIProviderSettingsPayload):
    supported_providers: List[str]
    updated_at: Optional[str]


class AIProviderTestResponse(BaseModel):
    ok: bool
    latency_ms: int
    message: str


def _is_sqlite_locked_error(error: OperationalError) -> bool:
    return "database is locked" in str(error).lower()


def extract_text_from_tiptap(doc: Dict[str, Any]) -> List[str]:
    """Extract text blocks from TipTap JSON"""
    blocks: List[str] = []

    def traverse(node: Any) -> None:
        if isinstance(node, dict):
            if node.get("type") == "paragraph":
                text = node.get("content", [])
                if isinstance(text, list):
                    text_content = "".join(
                        [c.get("text", "") for c in text if isinstance(c, dict)]
                    )
                    if text_content.strip():
                        blocks.append(text_content.strip())
                elif isinstance(text, str) and text.strip():
                    blocks.append(text.strip())
            if "content" in node:
                traverse(node["content"])
        elif isinstance(node, list):
            for item in node:
                traverse(item)

    if "content" in doc:
        traverse(doc["content"])

    return blocks


def _get_or_create_document(db: Session) -> Document:
    document = db.query(Document).first()
    if document is None:
        document = Document()
        db.add(document)
        db.flush()
    return document


def _get_or_create_block(
    db: Session, document_id: str, text: str, position: int
) -> Block:
    db_block = (
        db.query(Block)
        .filter(Block.document_id == document_id, Block.content == text)
        .first()
    )
    if db_block is None:
        db_block = Block(
            id=str(uuid.uuid4()),
            document_id=document_id,
            content=text,
            position=position,
            is_analyzed=False,
        )
        db.add(db_block)
        db.flush()
    return db_block


def _parse_due_date(
    time_expr: Optional[str], time_parser: TimeParser
) -> Optional[datetime]:
    if time_expr is None or time_expr == "":
        return None
    return time_parser.parse(time_expr)


def _build_task_result(
    task_text: str,
    due_date: Optional[datetime],
    time_expr: Optional[str],
    block_content: Optional[str] = None,
) -> TaskExtractResult:
    return TaskExtractResult(
        text=task_text,
        due_date=due_date.isoformat() if due_date is not None else None,
        time_expr=time_expr,
        block_content=block_content,
    )


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


def _payload_to_provider_config(payload: AIProviderSettingsPayload) -> AIProviderConfig:
    return AIProviderConfig(
        provider=payload.provider,
        api_base=payload.api_base,
        api_key=payload.api_key,
        model=payload.model,
        timeout_seconds=payload.timeout_seconds,
        max_attempts=payload.max_attempts,
        disable_thinking=payload.disable_thinking,
    )


def _load_provider_config(db: Session) -> AIProviderConfig:
    setting = db.query(AIProviderSetting).first()
    if setting is None:
        return AIProviderConfig.from_env()
    return _to_provider_config(setting)


def _build_provider_settings_response(
    config: AIProviderConfig, updated_at: Optional[datetime]
) -> AIProviderSettingsResponse:
    return AIProviderSettingsResponse(
        provider=config.provider,
        api_base=config.api_base,
        api_key=config.api_key,
        model=config.model,
        timeout_seconds=config.timeout_seconds,
        max_attempts=config.max_attempts,
        disable_thinking=config.disable_thinking,
        supported_providers=sorted(SUPPORTED_AI_PROVIDERS),
        updated_at=updated_at.isoformat() if updated_at is not None else None,
    )


@router.get("/provider-settings", response_model=AIProviderSettingsResponse)
def get_provider_settings(db: Session = Depends(get_db)) -> AIProviderSettingsResponse:
    setting = db.query(AIProviderSetting).first()
    if setting is None:
        config = AIProviderConfig.from_env()
        return _build_provider_settings_response(config=config, updated_at=None)

    config = _to_provider_config(setting)
    return _build_provider_settings_response(config=config, updated_at=setting.updated_at)


@router.put("/provider-settings", response_model=AIProviderSettingsResponse)
def update_provider_settings(
    payload: AIProviderSettingsPayload, db: Session = Depends(get_db)
) -> AIProviderSettingsResponse:
    setting = db.query(AIProviderSetting).first()
    if setting is None:
        setting = AIProviderSetting(id=1)
        db.add(setting)

    setting.provider = payload.provider
    setting.api_base = payload.api_base
    setting.api_key = payload.api_key
    setting.model = payload.model
    setting.timeout_seconds = payload.timeout_seconds
    setting.max_attempts = payload.max_attempts
    setting.disable_thinking = payload.disable_thinking

    db.commit()
    db.refresh(setting)

    config = _to_provider_config(setting)
    return _build_provider_settings_response(config=config, updated_at=setting.updated_at)


@router.post("/provider-settings/test", response_model=AIProviderTestResponse)
def test_provider_settings(payload: AIProviderSettingsPayload) -> AIProviderTestResponse:
    config = _payload_to_provider_config(payload)
    ai_service = AIService(config=config)

    try:
        test_result = ai_service.test_connection()
    except AIServiceError as error:
        raise HTTPException(
            status_code=502,
            detail=f"AI provider test failed: {error}",
        ) from error

    return AIProviderTestResponse(
        ok=True,
        latency_ms=int(test_result["latency_ms"]),
        message=str(test_result["message"]),
    )


@router.post("/extract", response_model=ExtractResponse)
def extract_tasks(request: ExtractRequest, db: Session = Depends(get_db)) -> ExtractResponse:
    """Extract tasks from document content using AI."""
    ai_service = AIService(config=_load_provider_config(db))
    time_parser = TimeParser()
    document = _get_or_create_document(db)
    blocks = extract_text_from_tiptap(request.content)

    all_tasks: List[TaskExtractResult] = []
    for index, text in enumerate(blocks):
        db_block = _get_or_create_block(
            db=db, document_id=str(document.id), text=text, position=index
        )
        try:
            extracted = ai_service.extract_tasks(text)
        except AIServiceError as error:
            db.rollback()
            raise HTTPException(
                status_code=502,
                detail=f"AI extraction failed for block {index + 1}: {error}",
            ) from error

        if extracted:
            db_block.is_task = True

        for task_data in extracted:
            task_text = str(task_data.get("text", "")).strip()
            if task_text == "":
                continue

            raw_time_expr = task_data.get("time_expr")
            time_expr = str(raw_time_expr).strip() if raw_time_expr else None
            due_date = _parse_due_date(time_expr=time_expr, time_parser=time_parser)

            db.add(
                TaskCache(
                    id=str(uuid.uuid4()),
                    block_id=str(db_block.id),
                    text=task_text,
                    status="pending",
                    due_date=due_date,
                    raw_time_expr=time_expr,
                )
            )
            all_tasks.append(
                _build_task_result(
                    task_text=task_text,
                    due_date=due_date,
                    time_expr=time_expr,
                )
            )

        db_block.is_analyzed = True

    db.commit()
    return ExtractResponse(tasks_found=len(all_tasks), tasks=all_tasks)


@router.post("/analyze-pending", response_model=AnalyzePendingResponse)
def analyze_pending_blocks(
    force: bool = Query(False),
    db: Session = Depends(get_db),
) -> AnalyzePendingResponse:
    ai_service = AIService(config=_load_provider_config(db))
    time_parser = TimeParser()

    doc = db.query(Document).first()
    if doc is None:
        raise HTTPException(status_code=404, detail="No document found")

    doc_content: Dict[str, Any] = (
        doc.content if doc.content else {"type": "doc", "content": []}
    )
    blocks = extract_text_from_tiptap(doc_content)

    analyzed_count = 0
    failed_count = 0
    first_error: Optional[str] = None
    all_tasks: List[TaskExtractResult] = []
    for index, text in enumerate(blocks[:10]):
        db_block = _get_or_create_block(
            db=db, document_id=str(doc.id), text=text, position=index
        )
        if db_block.is_analyzed and not force:
            continue

        if force:
            db.query(TaskCache).filter(TaskCache.block_id == str(db_block.id)).delete(
                synchronize_session=False
            )

        try:
            extracted = ai_service.extract_tasks(text)
        except AIServiceError as error:
            failed_count += 1
            if first_error is None:
                first_error = str(error)
            db_block.is_analyzed = False
            continue

        db_block.is_task = len(extracted) > 0

        for task_data in extracted:
            task_text = str(task_data.get("text", "")).strip()
            if task_text == "":
                continue

            raw_time_expr = task_data.get("time_expr")
            time_expr = str(raw_time_expr).strip() if raw_time_expr else None
            due_date = _parse_due_date(time_expr=time_expr, time_parser=time_parser)

            db.add(
                TaskCache(
                    id=str(uuid.uuid4()),
                    block_id=str(db_block.id),
                    text=task_text,
                    status="pending",
                    due_date=due_date,
                    raw_time_expr=time_expr,
                )
            )
            all_tasks.append(
                _build_task_result(
                    task_text=task_text,
                    due_date=due_date,
                    time_expr=time_expr,
                    block_content=(text[:50] + "...") if len(text) > 50 else text,
                )
            )

        db_block.is_analyzed = True
        analyzed_count += 1

    if failed_count > 0 and analyzed_count == 0 and len(all_tasks) == 0:
        db.rollback()
        raise HTTPException(
            status_code=502,
            detail=f"AI extraction failed for {failed_count} block(s): {first_error}",
        )

    db.commit()
    return AnalyzePendingResponse(
        analyzed_count=analyzed_count, tasks_found=len(all_tasks), tasks=all_tasks
    )


@router.post("/reset-debug-state", response_model=ResetDebugStateResponse)
def reset_debug_state(db: Session = Depends(get_db)) -> ResetDebugStateResponse:
    max_attempts = 3
    for attempt in range(1, max_attempts + 1):
        try:
            deleted_tasks = db.query(TaskCache).delete(synchronize_session=False)
            reset_blocks = db.query(Block).update(
                {
                    Block.is_analyzed: False,
                    Block.is_task: False,
                    Block.is_completed: False,
                },
                synchronize_session=False,
            )
            db.commit()
            return ResetDebugStateResponse(
                deleted_tasks=deleted_tasks,
                reset_blocks=reset_blocks,
            )
        except OperationalError as error:
            db.rollback()
            if _is_sqlite_locked_error(error) and attempt < max_attempts:
                time.sleep(0.2 * attempt)
                continue
            if _is_sqlite_locked_error(error):
                raise HTTPException(
                    status_code=503,
                    detail="Database is busy. Please retry in a moment.",
                ) from error
            raise
