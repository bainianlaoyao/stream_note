from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.models.database import get_db
from app.models.task import TaskCache

router = APIRouter()


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


@router.get("", response_model=list[TaskResponse])
def get_tasks(status: Optional[str] = Query(None), db: Session = Depends(get_db)):
    query = db.query(TaskCache)
    if status is not None:
        query = query.filter(TaskCache.status == status)
    tasks = query.order_by(TaskCache.created_at.desc()).all()
    return [_to_task_response(task) for task in tasks]


@router.patch("/{task_id}", response_model=TaskResponse)
def update_task(task_id: str, data: TaskUpdate, db: Session = Depends(get_db)):
    task = db.query(TaskCache).filter(TaskCache.id == task_id).first()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    task.status = data.status
    db.commit()
    db.refresh(task)
    return _to_task_response(task)
