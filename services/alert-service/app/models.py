from datetime import datetime, timezone

from sqlalchemy import (
    Integer,
    String,
    Float,
    DateTime,
    Text,
    Index
)

from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Alert(Base):

    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    device_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True
    )

    device_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    value: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    severity: Mapped[str] = mapped_column(
        String(20),
        default="warning"
    )

    message: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    event_id: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="open",
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    __table_args__ = (
        Index("ix_alerts_device_created", "device_id", "created_at"),
        Index("uq_alerts_event_id", "event_id", unique=True),
    )
