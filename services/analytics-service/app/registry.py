import asyncio
import logging
import os
from datetime import datetime, timedelta, timezone

from sqlalchemy import DateTime, Float, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from app.messaging import publish_alert


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://cybernet:cybernet_dev@postgres-main:5432/cybernet"
)
INACTIVE_AFTER_SECONDS = int(os.getenv("INACTIVE_AFTER_SECONDS", "300"))
INACTIVITY_CHECK_INTERVAL_SECONDS = int(
    os.getenv("INACTIVITY_CHECK_INTERVAL_SECONDS", "30")
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


class Device(Base):
    __tablename__ = "devices"

    device_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    device_type: Mapped[str] = mapped_column(String(50), nullable=False)
    location: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(20), nullable=False)
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


async def monitor_inactive_devices():
    while True:
        db = SessionLocal()
        try:
            cutoff = datetime.now(timezone.utc) - timedelta(
                seconds=INACTIVE_AFTER_SECONDS
            )
            inactive = (
                db.query(Device)
                .filter(Device.status != "inactive", Device.last_seen < cutoff)
                .with_for_update(skip_locked=True)
                .all()
            )

            for device in inactive:
                await publish_alert({
                    "event_id": f"offline:{device.device_id}:{device.last_seen.isoformat()}",
                    "device_id": device.device_id,
                    "device_type": device.device_type,
                    "value": device.value,
                    "severity": "warning",
                    "message": (
                        f"Device has not reported for "
                        f"{INACTIVE_AFTER_SECONDS} seconds"
                    )
                })
                device.status = "inactive"
                logger.warning("Device %s marked inactive", device.device_id)

            db.commit()
        except asyncio.CancelledError:
            db.rollback()
            raise
        except Exception:
            db.rollback()
            logger.exception("Inactive-device scan failed; will retry")
        finally:
            db.close()

        await asyncio.sleep(INACTIVITY_CHECK_INTERVAL_SECONDS)
