
from contextlib import asynccontextmanager
import asyncio

from fastapi import FastAPI
from sqlalchemy import text

from app.database import Base, engine
from app import models
from app.messaging import connect_rabbitmq, close_rabbitmq
from app.consumer import start_consumer, close_consumer
from app.routes import router
from app.outbox import dispatch_outbox
from common.audit import RequestAuditMiddleware
from prometheus_fastapi_instrumentator import Instrumentator


@asynccontextmanager
async def lifespan(app: FastAPI):

    Base.metadata.create_all(bind=engine)

    await connect_rabbitmq()
    await start_consumer()
    outbox_task = asyncio.create_task(dispatch_outbox())

    yield

    outbox_task.cancel()
    try:
        await outbox_task
    except asyncio.CancelledError:
        pass

    await close_consumer()
    await close_rabbitmq()


app = FastAPI(
    title="CyberNet Command Service",
    version="1.0.0",
    lifespan=lifespan
)
app.add_middleware(
    RequestAuditMiddleware,
    service_name="command-service"
)
Instrumentator().instrument(app).expose(app, include_in_schema=False)

app.include_router(router)


@app.get("/health")
async def health():
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return {
        "service": "command-service",
        "status": "healthy"
    }
