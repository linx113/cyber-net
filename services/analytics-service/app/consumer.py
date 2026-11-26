import os
import json
import aio_pika
from app.messaging import publish_alert
from app.analyzer import analyze_telemetry
from common.audit import log_message


RABBITMQ_URL = os.getenv(
    "RABBITMQ_URL",
    "amqp://cybernet:rabbitmq_dev@rabbitmq:5672/"
)


async def process_message(message: aio_pika.IncomingMessage):

    async with message.process(requeue=True):

        data = json.loads(message.body.decode())
        event_id = data.get("event_id")
        try:
            result = analyze_telemetry(data)
            if result["status"] == "anomaly":
                await publish_alert(result)

            print(
                f"[ANALYTICS] {json.dumps(result)}",
                flush=True
            )
            await log_message(
                "analytics-service",
                "telemetry.queue",
                event_id,
                "processed"
            )
        except Exception as error:
            await log_message(
                "analytics-service",
                "telemetry.queue",
                event_id,
                "failed",
                str(error)
            )
            raise


async def start_consumer():

    connection = await aio_pika.connect_robust(
        RABBITMQ_URL
    )

    channel = await connection.channel()

    await channel.set_qos(prefetch_count=50)

    queue = await channel.declare_queue(
        "telemetry.queue",
        durable=True
    )

    await queue.consume(process_message)

    print("[ANALYTICS] Consumer started", flush=True)

    return connection
