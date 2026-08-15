"""ORM model registry — import all modules here so Base.metadata sees every table."""
from app.models.export import ArchiveExportJob, ExportFormat, ExportStatus  # noqa: F401
from app.models.language import Language, Orthography, PhonemeInventoryEntry  # noqa: F401
from app.models.linguistics import (  # noqa: F401
    Annotation,
    AnnotationType,
    InterlinearGloss,
    LearningMaterial,
    Transcription,
    TranscriptionSegment,
    TranscriptionSource,
)
from app.models.recording import (  # noqa: F401
    ConsentStatus,
    Recording,
    RecordingStatus,
    Speaker,
)
from app.models.user import Community, User, UserRole  # noqa: F401

__all__ = [
    "ArchiveExportJob",
    "ExportFormat",
    "ExportStatus",
    "Language",
    "Orthography",
    "PhonemeInventoryEntry",
    "Annotation",
    "AnnotationType",
    "InterlinearGloss",
    "LearningMaterial",
    "Transcription",
    "TranscriptionSegment",
    "TranscriptionSource",
    "ConsentStatus",
    "Recording",
    "RecordingStatus",
    "Speaker",
    "Community",
    "User",
    "UserRole",
]
