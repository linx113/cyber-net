import os

from redis import Redis


cache = Redis.from_url(
    os.getenv("REDIS_URL", "redis://redis:6379/0"),
    decode_responses=True,
    socket_connect_timeout=1,
    socket_timeout=1,
)
