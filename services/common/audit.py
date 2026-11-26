import asyncio
import atexit
import logging
import os
import time
import uuid

import httpx
from starlette.middleware.base import BaseHTTPMiddleware


LOG_SERVICE_URL = os.getenv(
    "LOG_SERVICE_URL",
    "http://logging-service:8000"
).rstrip("/")
logger = logging.getLogger("cybernet.audit")
client = httpx.Client(timeout=0.75)
atexit.register(client.close)


async def _send(path: str, payload: dict):
    try:
        response = await asyncio.to_thread(
            client.post,
            f"{LOG_SERVICE_URL}{path}",
            json=payload
        )
        response.raise_for_status()
    except httpx.HTTPError:
        logger.exception("Could not persist audit event to logging service")


class RequestAuditMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, service_name: str):
        super().__init__(app)
        self.service_name = service_name

    async def dispatch(self, request, call_next):
        started = time.perf_counter()
        request_id = request.headers.get("x-request-id") or uuid.uuid4().hex
        forwarded_for = request.headers.get("x-forwarded-for", "")
        client_ip = (
            forwarded_for.split(",", 1)[0].strip()
            or (request.client.host if request.client else "unknown")
        )
        error = None

        try:
            response = await call_next(request)
        except Exception as exception:
            error = str(exception)[:2000]
            await _send("/logs", {
                "request_id": request_id,
                "service": self.service_name,
                "path": request.url.path,
                "method": request.method,
                "client_ip": client_ip,
                "status_code": 500,
                "processing_ms": round((time.perf_counter() - started) * 1000, 2),
                "error": error
            })
            raise

        if response.status_code >= 400:
            error = f"HTTP {response.status_code}"
        await _send("/logs", {
            "request_id": request_id,
            "service": self.service_name,
            "path": request.url.path,
            "method": request.method,
            "client_ip": client_ip,
            "status_code": response.status_code,
            "processing_ms": round((time.perf_counter() - started) * 1000, 2),
            "error": error
        })
        response.headers["X-Request-ID"] = request_id
        return response


async def log_message(
    service: str,
    queue: str,
    event_id: str | None,
    outcome: str,
    error: str | None = None
):
    await _send("/logs/messages", {
        "service": service,
        "queue": queue,
        "event_id": event_id,
        "outcome": outcome,
        "error": error[:2000] if error else None
    })
