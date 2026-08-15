from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.language import Language, PhonemeInventoryEntry
from app.models.linguistics import Transcription
from app.models.recording import Recording
from app.schemas.language import PhonemeEntryRead
from app.services.phoneme_service import extract_phoneme_inventory

router = APIRouter(prefix="/api/v1/languages", tags=["phonemes"])


@router.post(
    "/{language_id}/phonemes/auto-detect",
    response_model=list[PhonemeEntryRead],
    status_code=status.HTTP_201_CREATED,
)
async def auto_detect_phoneme_inventory(
    language_id: UUID, db: AsyncSession = Depends(get_db)
) -> list[PhonemeInventoryEntry]:
    """Derive a candidate phoneme inventory from all transcriptions on record
    for this language. Existing auto-detected entries are replaced; manually
    curated entries (detected_automatically=False) are left untouched.
    """
    language = await db.get(Language, language_id)
    if not language:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Language not found.")

    result = await db.execute(
        select(Transcription.text)
        .join(Recording, Recording.id == Transcription.recording_id)
        .where(Recording.language_id == language_id)
    )
    transcripts = [row[0] for row in result.all()]
    if not transcripts:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "No transcriptions available yet for this language — record and "
            "transcribe some audio first.",
        )

    existing = await db.execute(
        select(PhonemeInventoryEntry).where(
            PhonemeInventoryEntry.language_id == language_id,
            PhonemeInventoryEntry.detected_automatically.is_(True),
        )
    )
    for entry in existing.scalars().all():
        await db.delete(entry)

    extracted = extract_phoneme_inventory(transcripts)
    created: list[PhonemeInventoryEntry] = []
    for item in extracted:
        entry = PhonemeInventoryEntry(
            language_id=language_id,
            ipa_symbol=item.ipa_symbol,
            phoneme_type=item.phoneme_type,
            manner=item.manner,
            place=item.place,
            voicing=item.voicing,
            example_word=item.example_word,
            frequency_rank=item.frequency_rank,
            detected_automatically=True,
        )
        db.add(entry)
        created.append(entry)

    await db.commit()
    for entry in created:
        await db.refresh(entry)
    return created
