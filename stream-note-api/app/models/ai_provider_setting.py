from sqlalchemy import Boolean, DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from typing import Optional

from app.models.database import Base


class AIProviderSetting(Base):
    __tablename__ = "ai_provider_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    provider: Mapped[str] = mapped_column(
        String(32), nullable=False, default="openai_compatible"
    )
    api_base: Mapped[str] = mapped_column(
        String(512), nullable=False, default="http://localhost:11434/v1"
    )
    api_key: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    model: Mapped[str] = mapped_column(String(128), nullable=False, default="llama3.2")
    timeout_seconds: Mapped[float] = mapped_column(Float, nullable=False, default=20.0)
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
    disable_thinking: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )
