
import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class DeviceCommand(Base):
    __tablename__ = "device_commands"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    device_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    command: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    parameters: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="pending",
        nullable=False
    )

    result: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    __table_args__ = (
        Index("idx_device_commands_device_id", "device_id"),
        Index("idx_device_commands_status", "status"),
    )


class CommandOutbox(Base):
    __tablename__ = "command_outbox"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True
    )
