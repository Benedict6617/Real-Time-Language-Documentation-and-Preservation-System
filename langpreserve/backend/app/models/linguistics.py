import enum
import uuid

from sqlalchemy import Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDPKMixin


class TranscriptionSource(str, enum.Enum):
    ASR_DRAFT = "asr_draft"
    HUMAN_CORRECTED = "human_corrected"
    COMMUNITY_VERIFIED = "community_verified"


class Transcription(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "transcriptions"

    recording_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("recordings.id"))
    orthography_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("orthographies.id"), nullable=True
    )

    text: Mapped[str] = mapped_column(Text)
    source: Mapped[TranscriptionSource] = mapped_column(
        Enum(TranscriptionSource, name="transcription_source"),
        default=TranscriptionSource.ASR_DRAFT,
    )
    asr_model_version: Mapped[str | None] = mapped_column(String(80), nullable=True)
    confidence: Mapped[float | None] = mapped_column(
        Float, nullable=True, doc="Mean ASR confidence, 0.0-1.0"
    )
    is_final: Mapped[bool] = mapped_column(default=False)

    recording: Mapped["Recording"] = relationship(back_populates="transcriptions")
    segments: Mapped[list["TranscriptionSegment"]] = relationship(
        back_populates="transcription", cascade="all, delete-orphan", order_by="TranscriptionSegment.start_ms"
    )
    igt_lines: Mapped[list["InterlinearGloss"]] = relationship(
        back_populates="transcription", cascade="all, delete-orphan"
    )


class TranscriptionSegment(UUIDPKMixin, Base):
    """Word/utterance-level timing alignment within a transcription."""

    __tablename__ = "transcription_segments"

    transcription_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("transcriptions.id"))
    start_ms: Mapped[int] = mapped_column(Integer)
    end_ms: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(String(500))
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    transcription: Mapped["Transcription"] = relationship(back_populates="segments")


class InterlinearGloss(UUIDPKMixin, Base):
    """A single IGT (interlinear glossed text) line: surface, morphemes, gloss, translation."""

    __tablename__ = "interlinear_glosses"

    transcription_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("transcriptions.id"))
    line_number: Mapped[int] = mapped_column(Integer)

    surface_form: Mapped[str] = mapped_column(String(500))
    morpheme_breakdown: Mapped[str] = mapped_column(
        String(500), doc="Hyphenated morphemes, e.g. 'a-tsʼúgé-le'"
    )
    gloss_line: Mapped[str] = mapped_column(
        String(500), doc="Leipzig-style gloss, e.g. '3SG-run-PST'"
    )
    free_translation: Mapped[str] = mapped_column(String(500))
    pos_tags: Mapped[str | None] = mapped_column(
        String(255), nullable=True, doc="Space-separated POS tags aligned to morphemes."
    )
    generated_automatically: Mapped[bool] = mapped_column(default=False)
    reviewed_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )

    transcription: Mapped["Transcription"] = relationship(back_populates="igt_lines")


class AnnotationType(str, enum.Enum):
    CORRECTION = "correction"
    CULTURAL_NOTE = "cultural_note"
    ALTERNATE_SPELLING = "alternate_spelling"
    TRANSLATION_SUGGESTION = "translation_suggestion"
    FLAG_FOR_REVIEW = "flag_for_review"


class Annotation(UUIDPKMixin, TimestampMixin, Base):
    """A community/linguist annotation attached to a transcription or IGT line."""

    __tablename__ = "annotations"

    transcription_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("transcriptions.id"), nullable=True
    )
    igt_line_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("interlinear_glosses.id"), nullable=True
    )
    author_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))

    annotation_type: Mapped[AnnotationType] = mapped_column(
        Enum(AnnotationType, name="annotation_type")
    )
    body: Mapped[str] = mapped_column(Text)
    upvotes: Mapped[int] = mapped_column(default=0)
    resolved: Mapped[bool] = mapped_column(default=False)


class LearningMaterial(UUIDPKMixin, TimestampMixin, Base):
    """Auto-generated or hand-curated revitalization material derived from recordings."""

    __tablename__ = "learning_materials"

    language_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("languages.id"))
    material_type: Mapped[str] = mapped_column(
        String(40), doc="flashcard_deck | minimal_pairs | phrasebook | audio_lesson"
    )
    title: Mapped[str] = mapped_column(String(255))
    content_json: Mapped[str] = mapped_column(
        Text, doc="JSON payload with the generated material content."
    )
    source_recording_ids: Mapped[str | None] = mapped_column(
        Text, nullable=True, doc="JSON list of source recording UUIDs used to generate this."
    )
    generated_automatically: Mapped[bool] = mapped_column(default=True)
