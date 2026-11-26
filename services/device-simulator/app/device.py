
import random
import uuid
from datetime import datetime, timezone


DEVICE_TYPES = {
    "temperature": {
        "unit": "C",
        "min": 15,
        "max": 35
    },
    "humidity": {
        "unit": "%",
        "min": 30,
        "max": 80
    },
    "air_quality": {
        "unit": "AQI",
        "min": 0,
        "max": 100
    },
    "street_light": {
        "unit": "on",
        "min": 0,
        "max": 1
    },
    "traffic_sensor": {
        "unit": "vehicles",
        "min": 0,
        "max": 100
    },
    "traffic_light": {
        "unit": "mode",
        "min": 0,
        "max": 3
    }
}


class Device:

    def __init__(
        self,
        device_type=None,
        update_interval=5,
        device_id=None,
        location=None
    ):
        self.id = device_id or str(uuid.uuid4())

        self.type = device_type or random.choice(
            list(DEVICE_TYPES.keys())
        )

        self.location = location or random.choice([
            "Sector-A", "Sector-B", "Sector-C", "Sector-D"
        ])

        self.status = "active"

        self.brightness = 100
        self.is_on = True
        self.value = None
        self.last_updated = None
        self.traffic_mode = "auto"
        self.update_interval = update_interval

    def execute_command(self, command, parameters=None):
        """
        Выполняет команду, адресованную устройству.
        """

        parameters = parameters or ""

        if command == "set_maintenance":
            enabled = parameters.lower().endswith("=true")
            self.status = "maintenance" if enabled else "active"
            return {"success": True, "status": self.status}

        if command == "restart":
            self.status = "active"
            self.last_updated = None
            return {"success": True, "message": "Device restarted"}

        if command == "set_interval":
            try:
                seconds = int(parameters.split("=")[1])
                if not 1 <= seconds <= 3600:
                    raise ValueError
            except (ValueError, IndexError):
                return {
                    "success": False,
                    "message": "Interval must be between 1 and 3600 seconds"
                }
            self.update_interval = seconds
            return {"success": True, "update_interval": seconds}

        if command == "set_traffic_mode":
            if self.type != "traffic_light":
                return {
                    "success": False,
                    "message": "Command requires a traffic light"
                }
            mode = parameters.split("=", 1)[-1].lower()
            if mode not in ("red", "yellow", "green", "auto"):
                return {
                    "success": False,
                    "message": "Mode must be red, yellow, green, or auto"
                }
            self.traffic_mode = mode
            return {"success": True, "traffic_mode": mode}

        if self.type != "street_light":
            return {
                "success": False,
                "message": "Command is not supported by this device"
            }

        if command == "set_lighting":
            try:
                brightness = int(
                    parameters.split("=")[1]
                )

                if not 0 <= brightness <= 100:
                    raise ValueError

            except (ValueError, IndexError):
                return {
                    "success": False,
                    "message": "Brightness must be between 0 and 100"
                }

            self.brightness = brightness
            self.is_on = brightness > 0

            return {
                "success": True,
                "message": "Lighting updated",
                "brightness": self.brightness,
                "is_on": self.is_on
            }

        elif command == "turn_on":
            self.is_on = True

            return {
                "success": True,
                "message": "Street light turned on",
                "brightness": self.brightness,
                "is_on": self.is_on
            }

        elif command == "turn_off":
            self.is_on = False

            return {
                "success": True,
                "message": "Street light turned off",
                "brightness": self.brightness,
                "is_on": self.is_on
            }

        return {
            "success": False,
            "message": f"Unknown command: {command}"
        }

    def generate_data(self, anomaly=False):

        config = DEVICE_TYPES[self.type]

        value = random.uniform(
            config["min"],
            config["max"]
        )

        if anomaly:
            value *= random.uniform(2, 4)

        if self.type == "street_light":
            value = int(self.is_on)
        elif self.type == "traffic_light":
            value = {"red": 0, "yellow": 1, "green": 2, "auto": 3}[
                self.traffic_mode
            ]

        timestamp = datetime.now(timezone.utc).isoformat()
        self.value = round(value, 2)
        self.last_updated = timestamp

        return {
            "device_id": self.id,
            "type": self.type,
            "location": self.location,
            "value": self.value,
            "unit": config["unit"],
            "status": self.status,
            "timestamp": timestamp
        }
