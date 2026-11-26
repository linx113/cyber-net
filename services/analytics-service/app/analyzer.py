
import os


THRESHOLDS = {
    "temperature": {
        "min": float(os.getenv("TEMPERATURE_MIN_C", "-20")),
        "max": float(os.getenv("TEMPERATURE_MAX_C", "60"))
    },
    "humidity": {
        "min": float(os.getenv("HUMIDITY_MIN", "20")),
        "max": float(os.getenv("HUMIDITY_MAX", "80"))
    },
    "air_quality": {
        "min": float(os.getenv("AIR_QUALITY_RANGE_MIN", "0")),
        "max": float(os.getenv("AIR_QUALITY_RANGE_MAX", "100"))
    },
    "street_light": {
        "min": float(os.getenv("STREET_LIGHT_MIN", "0")),
        "max": float(os.getenv("STREET_LIGHT_MAX", "1"))
    },
    "traffic_sensor": {
        "min": float(os.getenv("TRAFFIC_SENSOR_MIN", "0")),
        "max": float(os.getenv("TRAFFIC_SENSOR_MAX", "100"))
    },
    "traffic_light": {
        "min": float(os.getenv("TRAFFIC_LIGHT_MIN", "0")),
        "max": float(os.getenv("TRAFFIC_LIGHT_MAX", "3"))
    }
}

TEMPERATURE_WARNING_C = float(
    os.getenv("TEMPERATURE_WARNING_C", "40")
)
TEMPERATURE_CRITICAL_C = float(
    os.getenv("TEMPERATURE_CRITICAL_C", "60")
)
AIR_QUALITY_MIN = float(os.getenv("AIR_QUALITY_MIN", "25"))

if TEMPERATURE_CRITICAL_C <= TEMPERATURE_WARNING_C:
    raise ValueError("TEMPERATURE_CRITICAL_C must exceed TEMPERATURE_WARNING_C")
if THRESHOLDS["temperature"]["max"] < TEMPERATURE_CRITICAL_C:
    raise ValueError("TEMPERATURE_MAX_C must be at least TEMPERATURE_CRITICAL_C")
if not 0 <= AIR_QUALITY_MIN <= 100:
    raise ValueError("AIR_QUALITY_MIN must be between 0 and 100")
for device_type, limits in THRESHOLDS.items():
    if limits["min"] >= limits["max"]:
        raise ValueError(f"Invalid configured range for {device_type}")


def analyze_telemetry(data: dict):

    device_type = data.get("type")
    value = data.get("value")
    device_id = data.get("device_id")
    event_id = data.get("event_id")

    if device_type not in THRESHOLDS:
        return {
            "status": "unknown",
            "device_id": device_id,
            "event_id": event_id,
            "message": "Unknown device type"
        }

    if device_type == "temperature":
        if value > TEMPERATURE_CRITICAL_C:
            return {
                "status": "anomaly",
                "severity": "critical",
                "device_id": device_id,
                "event_id": event_id,
                "device_type": device_type,
                "value": value,
                "message": "Temperature exceeded the critical threshold"
            }

        if value > TEMPERATURE_WARNING_C:
            return {
                "status": "anomaly",
                "severity": "warning",
                "device_id": device_id,
                "event_id": event_id,
                "device_type": device_type,
                "value": value,
                "message": "Temperature exceeded the warning threshold"
            }

    if device_type == "air_quality" and value < AIR_QUALITY_MIN:
        return {
            "status": "anomaly",
            "severity": "critical",
            "device_id": device_id,
            "event_id": event_id,
            "device_type": device_type,
            "value": value,
            "message": "Air quality fell below the minimum threshold"
        }

    limits = THRESHOLDS[device_type]
    minimum = limits["min"]
    maximum = limits["max"]

    if value < minimum or value > maximum:
        severity = "critical"
        status = "anomaly"
        message = "Value outside permitted range"

    elif device_type != "street_light" and (
        value <= minimum + (maximum - minimum) * 0.1
        or value >= maximum - (maximum - minimum) * 0.1
    ):
        severity = "warning"
        status = "anomaly"
        message = "Value approaching permitted limit"

    else:
        severity = "info"
        status = "normal"
        message = "Telemetry is normal"

    return {
        "status": status,
        "severity": severity,
        "device_id": device_id,
        "event_id": event_id,
        "device_type": device_type,
        "value": value,
        "message": message
    }
