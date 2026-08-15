from uuid import UUID

from pydantic import BaseModel, Field

from app.models.recording import ConsentStatus, RecordingStatus
from app.schemas.common import TimestampedSchema


class SpeakerCreate(BaseModel):
    display_name: str = Field(..., max_length=255)
    community_id: UUID | None = None
    birth_decade: str | None = None
    dialect_notes: str | None = None
    consent_status: ConsentStatus = ConsentStatus.PENDING


class SpeakerRead(TimestampedSchema):
    display_name: str
    community_id: UUID | None
    birth_decade: str | None
    dialect_notes: str | None
    consent_status: ConsentStatus


class RecordingCreate(BaseModel):
    language_id: UUID
    speaker_id: UUID | None = None
    title: str = Field(..., max_length=255)
    genre: str | None = None
    location_description: str | None = None
    recorded_at_field_date: str | None = None
    duration_seconds: float | None = None
    sample_rate_hz: int | None = None
    file_format: str | None = None
    field_notes: str | None = None
    captured_offline: bool = False
    consent_status: ConsentStatus = ConsentStatus.PENDING


class RecordingRead(TimestampedSchema):
    language_id: UUID
    speaker_id: UUID | None
    title: str
    genre: str | None
    location_description: str | None
    recorded_at_field_date: str | None
    duration_seconds: float | None
    storage_key: str
    sample_rate_hz: int | None
    file_format: str | None
    status: RecordingStatus
    consent_status: ConsentStatus
    field_notes: str | None
    captured_offline: bool


class RecordingStatusUpdate(BaseModel):
    status: RecordingStatus


class OfflineSyncBatch(BaseModel):
    """Payload shape sent by the mobile app when reconnecting after fieldwork."""

    device_id: str
    recordings: list[RecordingCreate]
    client_recorded_local_ids: list[str] = Field(
        default_factory=list,
        description="Local (device-generated) IDs, returned mapped to server UUIDs.",
    )
