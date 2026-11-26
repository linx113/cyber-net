import asyncio
import csv
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx


API_URL = os.getenv("API_URL", "http://nginx/api/telemetry")
CONCURRENCY_LEVELS = [
    int(value)
    for value in os.getenv("CONCURRENCY_LEVELS", "100,500,1000").split(",")
]
REQUESTS_PER_CLIENT = int(os.getenv("REQUESTS_PER_CLIENT", "1"))
RESULTS_FILE = Path(os.getenv("RESULTS_FILE", "/results/load-test.csv"))


async def run_test(concurrency: int, requests_per_client: int | None = None) -> dict:
    requests_per_client = requests_per_client or REQUESTS_PER_CLIENT
    latencies = []
    successes = 0
    errors = 0
    instances = {}
    limits = httpx.Limits(
        max_connections=concurrency,
        max_keepalive_connections=concurrency
    )
    timeout = httpx.Timeout(30.0)
    started = time.perf_counter()

    async with httpx.AsyncClient(limits=limits, timeout=timeout) as client:
        async def send_requests(client_id: int):
            nonlocal successes, errors

            for _ in range(requests_per_client):
                payload = {
                    "device_id": f"LOAD-{concurrency}-{client_id}",
                    "type": "temperature",
                    "location": "Load-Test",
                    "value": 24.0,
                    "unit": "C",
                    "status": "active",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                request_started = time.perf_counter()
                try:
                    response = await client.post(API_URL, json=payload)
                    latencies.append((time.perf_counter() - request_started) * 1000)
                    if response.is_success:
                        body = response.json()
                        successes += 1
                        instance = body.get("processed_by")
                        if instance:
                            instances[instance] = instances.get(instance, 0) + 1
                    else:
                        errors += 1
                except (httpx.HTTPError, ValueError):
                    latencies.append((time.perf_counter() - request_started) * 1000)
                    errors += 1

        await asyncio.gather(
            *(send_requests(client_id) for client_id in range(concurrency))
        )

    elapsed = time.perf_counter() - started
    total = successes + errors
    result = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "concurrency": concurrency,
        "requests": total,
        "successes": successes,
        "errors": errors,
        "average_response_ms": round(sum(latencies) / len(latencies), 2) if latencies else 0,
        "max_response_ms": round(max(latencies), 2) if latencies else 0,
        "requests_per_second": round(total / elapsed, 2) if elapsed else 0,
        "duration_seconds": round(elapsed, 2),
        "instance_distribution": json.dumps(instances, sort_keys=True)
    }
    return result


def save_results(results: list[dict]):
    RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    file_exists = RESULTS_FILE.exists()
    with RESULTS_FILE.open("a", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=results[0].keys())
        if not file_exists:
            writer.writeheader()
        writer.writerows(results)


async def main():
    if not CONCURRENCY_LEVELS or any(level <= 0 for level in CONCURRENCY_LEVELS):
        raise ValueError("CONCURRENCY_LEVELS must contain positive integers")
    if REQUESTS_PER_CLIENT <= 0:
        raise ValueError("REQUESTS_PER_CLIENT must be a positive integer")

    results = []
    for concurrency in CONCURRENCY_LEVELS:
        result = await run_test(concurrency)
        results.append(result)
        print(json.dumps(result), flush=True)

    save_results(results)
    print(
        "Concurrency | Requests | Success | Errors | Avg ms | Max ms | Requests/s",
        flush=True
    )
    for result in results:
        print(
            "{concurrency:11} | {requests:8} | {successes:7} | {errors:6} | "
            "{average_response_ms:6.2f} | {max_response_ms:6.2f} | "
            "{requests_per_second:10.2f}".format(**result),
            flush=True
        )
    print(f"Results appended to {RESULTS_FILE}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
