from uuid import UUID

from pydantic import BaseModel, Field

from app.models.linguistics import AnnotationType, TranscriptionSource
from app.schemas.common import ORMBase, TimestampedSchema


class TranscriptionSegmentRead(ORMBase):
    id: UUID
    start_ms: int
    end_ms: int
    text: str
    confidence: float | None


class TranscriptionRequest(BaseModel):
    """Trigger ASR transcription for a recording."""

    orthography_id: UUID | None = None
    language_hint_iso: str | None = Field(
        default=None, description="ISO 639-3 hint to help select/condition the ASR model."
    )


class TranscriptionCreate(BaseModel):
    recording_id: UUID
    orthography_id: UUID | None = None
    text: str
    source: TranscriptionSource = TranscriptionSource.HUMAN_CORRECTED


class TranscriptionUpdate(BaseModel):
    text: str | None = None
    is_final: bool | None = None


class TranscriptionRead(TimestampedSchema):
    recording_id: UUID
    orthography_id: UUID | None
    text: str
    source: TranscriptionSource
    asr_model_version: str | None
    confidence: float | None
    is_final: bool
    segments: list[TranscriptionSegmentRead] = []


class InterlinearGlossCreate(BaseModel):
    transcription_id: UUID
    line_number: int
    surface_form: str
    morpheme_breakdown: str
    gloss_line: str
    free_translation: str
    pos_tags: str | None = None


class InterlinearGlossRead(ORMBase):
    id: UUID
    transcription_id: UUID
    line_number: int
    surface_form: str
    morpheme_breakdown: str
    gloss_line: str
    free_translation: str
    pos_tags: str | None
    generated_automatically: bool


class GrammarAnalysisRequest(BaseModel):
    """Trigger automatic morpheme segmentation + gloss generation for a transcription."""

    transcription_id: UUID


class AnnotationCreate(BaseModel):
    transcription_id: UUID | None = None
    igt_line_id: UUID | None = None
    annotation_type: AnnotationType
    body: str


class AnnotationRead(TimestampedSchema):
    transcription_id: UUID | None
    igt_line_id: UUID | None
    author_user_id: UUID
    annotation_type: AnnotationType
    body: str
    upvotes: int
    resolved: bool
