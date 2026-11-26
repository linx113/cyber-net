
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import Base, engine, SessionLocal
from app import models
from app.consumer import start_consumer
from app.schemas import AlertStatusUpdate
from common.audit import RequestAuditMiddleware
from prometheus_fastapi_instrumentator import Instrumentator


connection = None


def initialize_schema():
    Base.metadata.create_all(bind=engine)
    with engine.begin() as connection:
        connection.execute(text(
            "ALTER TABLE alerts ADD COLUMN IF NOT EXISTS event_id VARCHAR(200)"
        ))
        connection.execute(text(
            "ALTER TABLE alerts ADD COLUMN IF NOT EXISTS status "
            "VARCHAR(20) NOT NULL DEFAULT 'open'"
        ))
        connection.execute(text(
            "CREATE UNIQUE INDEX IF NOT EXISTS uq_alerts_event_id "
            "ON alerts (event_id)"
        ))


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    global connection

    initialize_schema()

    connection = await start_consumer()

    yield

    if connection:
        await connection.close()


app = FastAPI(
    title="CyberNet Alert Service",
    version="1.0.0",
    lifespan=lifespan
)
app.add_middleware(
    RequestAuditMiddleware,
    service_name="alert-service"
)
Instrumentator().instrument(app).expose(app, include_in_schema=False)


@app.get("/health")
async def health():
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return {
        "service": "alert-service",
        "status": "healthy"
    }


@app.get("/alerts")
def get_alerts(
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    return (
        db.query(models.Alert)
        .order_by(models.Alert.created_at.desc(), models.Alert.id.desc())
        .limit(limit)
        .all()
    )

@app.get("/alerts/count")
def get_alerts_count(db: Session = Depends(get_db)):
    return {
        "count": db.query(models.Alert).count()
    }


@app.patch("/alerts/{alert_id}/status")
def update_alert_status(
    alert_id: int,
    payload: AlertStatusUpdate,
    db: Session = Depends(get_db)
):
    alert = db.query(models.Alert).filter(
        models.Alert.id == alert_id
    ).first()
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.status = payload.status
    try:
        db.commit()
        db.refresh(alert)
    except SQLAlchemyError as error:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to update alert status"
        ) from error

    return alert
