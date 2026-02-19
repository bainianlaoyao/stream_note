from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import Optional

from app.models.block import Block
from app.models.database import get_db
from app.models.task import TaskCache

router = APIRouter()
VALID_TASK_STATUSES = {"pending", "completed"}


class TaskResponse(BaseModel):
    id: str
    block_id: str
    text: str
    status: str
    due_date: Optional[str]
    raw_time_expr: Optional[str]
    created_at: str


class TaskUpdate(BaseModel):
    status: str


class TaskSummaryResponse(BaseModel):
    pending_count: int
    completed_count: int
    total_count: int


class ToggleTaskCommandResponse(BaseModel):
    task: TaskResponse
    summary: TaskSummaryResponse


def _to_task_response(task: TaskCache) -> TaskResponse:
    due_date = task.due_date.isoformat() if task.due_date is not None else None
    raw_time_expr = task.raw_time_expr if task.raw_time_expr is not None else None
    return TaskResponse(
        id=str(task.id),
        block_id=str(task.block_id),
        text=task.text,
        status=task.status,
        due_date=due_date,
        raw_time_expr=raw_time_expr,
        created_at=task.created_at.isoformat(),
    )


def _validate_status(status: str) -> str:
    if status not in VALID_TASK_STATUSES:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid task status: {status}. Allowed: pending, completed",
        )
    return status


def _sync_block_completion(db: Session, block_id: str, task_status: str) -> None:
    block = db.query(Block).filter(Block.id == block_id).first()
    if block is None:
        return
    block.is_completed = task_status == "completed"


def _get_summary(db: Session) -> TaskSummaryResponse:
    total_count = db.query(func.count(TaskCache.id)).scalar() or 0
    pending_count = (
        db.query(func.count(TaskCache.id))
        .filter(TaskCache.status == "pending")
        .scalar()
        or 0
    )
    completed_count = (
        db.query(func.count(TaskCache.id))
        .filter(TaskCache.status == "completed")
        .scalar()
        or 0
    )
    return TaskSummaryResponse(
        pending_count=int(pending_count),
        completed_count=int(completed_count),
        total_count=int(total_count),
    )


@router.get("", response_model=list[TaskResponse])
def get_tasks(status: Optional[str] = Query(None), db: Session = Depends(get_db)):
    query = db.query(TaskCache)
    if status is not None:
        query = query.filter(TaskCache.status == status)
    tasks = query.order_by(TaskCache.created_at.desc()).all()
    return [_to_task_response(task) for task in tasks]


@router.get("/summary", response_model=TaskSummaryResponse)
def get_tasks_summary(db: Session = Depends(get_db)) -> TaskSummaryResponse:
    return _get_summary(db)


@router.post(
    "/{task_id}/commands/toggle", response_model=ToggleTaskCommandResponse
)
def toggle_task_status(
    task_id: str, db: Session = Depends(get_db)
) -> ToggleTaskCommandResponse:
    task = db.query(TaskCache).filter(TaskCache.id == task_id).first()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    task.status = "pending" if task.status == "completed" else "completed"
    _sync_block_completion(db, str(task.block_id), task.status)
    db.commit()
    db.refresh(task)

    return ToggleTaskCommandResponse(
        task=_to_task_response(task),
        summary=_get_summary(db),
    )


@router.patch("/{task_id}", response_model=TaskResponse)
def update_task(task_id: str, data: TaskUpdate, db: Session = Depends(get_db)):
    task = db.query(TaskCache).filter(TaskCache.id == task_id).first()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    task.status = _validate_status(data.status)
    _sync_block_completion(db, str(task.block_id), task.status)
    db.commit()
    db.refresh(task)
    return _to_task_response(task)
