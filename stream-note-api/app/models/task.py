from sqlalchemy import String, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional
from app.models.database import Base
import uuid


class TaskCache(Base):
    __tablename__ = "task_cache"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    block_id: Mapped[str] = mapped_column(String, ForeignKey("blocks.id"), nullable=False, index=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String, default="pending")
    due_date: Mapped[Optional[DateTime]] = mapped_column(DateTime, nullable=True)
    raw_time_expr: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())
