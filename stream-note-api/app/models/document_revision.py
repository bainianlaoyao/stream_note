import uuid
from typing import Any, Dict, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.models.database import Base


class DocumentRevision(Base):
    __tablename__ = "document_revisions"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    document_id: Mapped[str] = mapped_column(
        String, ForeignKey("documents.id"), nullable=False, index=True
    )
    revision_no: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[Dict[str, Any]] = mapped_column(
        JSON, nullable=False, default=lambda: {"type": "doc", "content": []}
    )
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    char_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reason: Mapped[str] = mapped_column(String(32), nullable=False, default="auto_save")
    restored_from_revision_id: Mapped[Optional[str]] = mapped_column(
        String, ForeignKey("document_revisions.id"), nullable=True
    )
    created_at: Mapped[DateTime] = mapped_column(DateTime, default=func.now(), index=True)
