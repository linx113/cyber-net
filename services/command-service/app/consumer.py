
import json
import logging
import os
from uuid import UUID

import aio_pika

from app.database import SessionLocal
from app.models import DeviceCommand
from common.audit import log_message


logger = logging.getLogger("CommandConsumer")

RABBITMQ_URL = os.getenv(
    "RABBITMQ_URL",
    "amqp://cybernet:rabbitmq_dev@rabbitmq:5672/"
)

connection = None
channel = None


async def process_result(message: aio_pika.IncomingMessage):

    async with message.process(requeue=True):

        data = json.loads(message.body.decode())
        event_id = data.get("command_id")

        command_id = UUID(data["command_id"])
        new_status = data["status"]

        if new_status not in ("completed", "failed"):
            logger.warning("Unknown command status: %s", new_status)
            return

        db = SessionLocal()

        try:
            command = (
                db.query(DeviceCommand)
                .filter(DeviceCommand.id == command_id)
                .first()
            )

            if command is None:
                logger.warning(
                    "Command %s not found in database",
                    command_id
                )
                return

            command.status = new_status
            command.result = data.get("result")

            db.commit()

            logger.info(
                "Command %s updated: %s",
                command_id,
                new_status
            )

            logger.info(
                "Execution result: %s",
                data.get("result")
            )
            await log_message(
                "command-service",
                "commands.results.queue",
                event_id,
                "processed"
            )

        except Exception as error:
            db.rollback()
            logger.exception("Failed to update command status")
            await log_message(
                "command-service",
                "commands.results.queue",
                event_id,
                "failed",
                str(error)
            )
            raise

        finally:
            db.close()


async def start_consumer():

    global connection, channel

    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    channel = await connection.channel()

    exchange = await channel.declare_exchange(
        "cybernet.events",
        aio_pika.ExchangeType.DIRECT,
        durable=True
    )

    queue = await channel.declare_queue(
        "commands.results.queue",
        durable=True
    )

    await queue.bind(
        exchange,
        routing_key="command.completed"
    )

    await queue.bind(
        exchange,
        routing_key="command.failed"
    )

    await queue.consume(process_result)

    logger.info("Command result consumer started")


async def close_consumer():

    global connection, channel

    if connection:
        await connection.close()

    connection = None
    channel = None
