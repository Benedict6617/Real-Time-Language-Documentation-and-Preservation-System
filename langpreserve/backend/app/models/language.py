import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDPKMixin


class Language(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "languages"

    name: Mapped[str] = mapped_column(String(255), index=True)
    glottocode: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    iso_639_3: Mapped[str | None] = mapped_column(String(3), nullable=True, index=True)
    endangerment_status: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        doc="EGIDS-style status, e.g. 'Threatened', 'Shifting', 'Moribund'.",
    )
    estimated_speakers: Mapped[int | None] = mapped_column(nullable=True)
    region: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    community_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("communities.id"), nullable=True
    )

    orthographies: Mapped[list["Orthography"]] = relationship(
        back_populates="language", cascade="all, delete-orphan"
    )
    phoneme_inventory: Mapped[list["PhonemeInventoryEntry"]] = relationship(
        back_populates="language", cascade="all, delete-orphan"
    )


class Orthography(UUIDPKMixin, TimestampMixin, Base):
    """One writing system a language is documented in (IPA, community, colonial, etc.)."""

    __tablename__ = "orthographies"

    language_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("languages.id"))
    name: Mapped[str] = mapped_column(String(120))
    kind: Mapped[str] = mapped_column(
        String(30),
        doc="One of: ipa, practical_community, reference_majority, historical",
    )
    is_default: Mapped[bool] = mapped_column(default=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    language: Mapped["Language"] = relationship(back_populates="orthographies")


class PhonemeInventoryEntry(UUIDPKMixin, TimestampMixin, Base):
    """A single phoneme in a language's inventory, with cross-orthography spellings."""

    __tablename__ = "phoneme_inventory_entries"

    language_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("languages.id"))
    ipa_symbol: Mapped[str] = mapped_column(String(10))
    phoneme_type: Mapped[str] = mapped_column(
        String(20), doc="consonant | vowel | tone | suprasegmental"
    )
    manner: Mapped[str | None] = mapped_column(String(50), nullable=True)
    place: Mapped[str | None] = mapped_column(String(50), nullable=True)
    voicing: Mapped[str | None] = mapped_column(String(20), nullable=True)
    example_word: Mapped[str | None] = mapped_column(String(255), nullable=True)
    community_spelling: Mapped[str | None] = mapped_column(String(20), nullable=True)
    frequency_rank: Mapped[int | None] = mapped_column(nullable=True)
    detected_automatically: Mapped[bool] = mapped_column(default=False)

    language: Mapped["Language"] = relationship(back_populates="phoneme_inventory")
