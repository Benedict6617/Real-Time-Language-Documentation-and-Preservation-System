from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import ORMBase, TimestampedSchema


class LanguageCreate(BaseModel):
    name: str = Field(..., max_length=255)
    glottocode: str | None = Field(default=None, max_length=20)
    iso_639_3: str | None = Field(default=None, max_length=3)
    endangerment_status: str | None = None
    estimated_speakers: int | None = None
    region: str | None = None
    notes: str | None = None
    community_id: UUID | None = None


class LanguageUpdate(BaseModel):
    name: str | None = None
    endangerment_status: str | None = None
    estimated_speakers: int | None = None
    region: str | None = None
    notes: str | None = None


class LanguageRead(TimestampedSchema):
    name: str
    glottocode: str | None
    iso_639_3: str | None
    endangerment_status: str | None
    estimated_speakers: int | None
    region: str | None
    notes: str | None
    community_id: UUID | None


class OrthographyCreate(BaseModel):
    language_id: UUID
    name: str
    kind: str = Field(..., pattern="^(ipa|practical_community|reference_majority|historical)$")
    is_default: bool = False
    description: str | None = None


class OrthographyRead(TimestampedSchema):
    language_id: UUID
    name: str
    kind: str
    is_default: bool
    description: str | None


class PhonemeEntryCreate(BaseModel):
    language_id: UUID
    ipa_symbol: str = Field(..., max_length=10)
    phoneme_type: str = Field(..., pattern="^(consonant|vowel|tone|suprasegmental)$")
    manner: str | None = None
    place: str | None = None
    voicing: str | None = None
    example_word: str | None = None
    community_spelling: str | None = None
    frequency_rank: int | None = None
    detected_automatically: bool = False


class PhonemeEntryRead(ORMBase):
    id: UUID
    language_id: UUID
    ipa_symbol: str
    phoneme_type: str
    manner: str | None
    place: str | None
    voicing: str | None
    example_word: str | None
    community_spelling: str | None
    frequency_rank: int | None
    detected_automatically: bool
