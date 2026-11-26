from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field, ConfigDict

class TelemetryInput(BaseModel):
    device_id: str = Field(min_length=1, max_length=100)
    type: Literal[
        "temperature", "humidity", "air_quality", "street_light",
        "traffic_sensor", "traffic_light"
    ]
    location: str = Field(min_length=1, max_length=100)
    value: float = Field(allow_inf_nan=False)
    unit: str = Field(min_length=1, max_length=20)
    status: Literal["active", "inactive", "maintenance"]
    timestamp: datetime


class DeviceRecord(BaseModel):
    id: str
    type: str
    location: str
    status: str
    value: float
    unit: str
    last_updated: datetime
    brightness: int | None = None
    is_on: bool | None = None


class DevicesResponse(BaseModel):
    total: int
    devices: list[DeviceRecord]


class TelemetryResponse(BaseModel):
    message: str
    device_id: str
    processed_by: str

class TelemetryRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    device_id: str
    device_type: str
    location: str
    value: float
    unit: str
    status: str
    timestamp: datetime
    received_at: datetime
