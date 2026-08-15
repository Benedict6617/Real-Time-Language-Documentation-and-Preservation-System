import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.language import Language, PhonemeInventoryEntry
from app.models.linguistics import InterlinearGloss, LearningMaterial, Transcription
from app.models.recording import Recording
from app.schemas.export import (
    LearningMaterialGenerateRequest,
    LearningMaterialRead,
    TTSSynthesizeRequest,
)
from app.services.tts_service import TTSServiceError, get_tts_provider

router = APIRouter(prefix="/api/v1", tags=["learning-materials"])


@router.post(
    "/learning-materials/generate",
    response_model=LearningMaterialRead,
    status_code=status.HTTP_201_CREATED,
)
async def generate_learning_material(
    payload: LearningMaterialGenerateRequest, db: AsyncSession = Depends(get_db)
) -> LearningMaterial:
    language = await db.get(Language, payload.language_id)
    if not language:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Language not found.")

    if payload.material_type == "flashcard_deck":
        content = await _build_flashcard_deck(db, payload.language_id)
        title = f"{language.name} Flashcards — auto-generated"
    elif payload.material_type == "minimal_pairs":
        content = await _build_minimal_pairs(db, payload.language_id)
        title = f"{language.name} Minimal Pairs — auto-generated"
    elif payload.material_type == "phrasebook":
        content = await _build_phrasebook(db, payload.language_id, payload.source_recording_ids)
        title = f"{language.name} Phrasebook — auto-generated"
    else:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Unknown material_type: {payload.material_type}")

    material = LearningMaterial(
        language_id=payload.language_id,
        material_type=payload.material_type,
        title=title,
        content_json=json.dumps(content),
        source_recording_ids=json.dumps([str(i) for i in payload.source_recording_ids]),
        generated_automatically=True,
    )
    db.add(material)
    await db.commit()
    await db.refresh(material)
    return material


@router.get("/languages/{language_id}/learning-materials", response_model=list[LearningMaterialRead])
async def list_learning_materials(
    language_id: UUID, db: AsyncSession = Depends(get_db)
) -> list[LearningMaterial]:
    result = await db.execute(
        select(LearningMaterial).where(LearningMaterial.language_id == language_id)
    )
    return list(result.scalars().all())


async def _build_flashcard_deck(db: AsyncSession, language_id: UUID) -> dict:
    result = await db.execute(
        select(PhonemeInventoryEntry)
        .where(PhonemeInventoryEntry.language_id == language_id)
        .where(PhonemeInventoryEntry.example_word.is_not(None))
    )
    cards = [
        {"front": e.example_word, "back": e.ipa_symbol, "note": e.phoneme_type}
        for e in result.scalars().all()
    ]
    return {"cards": cards}


async def _build_minimal_pairs(db: AsyncSession, language_id: UUID) -> dict:
    result = await db.execute(
        select(PhonemeInventoryEntry)
        .where(PhonemeInventoryEntry.language_id == language_id)
        .where(PhonemeInventoryEntry.phoneme_type.in_(["consonant", "vowel"]))
        .order_by(PhonemeInventoryEntry.frequency_rank)
    )
    entries = list(result.scalars().all())
    pairs = []
    for a, b in zip(entries, entries[1:]):
        if a.phoneme_type == b.phoneme_type and a.example_word and b.example_word:
            pairs.append({"pair": [a.ipa_symbol, b.ipa_symbol], "examples": [a.example_word, b.example_word]})
    return {"minimal_pairs": pairs}


async def _build_phrasebook(
    db: AsyncSession, language_id: UUID, source_recording_ids: list[UUID]
) -> dict:
    query = (
        select(InterlinearGloss)
        .join(Transcription, Transcription.id == InterlinearGloss.transcription_id)
        .join(Recording, Recording.id == Transcription.recording_id)
        .where(Recording.language_id == language_id)
    )
    if source_recording_ids:
        query = query.where(Recording.id.in_(source_recording_ids))
    result = await db.execute(query.limit(50))
    entries = [
        {"phrase": i.surface_form, "translation": i.free_translation, "gloss": i.gloss_line}
        for i in result.scalars().all()
    ]
    return {"entries": entries}


@router.post("/tts/synthesize")
async def synthesize_speech(payload: TTSSynthesizeRequest) -> Response:
    provider = get_tts_provider()
    try:
        result = await provider.synthesize(payload.text, voice_profile=payload.voice_profile)
    except TTSServiceError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(exc)) from exc

    return Response(
        content=result.audio_bytes,
        media_type=f"audio/{result.format}",
        headers={"X-TTS-Provider": result.provider, "X-Duration-Seconds": str(result.duration_seconds)},
    )
