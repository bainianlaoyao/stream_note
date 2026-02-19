import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.models.block import Block
from app.models.database import get_db
from app.models.document import Document
from app.models.task import TaskCache
from app.services.ai_service import AIService
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


@router.post("/extract", response_model=ExtractResponse)
def extract_tasks(request: ExtractRequest, db: Session = Depends(get_db)) -> ExtractResponse:
    """Extract tasks from document content using AI."""
    ai_service = AIService()
    time_parser = TimeParser()
    document = _get_or_create_document(db)
    blocks = extract_text_from_tiptap(request.content)

    all_tasks: List[TaskExtractResult] = []
    for index, text in enumerate(blocks):
        db_block = _get_or_create_block(
            db=db, document_id=str(document.id), text=text, position=index
        )
        extracted = ai_service.extract_tasks(text)
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
def analyze_pending_blocks(db: Session = Depends(get_db)) -> AnalyzePendingResponse:
    ai_service = AIService()
    time_parser = TimeParser()

    doc = db.query(Document).first()
    if doc is None:
        raise HTTPException(status_code=404, detail="No document found")

    doc_content: Dict[str, Any] = (
        doc.content if doc.content else {"type": "doc", "content": []}
    )
    blocks = extract_text_from_tiptap(doc_content)

    analyzed_count = 0
    all_tasks: List[TaskExtractResult] = []
    for index, text in enumerate(blocks[:10]):
        db_block = _get_or_create_block(
            db=db, document_id=str(doc.id), text=text, position=index
        )
        if db_block.is_analyzed:
            continue

        extracted = ai_service.extract_tasks(text)
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

    db.commit()
    return AnalyzePendingResponse(
        analyzed_count=analyzed_count, tasks_found=len(all_tasks), tasks=all_tasks
    )


@router.post("/reset-debug-state", response_model=ResetDebugStateResponse)
def reset_debug_state(db: Session = Depends(get_db)) -> ResetDebugStateResponse:
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
