import os

DEVICE_COUNT = int(os.getenv("DEVICE_COUNT", 100))
UPDATE_INTERVAL = float(os.getenv("UPDATE_INTERVAL", 5))
ANOMALY_RATE = float(os.getenv("ANOMALY_RATE", 0.05))

if not 100 <= DEVICE_COUNT <= 10_000:
    raise ValueError("DEVICE_COUNT must be between 100 and 10000")
if UPDATE_INTERVAL <= 0:
    raise ValueError("UPDATE_INTERVAL must be positive")
if not 0 <= ANOMALY_RATE <= 1:
    raise ValueError("ANOMALY_RATE must be between 0 and 1")

API_URL = os.getenv(
    "API_URL",
    "http://nginx/api/telemetry"
)
