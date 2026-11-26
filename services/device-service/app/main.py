from contextlib import asynccontextmanager
import asyncio
import os

from fastapi import FastAPI

from app.routes import router
from app.database import Base, engine
from app import models
from app.messaging import (
    connect_rabbitmq,
    close_rabbitmq
)
from app.outbox import dispatch_outbox
from common.audit import RequestAuditMiddleware
from prometheus_fastapi_instrumentator import Instrumentator


@asynccontextmanager
async def lifespan(app: FastAPI):

    Base.metadata.create_all(bind=engine)

    await connect_rabbitmq()
    outbox_task = asyncio.create_task(dispatch_outbox())

    yield

    outbox_task.cancel()
    try:
        await outbox_task
    except asyncio.CancelledError:
        pass

    await close_rabbitmq()


app = FastAPI(
    title="CyberNet Device Service",
    version="1.0.0",
    lifespan=lifespan
)
app.add_middleware(
    RequestAuditMiddleware,
    service_name=os.getenv("INSTANCE_ID", "device-service")
)
Instrumentator().instrument(app).expose(app, include_in_schema=False)


app.include_router(
    router,
    prefix="/api"
)


@app.get("/")
def root():

    return {
        "service": "CyberNet Device Service",
        "status": "running"
    }
