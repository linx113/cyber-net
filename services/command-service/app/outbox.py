import asyncio
import logging
from datetime import datetime, timezone

from app.database import SessionLocal
from app.messaging import publish_command
from app.models import CommandOutbox


logger = logging.getLogger(__name__)


async def dispatch_outbox():
    while True:
        db = SessionLocal()
        try:
            event = (
                db.query(CommandOutbox)
                .filter(CommandOutbox.published_at.is_(None))
                .order_by(CommandOutbox.created_at, CommandOutbox.id)
                .with_for_update(skip_locked=True)
                .first()
            )

            if event is None:
                db.rollback()
                await asyncio.sleep(0.5)
                continue

            await publish_command(event.payload)
            event.published_at = datetime.now(timezone.utc)
            db.commit()
        except asyncio.CancelledError:
            db.rollback()
            raise
        except Exception:
            db.rollback()
            logger.exception("Failed to publish command outbox event; retrying")
            await asyncio.sleep(2)
        finally:
            db.close()
