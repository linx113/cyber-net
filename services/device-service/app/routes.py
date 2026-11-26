
import os
import socket
import logging
import json
from datetime import timedelta

from datetime import datetime, timezone

from app.cache import cache
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.dialects.postgresql import insert
from redis.exceptions import RedisError
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.schemas import (
    DeviceRecord,
    DevicesResponse,
    TelemetryInput,
    TelemetryResponse,
    TelemetryRecord
)
from app.database import get_db
from app.models import Device, Telemetry, TelemetryOutbox


router = APIRouter()
logger = logging.getLogger(__name__)

INSTANCE_ID = os.getenv(
    "INSTANCE_ID",
    socket.gethostname()
)
INACTIVE_AFTER_SECONDS = int(os.getenv("INACTIVE_AFTER_SECONDS", "300"))


@router.post(
    "/telemetry",
    response_model=TelemetryResponse
)
async def receive_telemetry(
    telemetry: TelemetryInput,
    db: Session = Depends(get_db)
):

    record = Telemetry(
        device_id=telemetry.device_id,
        device_type=telemetry.type,
        location=telemetry.location,
        value=telemetry.value,
        unit=telemetry.unit,
        status=telemetry.status,
        timestamp=telemetry.timestamp,
        received_at=datetime.now(timezone.utc)
    )
    try:
        db.add(record)
        db.flush()
        db.execute(
            insert(Device)
            .values(
                device_id=telemetry.device_id,
                device_type=telemetry.type,
                location=telemetry.location,
                status=telemetry.status,
                value=telemetry.value,
                unit=telemetry.unit,
                last_seen=record.received_at
            )
            .on_conflict_do_update(
                index_elements=[Device.device_id],
                set_={
                    "device_type": telemetry.type,
                    "location": telemetry.location,
                    "status": telemetry.status,
                    "value": telemetry.value,
                    "unit": telemetry.unit,
                    "last_seen": record.received_at
                }
            )
        )
        outbox_event = TelemetryOutbox(
            payload={
                **telemetry.model_dump(mode="json"),
                "event_id": f"telemetry:{record.id}"
            }
        )
        db.add(outbox_event)
        db.commit()

    except SQLAlchemyError:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Failed to save telemetry"
        )

    try:
        cache.delete("telemetry:count", "devices:list")
    except RedisError:
        logger.warning("Redis unavailable while invalidating telemetry count")

    return TelemetryResponse(
        message="Telemetry saved and queued for processing",
        device_id=telemetry.device_id,
        processed_by=INSTANCE_ID
    )


@router.get("/health")
def health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))

    return {
        "status": "healthy",
        "instance": INSTANCE_ID
    }


@router.get("/telemetry/count")
def telemetry_count(db: Session = Depends(get_db)):
    try:
        cached_count = cache.get("telemetry:count")
        if cached_count is not None:
            return {"total_records": int(cached_count)}
    except (RedisError, ValueError):
        logger.warning("Could not read telemetry count from Redis")

    total_records = db.query(Telemetry).count()

    try:
        cache.setex("telemetry:count", 30, total_records)
    except RedisError:
        logger.warning("Could not cache telemetry count in Redis")

    return {"total_records": total_records}


@router.get("/devices", response_model=DevicesResponse)
def get_devices(db: Session = Depends(get_db)):
    try:
        cached_devices = cache.get("devices:list")
        if cached_devices is not None:
            return json.loads(cached_devices)
    except (RedisError, ValueError):
        logger.warning("Could not read device list from Redis")

    now = datetime.now(timezone.utc)
    rows = db.query(Device).order_by(Device.device_id).all()
    devices = [
        DeviceRecord(
            id=row.device_id,
            type=row.device_type,
            location=row.location,
            status=(
                "inactive"
                if now - row.last_seen > timedelta(seconds=INACTIVE_AFTER_SECONDS)
                else row.status
            ),
            value=row.value,
            unit=row.unit,
            last_updated=row.last_seen
        ).model_dump(mode="json")
        for row in rows
    ]
    response = {
        "total": len(devices),
        "devices": devices
    }

    try:
        cache.setex("devices:list", 10, json.dumps(response))
    except RedisError:
        logger.warning("Could not cache device list in Redis")

    return response


@router.get("/telemetry", response_model=list[TelemetryRecord])
def get_telemetry(
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    return (
        db.query(Telemetry)
        .order_by(Telemetry.timestamp.desc(), Telemetry.id.desc())
        .limit(limit)
        .all()
    )
