from datetime import datetime

from pydantic import BaseModel, Field


class RequestLogCreate(BaseModel):
    request_id: str = Field(min_length=1, max_length=100)
    service: str = Field(min_length=1, max_length=100)
    path: str = Field(min_length=1, max_length=500)
    method: str = Field(min_length=1, max_length=10)
    client_ip: str = Field(min_length=1, max_length=100)
    status_code: int = Field(ge=100, le=599)
    processing_ms: float = Field(ge=0)
    error: str | None = None


class MessageLogCreate(BaseModel):
    service: str = Field(min_length=1, max_length=100)
    queue: str = Field(min_length=1, max_length=200)
    event_id: str | None = Field(default=None, max_length=200)
    outcome: str = Field(min_length=1, max_length=30)
    error: str | None = None


class RequestLogResponse(RequestLogCreate):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class MessageLogResponse(MessageLogCreate):
    id: int
    processed_at: datetime

    model_config = {"from_attributes": True}
