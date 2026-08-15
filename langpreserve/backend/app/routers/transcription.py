from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.linguistics import (
    InterlinearGloss,
    Transcription,
    TranscriptionSegment,
    TranscriptionSource,
)
from app.models.recording import Recording, RecordingStatus
from app.schemas.transcription import (
    GrammarAnalysisRequest,
    InterlinearGlossCreate,
    InterlinearGlossRead,
    TranscriptionCreate,
    TranscriptionRead,
    TranscriptionRequest,
    TranscriptionUpdate,
)
from app.services.asr_service import ASRServiceError, get_asr_provider
from app.services.grammar_analysis_service import generate_draft_igt
from app.services.storage_service import get_storage_service

router = APIRouter(prefix="/api/v1", tags=["transcription"])


@router.post(
    "/recordings/{recording_id}/transcribe",
    response_model=TranscriptionRead,
    status_code=status.HTTP_201_CREATED,
)
async def transcribe_recording(
    recording_id: UUID, payload: TranscriptionRequest, db: AsyncSession = Depends(get_db)
) -> Transcription:
    """Run the configured ASR provider against a recording and store a draft transcription."""
    recording = await db.get(Recording, recording_id)
    if not recording:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Recording not found.")

    storage = get_storage_service()
    try:
        audio_bytes = storage.get_object(recording.storage_key)
    except FileNotFoundError as exc:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Audio not yet available in storage (offline recording still syncing?).",
        ) from exc

    provider = get_asr_provider()
    try:
        result = await provider.transcribe(
            audio_bytes, language_hint_iso=payload.language_hint_iso
        )
    except ASRServiceError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(exc)) from exc

    transcription = Transcription(
        recording_id=recording.id,
        orthography_id=payload.orthography_id,
        text=result.text,
        source=TranscriptionSource.ASR_DRAFT,
        asr_model_version=result.model_version,
        confidence=result.mean_confidence,
        is_final=False,
    )
    db.add(transcription)
    await db.flush()

    for seg in result.segments:
        db.add(
            TranscriptionSegment(
                transcription_id=transcription.id,
                start_ms=seg.start_ms,
                end_ms=seg.end_ms,
                text=seg.text,
                confidence=seg.confidence,
            )
        )

    recording.status = (
        RecordingStatus.DRAFT_READY
        if result.mean_confidence >= 0.75
        else RecordingStatus.UNDER_REVIEW
    )

    await db.commit()

    result_query = await db.execute(
        select(Transcription)
        .options(selectinload(Transcription.segments))
        .where(Transcription.id == transcription.id)
    )
    return result_query.scalar_one()


@router.get("/transcriptions/{transcription_id}", response_model=TranscriptionRead)
async def get_transcription(
    transcription_id: UUID, db: AsyncSession = Depends(get_db)
) -> Transcription:
    result = await db.execute(
        select(Transcription)
        .options(selectinload(Transcription.segments))
        .where(Transcription.id == transcription_id)
    )
    transcription = result.scalar_one_or_none()
    if not transcription:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Transcription not found.")
    return transcription


@router.patch("/transcriptions/{transcription_id}", response_model=TranscriptionRead)
async def update_transcription(
    transcription_id: UUID, payload: TranscriptionUpdate, db: AsyncSession = Depends(get_db)
) -> Transcription:
    """Human/community correction of a draft transcription."""
    transcription = await db.get(Transcription, transcription_id)
    if not transcription:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Transcription not found.")

    if payload.text is not None:
        transcription.text = payload.text
        transcription.source = TranscriptionSource.HUMAN_CORRECTED
    if payload.is_final is not None:
        transcription.is_final = payload.is_final
        if payload.is_final:
            transcription.source = TranscriptionSource.COMMUNITY_VERIFIED

    await db.commit()
    await db.refresh(transcription)
    return transcription


@router.post(
    "/grammar/analyze",
    response_model=list[InterlinearGlossRead],
    status_code=status.HTTP_201_CREATED,
)
async def analyze_grammar(
    payload: GrammarAnalysisRequest, db: AsyncSession = Depends(get_db)
) -> list[InterlinearGloss]:
    """Generate draft interlinear glosses (IGT) for a transcription's segments."""
    result = await db.execute(
        select(Transcription)
        .options(selectinload(Transcription.segments))
        .where(Transcription.id == payload.transcription_id)
    )
    transcription = result.scalar_one_or_none()
    if not transcription:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Transcription not found.")

    lines_source = transcription.segments or [
        TranscriptionSegment(start_ms=0, end_ms=0, text=transcription.text)
    ]

    created: list[InterlinearGloss] = []
    for i, segment in enumerate(lines_source):
        draft = generate_draft_igt(segment.text)
        igt = InterlinearGloss(
            transcription_id=transcription.id,
            line_number=i,
            surface_form=draft.surface_form,
            morpheme_breakdown=draft.morpheme_breakdown,
            gloss_line=draft.gloss_line,
            free_translation=draft.free_translation,
            pos_tags=draft.pos_tags,
            generated_automatically=True,
        )
        db.add(igt)
        created.append(igt)

    await db.commit()
    for igt in created:
        await db.refresh(igt)
    return created


@router.post(
    "/grammar/igt",
    response_model=InterlinearGlossRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_manual_igt_line(
    payload: InterlinearGlossCreate, db: AsyncSession = Depends(get_db)
) -> InterlinearGloss:
    """Let a linguist add/override an IGT line by hand."""
    igt = InterlinearGloss(**payload.model_dump(), generated_automatically=False)
    db.add(igt)
    await db.commit()
    await db.refresh(igt)
    return igt


@router.get("/transcriptions/{transcription_id}/igt", response_model=list[InterlinearGlossRead])
async def list_igt_lines(
    transcription_id: UUID, db: AsyncSession = Depends(get_db)
) -> list[InterlinearGloss]:
    result = await db.execute(
        select(InterlinearGloss)
        .where(InterlinearGloss.transcription_id == transcription_id)
        .order_by(InterlinearGloss.line_number)
    )
    return list(result.scalars().all())
