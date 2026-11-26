import os
import aio_pika

from aio_pika import Message, DeliveryMode


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

    queue = await _channel.declare_queue(
        "alerts.queue",
        durable=True
    )
    await queue.bind(
        _exchange,
        routing_key="alert.detected"
    )


async def publish_alert(data: dict):

    if _exchange is None:
        raise RuntimeError("RabbitMQ is not connected")

    message = Message(
        body=__import__("json").dumps(data).encode(),
        delivery_mode=DeliveryMode.PERSISTENT,
        content_type="application/json"
    )

    await _exchange.publish(
        message,
        routing_key="alert.detected",
        mandatory=True
    )


async def close_rabbitmq():

    global _connection, _channel, _exchange

    if _connection:
        await _connection.close()

    _connection = None
    _channel = None
    _exchange = None
