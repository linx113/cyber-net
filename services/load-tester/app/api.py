import asyncio
import csv
import logging

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

from app.main import RESULTS_FILE, run_test, save_results
from common.audit import RequestAuditMiddleware
from prometheus_fastapi_instrumentator import Instrumentator


logger = logging.getLogger(__name__)
app = FastAPI(title="CyberNet Load Tester")
app.add_middleware(
    RequestAuditMiddleware,
    service_name="load-test-api"
)
Instrumentator().instrument(app).expose(app, include_in_schema=False)
_running = False
_run_task: asyncio.Task | None = None
_last_error: str | None = None


class LoadTestRequest(BaseModel):
    concurrency_levels: list[int] = Field(
        default_factory=lambda: [100, 500, 1000],
        min_length=1,
        max_length=10
    )
    requests_per_client: int = Field(default=1, ge=1, le=1000)


def read_results():
    if not RESULTS_FILE.exists():
        return []
    with RESULTS_FILE.open(newline="", encoding="utf-8") as source:
        return list(csv.DictReader(source))


async def execute_load_test(payload: LoadTestRequest):
    global _running, _last_error
    try:
        results = []
        for concurrency in payload.concurrency_levels:
            results.append(
                await run_test(concurrency, payload.requests_per_client)
            )
        save_results(results)
        _last_error = None
    except Exception as error:
        _last_error = str(error)
        logger.exception("Load test failed")
    finally:
        _running = False


@app.get("/health")
def health():
    return {"service": "load-test-api", "status": "healthy"}


@app.get("/load-tests")
def get_load_tests():
    return {
        "running": _running,
        "last_error": _last_error,
        "results": read_results()
    }


@app.post("/load-tests/run", status_code=status.HTTP_202_ACCEPTED)
async def start_load_test(payload: LoadTestRequest):
    global _running, _run_task, _last_error
    if any(level < 1 or level > 10_000 for level in payload.concurrency_levels):
        raise HTTPException(
            status_code=422,
            detail="Concurrency levels must be between 1 and 10000"
        )
    if _running:
        raise HTTPException(
            status_code=409,
            detail="A load test is already running"
        )
    _running = True
    _last_error = None
    _run_task = asyncio.create_task(execute_load_test(payload))
    return {"status": "started", "concurrency_levels": payload.concurrency_levels}
