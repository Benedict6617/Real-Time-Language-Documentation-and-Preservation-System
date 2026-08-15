from uuid import UUID

from pydantic import BaseModel

from app.models.export import ExportFormat, ExportStatus
from app.schemas.common import TimestampedSchema


class ExportJobCreate(BaseModel):
    language_id: UUID
    export_format: ExportFormat
    target_archive: str | None = None


class ExportJobRead(TimestampedSchema):
    language_id: UUID
    requested_by_user_id: UUID
    export_format: ExportFormat
    status: ExportStatus
    target_archive: str | None
    output_storage_key: str | None
    error_message: str | None


class LearningMaterialGenerateRequest(BaseModel):
    language_id: UUID
    material_type: str
    source_recording_ids: list[UUID] = []


class LearningMaterialRead(TimestampedSchema):
    language_id: UUID
    material_type: str
    title: str
    content_json: str
    generated_automatically: bool


class TTSSynthesizeRequest(BaseModel):
    language_id: UUID
    text: str
    orthography_id: UUID | None = None
    voice_profile: str | None = None
