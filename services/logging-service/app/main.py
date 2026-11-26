from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app import models
from app.database import Base, engine, get_db
from app.models import MessageLog, RequestLog
from app.schemas import (
    MessageLogCreate,
    MessageLogResponse,
    RequestLogCreate,
    RequestLogResponse
)
from prometheus_fastapi_instrumentator import Instrumentator


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="CyberNet Logging Service", lifespan=lifespan)
Instrumentator().instrument(app).expose(app, include_in_schema=False)


@app.get("/health")
def health():
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return {"service": "logging-service", "status": "healthy"}


@app.post("/logs", response_model=RequestLogResponse, status_code=201)
def create_request_log(
    payload: RequestLogCreate,
    db: Session = Depends(get_db)
):
    try:
        record = RequestLog(**payload.model_dump())
        db.add(record)
        db.commit()
        db.refresh(record)
        return record
    finally:
        db.close()


@app.post("/logs/messages", response_model=MessageLogResponse, status_code=201)
def create_message_log(
    payload: MessageLogCreate,
    db: Session = Depends(get_db)
):
    try:
        record = MessageLog(**payload.model_dump())
        db.add(record)
        db.commit()
        db.refresh(record)
        return record
    finally:
        db.close()


@app.get("/logs", response_model=list[RequestLogResponse])
def get_request_logs(
    limit: int = Query(default=100, ge=1, le=1000),
    service: str | None = None,
    db: Session = Depends(get_db)
):
    query = db.query(RequestLog)
    if service:
        query = query.filter(RequestLog.service == service)
    return query.order_by(RequestLog.created_at.desc()).limit(limit).all()


@app.get("/logs/messages", response_model=list[MessageLogResponse])
def get_message_logs(
    limit: int = Query(default=100, ge=1, le=1000),
    service: str | None = None,
    db: Session = Depends(get_db)
):
    query = db.query(MessageLog)
    if service:
        query = query.filter(MessageLog.service == service)
    return query.order_by(MessageLog.processed_at.desc()).limit(limit).all()
