
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class CommandCreate(BaseModel):
    device_id: str = Field(min_length=1, max_length=100)
    command: str = Field(min_length=1, max_length=100)
    parameters: str | None = Field(default=None, max_length=1000)


class CommandResponse(BaseModel):
    id: UUID
    device_id: str
    command: str
    parameters: str | None
    status: str
    result: dict | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
