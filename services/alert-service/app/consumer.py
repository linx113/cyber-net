import os
import json
import aio_pika

from sqlalchemy.dialects.postgresql import insert

from app.database import SessionLocal
from app.models import Alert
from common.audit import log_message


RABBITMQ_URL = os.getenv(
    "RABBITMQ_URL",
    "amqp://cybernet:rabbitmq_dev@rabbitmq:5672/"
)


async def process_alert(message: aio_pika.IncomingMessage):

    async with message.process(requeue=True):

        data = json.loads(message.body.decode())
        event_id = data.get("event_id")
        db = SessionLocal()

        try:
            statement = insert(Alert).values(
                device_id=data["device_id"],
                device_type=data["device_type"],
                value=data["value"],
                severity=data.get("severity", "warning"),
                message=data["message"],
                event_id=data.get("event_id"),
                status="open"
            )
            db.execute(
                statement.on_conflict_do_nothing(
                    index_elements=[Alert.event_id]
                )
            )
            db.commit()

            print(
                f"[ALERT] Saved alert for device {data['device_id']}",
                flush=True
            )
            await log_message(
                "alert-service",
                "alerts.queue",
                event_id,
                "processed"
            )

        except Exception as error:
            db.rollback()
            await log_message(
                "alert-service",
                "alerts.queue",
                event_id,
                "failed",
                str(error)
            )
            raise

        finally:
            db.close()


async def start_consumer():

    connection = await aio_pika.connect_robust(
        RABBITMQ_URL
    )

    channel = await connection.channel()

    await channel.set_qos(prefetch_count=20)

    exchange = await channel.declare_exchange(
        "cybernet.events",
        aio_pika.ExchangeType.DIRECT,
        durable=True
    )

    queue = await channel.declare_queue(
        "alerts.queue",
        durable=True
    )

    await queue.bind(
        exchange,
        routing_key="alert.detected"
    )

    await queue.consume(process_alert)

    print("[ALERT] Consumer started", flush=True)

    return connection
