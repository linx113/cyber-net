
from contextlib import asynccontextmanager
import asyncio

from fastapi import FastAPI
from sqlalchemy import text

from app.consumer import start_consumer
from app.messaging import connect_rabbitmq, close_rabbitmq
from app.registry import engine, monitor_inactive_devices
from common.audit import RequestAuditMiddleware
from prometheus_fastapi_instrumentator import Instrumentator


connection = None
inactivity_task = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global connection, inactivity_task

    await connect_rabbitmq()
    connection = await start_consumer()
    inactivity_task = asyncio.create_task(monitor_inactive_devices())

    yield

    inactivity_task.cancel()
    try:
        await inactivity_task
    except asyncio.CancelledError:
        pass

    if connection:
        await connection.close()

    await close_rabbitmq()


app = FastAPI(
    title="CyberNet Analytics Service",
    version="1.0.0",
    lifespan=lifespan
)
app.add_middleware(
    RequestAuditMiddleware,
    service_name="analytics-service"
)
Instrumentator().instrument(app).expose(app, include_in_schema=False)


@app.get("/health")
async def health():
    with engine.connect() as database:
        database.execute(text("SELECT 1"))
    return {
        "service": "analytics-service",
        "status": "healthy"
    }
