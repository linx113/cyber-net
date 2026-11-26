from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class RequestLog(Base):
    __tablename__ = "http_request_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    request_id: Mapped[str] = mapped_column(String(100), index=True)
    service: Mapped[str] = mapped_column(String(100), index=True)
    path: Mapped[str] = mapped_column(String(500))
    method: Mapped[str] = mapped_column(String(10))
    client_ip: Mapped[str] = mapped_column(String(100))
    status_code: Mapped[int] = mapped_column(Integer, index=True)
    processing_ms: Mapped[float] = mapped_column(Float)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True
    )


class MessageLog(Base):
    __tablename__ = "message_processing_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    service: Mapped[str] = mapped_column(String(100), index=True)
    queue: Mapped[str] = mapped_column(String(200), index=True)
    event_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    outcome: Mapped[str] = mapped_column(String(30))
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    processed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True
    )
