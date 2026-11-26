
import asyncio
import random
import logging
import json
import os

import httpx
import aio_pika

from app.device import DEVICE_TYPES, Device
from app.config import (
    DEVICE_COUNT,
    UPDATE_INTERVAL,
    ANOMALY_RATE,
    API_URL
)
from common.audit import log_message

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DeviceSimulator")

RABBITMQ_URL = os.getenv(
    "RABBITMQ_URL",
    "amqp://cybernet:rabbitmq_dev@rabbitmq:5672/"
)


class DeviceSimulator:

    def __init__(self):
        self.devices = [
            Device(
                device_type=list(DEVICE_TYPES)[index % len(DEVICE_TYPES)],
                update_interval=UPDATE_INTERVAL,
                device_id=f"SIM-{index + 1:05d}",
                location=f"Sector-{chr(65 + index % 4)}"
            )
            for index in range(DEVICE_COUNT)
        ]

        self.devices_by_id = {
            device.id: device
            for device in self.devices
        }

        self.running = False
        self.rabbitmq_connection = None
        self.rabbitmq_channel = None

    async def publish_command_result(self, data, result):

        exchange = await self.rabbitmq_channel.declare_exchange(
            "cybernet.events",
            aio_pika.ExchangeType.DIRECT,
            durable=True
        )

        status = "completed" if result["success"] else "failed"

        event = {
            "command_id": data["id"],
            "device_id": data["device_id"],
            "status": status,
            "result": result
        }

        message = aio_pika.Message(
            body=json.dumps(event).encode(),
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            content_type="application/json"
        )

        await exchange.publish(
            message,
            routing_key=f"command.{status}",
            mandatory=True
        )

        logger.info(
            "Command result published: %s (%s)",
            data["id"],
            status
        )

    async def connect_rabbitmq(self):

        self.rabbitmq_connection = await aio_pika.connect_robust(
            RABBITMQ_URL
        )

        self.rabbitmq_channel = await self.rabbitmq_connection.channel()

        exchange = await self.rabbitmq_channel.declare_exchange(
            "cybernet.commands",
            aio_pika.ExchangeType.DIRECT,
            durable=True
        )

        queue = await self.rabbitmq_channel.declare_queue(
            "device.commands.queue",
            durable=True
        )

        await queue.bind(
            exchange,
            routing_key="device.command"
        )

        await queue.consume(self.process_command)

        logger.info("RabbitMQ command consumer started")

    async def process_command(self, message: aio_pika.IncomingMessage):

        async with message.process(requeue=True):
            data = {}
            try:
                data = json.loads(message.body.decode())

                device_id = data.get("device_id")
                command = data.get("command")
                parameters = data.get("parameters")

                device = self.devices_by_id.get(device_id)

                if device is None:
                    logger.warning(
                        "Command rejected: device %s not found",
                        device_id
                    )

                    await self.publish_command_result(
                        data,
                        {
                            "success": False,
                            "message": "Device not found"
                        }
                    )
                    return

                result = device.execute_command(
                    command,
                    parameters
                )

                await self.publish_command_result(data, result)
                await log_message(
                    "device-simulator",
                    "device.commands.queue",
                    data.get("id"),
                    "processed" if result["success"] else "failed",
                    result.get("message") if not result["success"] else None
                )

                if result["success"]:
                    logger.info(
                        "Command %s executed on device %s: %s",
                        command,
                        device_id,
                        result
                    )
                else:
                    logger.warning(
                        "Command %s failed on device %s: %s",
                        command,
                        device_id,
                        result["message"]
                    )

            except Exception as error:
                logger.exception("Failed to process device command")
                await log_message(
                    "device-simulator",
                    "device.commands.queue",
                    data.get("id"),
                    "failed",
                    str(error)
                )
                raise

    async def send_data(self, client, device):

        anomaly = random.random() < ANOMALY_RATE

        data = device.generate_data(anomaly)
        attempt = 0

        while self.running:
            try:
                response = await client.post(API_URL, json=data)
                if response.status_code < 400:
                    return
                if response.status_code != 429 and response.status_code < 500:
                    logger.error(
                        "Device %s: non-retryable HTTP %s",
                        device.id,
                        response.status_code
                    )
                    return
                logger.warning(
                    "Device %s: retrying after HTTP %s",
                    device.id,
                    response.status_code
                )
            except httpx.HTTPError as error:
                logger.warning(
                    "Device %s: telemetry request failed; retrying: %s",
                    device.id,
                    error
                )

            await asyncio.sleep(min(2 ** min(attempt, 6), 60))
            attempt += 1

    async def run(self):

        self.running = True

        logger.info(
            "Starting %s virtual devices",
            len(self.devices)
        )

        limits = httpx.Limits(
            max_connections=1000,
            max_keepalive_connections=200
        )

        timeout = httpx.Timeout(10.0)

        async with httpx.AsyncClient(
            limits=limits,
            timeout=timeout
        ) as client:
            async def run_device(device):
                await asyncio.sleep(
                    random.uniform(0, device.update_interval)
                )
                while self.running:
                    await self.send_data(client, device)
                    await asyncio.sleep(device.update_interval)

            await asyncio.gather(
                *(run_device(device) for device in self.devices)
            )

    def stop(self):
        self.running = False

    async def close(self):

        if self.rabbitmq_connection:
            await self.rabbitmq_connection.close()
            self.rabbitmq_connection = None
