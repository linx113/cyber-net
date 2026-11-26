# CyberNet

CyberNet is a Docker Compose demo of a distributed smart-city telemetry and
device-command system. The stack includes a React dashboard, Nginx API load
balancer, three Device Service instances, a configurable simulator, RabbitMQ,
analytics and alert services, two PostgreSQL databases, and Redis.

## Run the system

Requirements: Docker Desktop with Docker Compose.

```powershell
docker compose up --build -d
```

Open the dashboard at <http://localhost:3000>. The API load balancer is
available at <http://localhost:8080>; RabbitMQ management is at
<http://localhost:15672>. Prometheus is available at <http://localhost:9090>
and Grafana at <http://localhost:3001> (default development credentials:
`admin` / `cybernet_dev`; override with `GRAFANA_USER` and
`GRAFANA_PASSWORD`).

Copy `.env.example` to `.env` to customize settings. Never commit `.env` or
production credentials.

The simulator supports 100–10,000 virtual devices. Configure it before startup
using environment variables (or a root `.env` file):

| Variable | Default | Description |
| --- | --- | --- |
| `DEVICE_COUNT` | `100` | Virtual devices, from 100 through 10,000 |
| `UPDATE_INTERVAL` | `5` | Seconds between telemetry updates |
| `ANOMALY_RATE` | `0.05` | Fraction of readings generated as anomalies |
| `TEMPERATURE_WARNING_C` | `40` | Temperature warning threshold |
| `TEMPERATURE_CRITICAL_C` | `60` | Temperature critical threshold |
| `TEMPERATURE_MIN_C` / `TEMPERATURE_MAX_C` | `-20` / `60` | Permitted temperature range (`TEMPERATURE_MAX_C` must be at least the critical threshold) |
| `HUMIDITY_MIN` / `HUMIDITY_MAX` | `20` / `80` | Permitted humidity range |
| `AIR_QUALITY_MIN` | `25` | Values below this trigger an air-quality alert |
| `AIR_QUALITY_RANGE_MIN` / `AIR_QUALITY_RANGE_MAX` | `0` / `100` | Permitted air-quality range |
| `STREET_LIGHT_MIN` / `STREET_LIGHT_MAX` | `0` / `1` | Permitted street-light range |
| `TRAFFIC_SENSOR_MIN` / `TRAFFIC_SENSOR_MAX` | `0` / `100` | Permitted traffic range |
| `TRAFFIC_LIGHT_MIN` / `TRAFFIC_LIGHT_MAX` | `0` / `3` | Permitted traffic-light mode range |
| `POSTGRES_PASSWORD` | `cybernet_dev` | PostgreSQL password |
| `RABBITMQ_PASSWORD` | `rabbitmq_dev` | RabbitMQ password |
| `GRAFANA_USER` / `GRAFANA_PASSWORD` | `admin` / `cybernet_dev` | Grafana login |
| `INACTIVE_AFTER_SECONDS` | `300` | Time without telemetry before a device is inactive |

Change the development passwords before exposing the stack outside a trusted
local environment.

## Main endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/api/telemetry` | Accept telemetry and persist it with an outbox event |
| `GET` | `/api/telemetry?limit=100` | Read recent telemetry |
| `GET` | `/api/telemetry/count` | Read total telemetry count (Redis cached) |
| `GET` | `/api/devices` | List the simulator's devices and latest readings |
| `GET` | `/api/alerts` | Read recent alerts |
| `GET` | `/api/alerts/count` | Read total alert count |
| `GET` | `/api/commands` | Read recent device commands |
| `POST` | `/api/commands` | Queue a command for a device |
| `GET` | `/api/load-tests` | Read load-test state and saved results |
| `POST` | `/api/load-tests/run` | Start a load test |

The dashboard refreshes its device, telemetry, and alert data every five
seconds. The Commands page supports street-light, traffic-light, maintenance,
restart, and telemetry-interval commands. Alerts can be acknowledged or
resolved from the alert history.

## Load test

Run the optional load-tester container after starting the stack:

```powershell
docker compose --profile tools run --rm load-tester
```

By default it tests 100, 500, and 1,000 concurrent clients with one request per
client at each level. Set `REQUESTS_PER_CLIENT` or `CONCURRENCY_LEVELS` in
`.env` to adjust the workload. Per-level successes, errors, average and maximum
response times, throughput, and duration are printed and appended to the
`load-test-results` Docker volume as `/results/load-test.csv`.
The dashboard shows the latest results and the CSV is retained across
container restarts.

To probe overload behavior, raise `CONCURRENCY_LEVELS` and
`REQUESTS_PER_CLIENT` in `.env` (for example `1000,2000,5000` and `5`) and
run the same tester. It sends telemetry through the normal API path, exercising
PostgreSQL writes, outbox publishing, and RabbitMQ consumers. Compare errors,
latency, Prometheus service metrics, RabbitMQ queue depth in its management
UI, and service logs. This is a stress experiment; use a local development
stack because it intentionally creates a large workload.

To compare one, two, and three Device Service instances, stop the instances
not under test, then run a test against the already-running stack:

```powershell
docker compose stop device-service-2 device-service-3
docker compose --profile tools run --rm --no-deps load-tester
docker compose start device-service-2 device-service-3
```

The test output includes which service instance handled each successful
request. Run the same test with one, two, and three instances active.

## Monitoring and backups

Prometheus scrapes service request metrics and Grafana provisions a dashboard
automatically. A manual backup of both PostgreSQL databases is available as a
one-shot tools-profile service:

```powershell
docker compose --profile tools run --rm db-backup
```

Backups are gzip-compressed under the root `backups/` directory, which is
ignored by Git. Copy them to secure storage before deleting local files. To
restore a dump, decompress it and pipe it to `psql` against the corresponding
database using the PostgreSQL user and database named above.

When upgrading an older local stack, alert history may still be in the
`postgres-logs` volume. This version stores new alerts in `postgres-main` as
required; existing rows are left untouched in the old volume and are not
automatically copied.

## Resilience checks

Stop one or two Device Service instances and check that requests still pass
through Nginx to the remaining instances:

```powershell
docker compose stop device-service-1
docker compose stop device-service-2
docker compose start device-service-1 device-service-2
```

Stop all three to verify the API becomes unavailable, then restart them. Stop
RabbitMQ while the system is running to verify that accepted telemetry and
commands remain in their PostgreSQL outboxes and are retried after RabbitMQ
recovers:

```powershell
docker compose stop rabbitmq
docker compose start rabbitmq
```

The telemetry outbox is written in the same transaction as telemetry, and the
command outbox is written in the same transaction as each command. Events are
marked published only after RabbitMQ accepts them. Consumers requeue messages
when processing fails. This provides at-least-once delivery; a process failure
between broker publication and marking the outbox row can produce a duplicate
event.

| Experiment | Expected behavior | Data and recovery |
| --- | --- | --- |
| Stop one Device Service | Nginx routes requests to the other two | Persisted records remain available |
| Stop two Device Services | The remaining instance serves requests at reduced capacity | Persisted records remain available |
| Stop all Device Services | API writes fail until an instance returns | The running simulator retries its current sample in memory; restarting the simulator discards pending retries |
| Stop RabbitMQ | Telemetry and commands can still be accepted by PostgreSQL | Outboxes publish after RabbitMQ returns; consumers retry failed deliveries |
| Stop `postgres-main` | Telemetry and command writes fail; alert storage pauses | The simulator retries failed telemetry; accepted outbox rows remain durable; alert events are requeued |
| Stop `postgres-logs` | Audit logs cannot be persisted | Application requests continue after a bounded logging timeout; missed audit records are not replayed |
| Restart all services | Services reconnect to their dependencies | Committed PostgreSQL data and durable RabbitMQ messages survive in named volumes |

After an experiment, restore stopped services with `docker compose start` or
bring the complete stack back with `docker compose up -d`. The simulator's
retry queue is in memory, so a process restart can lose the sample currently
being retried; later samples resume normally.

Inspect service state and logs with:

```powershell
docker compose ps
docker compose logs -f device-service-1 analytics-service alert-service
```

Remove containers without deleting persistent data with `docker compose down`.
Use `docker compose down -v` only when intentionally deleting database, broker,
and load-test result volumes.
