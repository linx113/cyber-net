
import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.simulator import DeviceSimulator
from common.audit import RequestAuditMiddleware
from prometheus_fastapi_instrumentator import Instrumentator


simulator = DeviceSimulator()
simulator_task = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global simulator_task

    await simulator.connect_rabbitmq()

    simulator_task = asyncio.create_task(
        simulator.run()
    )

    yield

    simulator.stop()
    simulator_task.cancel()

    try:
        await simulator_task
    except asyncio.CancelledError:
        pass

    await simulator.close()


app = FastAPI(
    title="CyberNet Device Simulator",
    version="1.0.0",
    lifespan=lifespan
)
app.add_middleware(
    RequestAuditMiddleware,
    service_name="device-simulator"
)
Instrumentator().instrument(app).expose(app, include_in_schema=False)


@app.get("/health")
async def health():
    return {
        "status": "running",
        "devices": len(simulator.devices)
    }


@app.get("/devices")
async def get_devices():
    return {
        "total": len(simulator.devices),
        "devices": [
            {
                "id": device.id,
                "type": device.type,
                "location": device.location,
                "status": device.status,
                "value": device.value,
                "unit": {
                    "temperature": "C",
                    "humidity": "%",
                    "air_quality": "AQI",
                    "street_light": "on",
                    "traffic_sensor": "vehicles",
                    "traffic_light": "mode"
                }[device.type],
                "last_updated": device.last_updated,
                "brightness": device.brightness,
                "is_on": device.is_on
            }
            for device in simulator.devices
        ]
    }
