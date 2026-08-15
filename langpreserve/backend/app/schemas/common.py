"""Shared base schemas and response envelopes."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ORMBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class TimestampedSchema(ORMBase):
    id: UUID
    created_at: datetime
    updated_at: datetime


class Message(BaseModel):
    detail: str


class PaginatedResponse(BaseModel):
    total: int
    limit: int
    offset: int
