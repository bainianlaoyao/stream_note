import time
from datetime import UTC, datetime, timedelta
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session
from typing import Optional

from app.api.v1.deps import get_current_user
from app.models.block import Block
from app.models.database import get_db
from app.models.task import TaskCache
from app.models.user import User

router = APIRouter()
VALID_TASK_STATUSES = {"pending", "completed"}
HIDE_COMPLETED_AFTER_HOURS = 24


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


class DeleteTaskCommandResponse(BaseModel):
    deleted_task_id: str
    summary: TaskSummaryResponse


def _to_task_response(task: TaskCache) -> TaskResponse:
    due_date = (
        task.due_date.isoformat() if isinstance(task.due_date, datetime) else None
    )
    raw_time_expr = task.raw_time_expr if task.raw_time_expr is not None else None
    created_at = (
        task.created_at.isoformat()
        if isinstance(task.created_at, datetime)
        else str(task.created_at)
    )
    return TaskResponse(
        id=str(task.id),
        block_id=str(task.block_id),
        text=task.text,
        status=task.status,
        due_date=due_date,
        raw_time_expr=raw_time_expr,
        created_at=created_at,
    )


def _validate_status(status: str) -> str:
    if status not in VALID_TASK_STATUSES:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid task status: {status}. Allowed: pending, completed",
        )
    return status


def _sync_block_completion(db: Session, user_id: str, block_id: str) -> None:
    db.flush()

    block = (
        db.query(Block).filter(Block.id == block_id, Block.user_id == user_id).first()
    )
    if block is None:
        return

    task_rows = (
        db.query(TaskCache.status)
        .filter(TaskCache.block_id == block_id, TaskCache.user_id == user_id)
        .all()
    )
    task_statuses = [str(row[0]) for row in task_rows]

    has_tasks = len(task_statuses) > 0
    block.is_task = has_tasks
    block.is_completed = has_tasks and all(
        status == "completed" for status in task_statuses
    )


def _build_visibility_clause(include_hidden: bool):
    if include_hidden:
        return None

    completed_cutoff = datetime.now(UTC).replace(tzinfo=None) - timedelta(
        hours=HIDE_COMPLETED_AFTER_HOURS
    )
    return or_(
        TaskCache.status != "completed",
        TaskCache.updated_at > completed_cutoff,
    )


def _is_sqlite_locked_error(error: OperationalError) -> bool:
    return "database is locked" in str(error).lower()


def _query_tasks(
    db: Session,
    user_id: str,
    status: Optional[str],
    include_hidden: bool,
):
    query = db.query(TaskCache).filter(TaskCache.user_id == user_id)
    if status is not None:
        query = query.filter(TaskCache.status == status)

    visibility_clause = _build_visibility_clause(include_hidden=include_hidden)
    if visibility_clause is not None:
        query = query.filter(visibility_clause)
    return query


def _sync_block_after_task_delete(db: Session, user_id: str, block_id: str) -> None:
    _sync_block_completion(db, user_id, block_id)


def _get_summary(
    db: Session, user_id: str, include_hidden: bool = False
) -> TaskSummaryResponse:
    total_count = (
        _query_tasks(db=db, user_id=user_id, status=None, include_hidden=include_hidden)
        .with_entities(func.count(TaskCache.id))
        .scalar()
        or 0
    )
    pending_count = (
        _query_tasks(
            db=db, user_id=user_id, status="pending", include_hidden=include_hidden
        )
        .with_entities(func.count(TaskCache.id))
        .scalar()
        or 0
    )
    completed_count = (
        _query_tasks(
            db=db, user_id=user_id, status="completed", include_hidden=include_hidden
        )
        .with_entities(func.count(TaskCache.id))
        .scalar()
        or 0
    )
    return TaskSummaryResponse(
        pending_count=int(pending_count),
        completed_count=int(completed_count),
        total_count=int(total_count),
    )


@router.get("", response_model=list[TaskResponse])
def get_tasks(
    status: Optional[str] = Query(None),
    include_hidden: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = _query_tasks(
        db=db,
        user_id=str(current_user.id),
        status=status,
        include_hidden=include_hidden,
    )
    tasks = query.order_by(TaskCache.created_at.desc()).all()
    return [_to_task_response(task) for task in tasks]


@router.get("/summary", response_model=TaskSummaryResponse)
def get_tasks_summary(
    include_hidden: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskSummaryResponse:
    return _get_summary(
        db=db,
        user_id=str(current_user.id),
        include_hidden=include_hidden,
    )


@router.post("/{task_id}/commands/toggle", response_model=ToggleTaskCommandResponse)
def toggle_task_status(
    task_id: str,
    include_hidden: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ToggleTaskCommandResponse:
    task = (
        db.query(TaskCache)
        .filter(TaskCache.id == task_id, TaskCache.user_id == str(current_user.id))
        .first()
    )
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    task.status = "pending" if task.status == "completed" else "completed"
    _sync_block_completion(db, str(current_user.id), str(task.block_id))
    db.commit()
    db.refresh(task)

    return ToggleTaskCommandResponse(
        task=_to_task_response(task),
        summary=_get_summary(
            db=db,
            user_id=str(current_user.id),
            include_hidden=include_hidden,
        ),
    )


@router.patch("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: str,
    data: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = (
        db.query(TaskCache)
        .filter(TaskCache.id == task_id, TaskCache.user_id == str(current_user.id))
        .first()
    )
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    task.status = _validate_status(data.status)
    _sync_block_completion(db, str(current_user.id), str(task.block_id))
    db.commit()
    db.refresh(task)
    return _to_task_response(task)


@router.delete("/{task_id}", response_model=DeleteTaskCommandResponse)
def delete_task(
    task_id: str,
    include_hidden: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DeleteTaskCommandResponse:
    max_attempts = 3
    for attempt in range(1, max_attempts + 1):
        try:
            task = (
                db.query(TaskCache)
                .filter(
                    TaskCache.id == task_id, TaskCache.user_id == str(current_user.id)
                )
                .first()
            )
            if task is None:
                raise HTTPException(status_code=404, detail="Task not found")

            block_id = str(task.block_id)
            db.delete(task)
            db.flush()
            _sync_block_after_task_delete(
                db=db,
                user_id=str(current_user.id),
                block_id=block_id,
            )
            db.commit()

            return DeleteTaskCommandResponse(
                deleted_task_id=task_id,
                summary=_get_summary(
                    db=db,
                    user_id=str(current_user.id),
                    include_hidden=include_hidden,
                ),
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

    raise HTTPException(status_code=500, detail="Unexpected delete retry state")
