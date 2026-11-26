import os
import json
import aio_pika

from aio_pika import DeliveryMode, Message


RABBITMQ_URL = os.getenv(
    "RABBITMQ_URL",
    "amqp://cybernet:rabbitmq_dev@rabbitmq:5672/"
)

_connection = None
_channel = None
_exchange = None


async def connect_rabbitmq():

    global _connection, _channel, _exchange

    _connection = await aio_pika.connect_robust(
        RABBITMQ_URL
    )

    _channel = await _connection.channel()

    _exchange = await _channel.declare_exchange(
        "cybernet.events",
        aio_pika.ExchangeType.DIRECT,
        durable=True
    )

    await _channel.declare_queue(
        "telemetry.queue",
        durable=True
    )

    await _channel.declare_queue(
        "telemetry.dead_letter",
        durable=True
    )

    queue = await _channel.get_queue(
        "telemetry.queue"
    )

    await queue.bind(
        _exchange,
        routing_key="telemetry.received"
    )


async def publish_telemetry(data: dict):

    if _exchange is None:
        raise RuntimeError("RabbitMQ is not connected")

    message = Message(
        body=json.dumps(data).encode(),
        delivery_mode=DeliveryMode.PERSISTENT,
        content_type="application/json"
    )

    await _exchange.publish(
        message,
        routing_key="telemetry.received",
        mandatory=True
    )


async def close_rabbitmq():

    global _connection, _channel, _exchange

    if _connection:
        await _connection.close()

    _connection = None
    _channel = None
    _exchange = None
