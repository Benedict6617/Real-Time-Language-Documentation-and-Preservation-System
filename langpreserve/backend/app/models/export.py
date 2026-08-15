import enum
import uuid

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import TimestampMixin, UUIDPKMixin


class ExportFormat(str, enum.Enum):
    ELAN_EAF = "elan_eaf"
    IMDI_METADATA = "imdi_metadata"
    CMDI_METADATA = "cmdi_metadata"
    ELAR_PACKAGE = "elar_package"
    PRAAT_TEXTGRID = "praat_textgrid"
    LATEX_IGT = "latex_igt"
    CSV_LEXICON = "csv_lexicon"


class ExportStatus(str, enum.Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"


class ArchiveExportJob(UUIDPKMixin, TimestampMixin, Base):
    """Tracks an export/packaging job for archival deposit or academic publication."""

    __tablename__ = "archive_export_jobs"

    language_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("languages.id"))
    requested_by_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    export_format: Mapped[ExportFormat] = mapped_column(Enum(ExportFormat, name="export_format"))
    status: Mapped[ExportStatus] = mapped_column(
        Enum(ExportStatus, name="export_status"), default=ExportStatus.QUEUED
    )
    target_archive: Mapped[str | None] = mapped_column(
        String(80), nullable=True, doc="e.g. 'ELAR', 'PARADISEC', 'local'"
    )
    output_storage_key: Mapped[str | None] = mapped_column(String(500), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
