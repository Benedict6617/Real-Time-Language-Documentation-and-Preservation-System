import enum
import uuid

from sqlalchemy import Enum, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDPKMixin


class RecordingStatus(str, enum.Enum):
    UPLOADED = "uploaded"
    QUEUED_FOR_ASR = "queued_for_asr"
    TRANSCRIBING = "transcribing"
    DRAFT_READY = "draft_ready"
    UNDER_REVIEW = "under_review"
    COMMUNITY_APPROVED = "community_approved"
    ARCHIVED = "archived"


class ConsentStatus(str, enum.Enum):
    PENDING = "pending"
    GRANTED = "granted"
    RESTRICTED = "restricted"
    WITHDRAWN = "withdrawn"


class Speaker(UUIDPKMixin, TimestampMixin, Base):
    """A speaker/consultant, stored with minimal PII by design.

    Field teams should store only what is needed for archival attribution and
    what the speaker has consented to share; see docs/CONTRIBUTING.md.
    """

    __tablename__ = "speakers"

    display_name: Mapped[str] = mapped_column(String(255))
    community_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("communities.id"), nullable=True
    )
    birth_decade: Mapped[str | None] = mapped_column(
        String(10), nullable=True, doc="e.g. '1950s' — avoids storing exact DOB."
    )
    dialect_notes: Mapped[str | None] = mapped_column(String(500), nullable=True)
    consent_status: Mapped[ConsentStatus] = mapped_column(
        Enum(ConsentStatus, name="consent_status"), default=ConsentStatus.PENDING
    )


class Recording(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "recordings"

    language_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("languages.id"))
    speaker_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("speakers.id"), nullable=True
    )
    recorded_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )

    title: Mapped[str] = mapped_column(String(255))
    genre: Mapped[str | None] = mapped_column(
        String(80), nullable=True, doc="narrative, elicitation, conversation, song, ritual..."
    )
    location_description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    recorded_at_field_date: Mapped[str | None] = mapped_column(String(20), nullable=True)
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)

    storage_key: Mapped[str] = mapped_column(
        String(500), doc="Object storage key/path for the primary audio file."
    )
    sample_rate_hz: Mapped[int | None] = mapped_column(nullable=True)
    file_format: Mapped[str | None] = mapped_column(String(10), nullable=True)
    checksum_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)

    status: Mapped[RecordingStatus] = mapped_column(
        Enum(RecordingStatus, name="recording_status"), default=RecordingStatus.UPLOADED
    )
    consent_status: Mapped[ConsentStatus] = mapped_column(
        Enum(ConsentStatus, name="recording_consent_status"), default=ConsentStatus.PENDING
    )
    field_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    captured_offline: Mapped[bool] = mapped_column(
        default=False, doc="True if captured via the offline mobile app and later synced."
    )

    language: Mapped["Language"] = relationship()
    speaker: Mapped["Speaker | None"] = relationship()
    transcriptions: Mapped[list["Transcription"]] = relationship(
        back_populates="recording", cascade="all, delete-orphan"
    )
