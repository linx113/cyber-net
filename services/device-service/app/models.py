from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Index,
    JSON
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import DateTime

from app.database import Base


class Telemetry(Base):
    __tablename__ = "telemetry"

    id = Column(Integer, primary_key=True, index=True)

    device_id = Column(String(100), nullable=False, index=True)
    device_type = Column(String(50), nullable=False)
    location = Column(String(100), nullable=False)

    value = Column(Float, nullable=False)
    unit = Column(String(20), nullable=False)

    status = Column(String(20), nullable=False)

    timestamp = Column(DateTime(timezone=True), nullable=False)

    received_at = Column(
        DateTime(timezone=True),
        nullable=False
    )

    __table_args__ = (
        Index("idx_telemetry_device_timestamp", "device_id", "timestamp"),
    )


class Device(Base):
    __tablename__ = "devices"

    device_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    device_type: Mapped[str] = mapped_column(String(50), nullable=False)
    location: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(20), nullable=False)
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class TelemetryOutbox(Base):
    __tablename__ = "telemetry_outbox"

    id = Column(Integer, primary_key=True, index=True)
    payload = Column(JSON, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
    published_at = Column(DateTime(timezone=True), nullable=True, index=True)
