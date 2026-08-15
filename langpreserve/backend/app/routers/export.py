from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.export import ArchiveExportJob, ExportFormat, ExportStatus
from app.models.language import Language
from app.models.linguistics import InterlinearGloss, Transcription
from app.models.recording import Recording
from app.models.user import User
from app.schemas.export import ExportJobCreate, ExportJobRead
from app.services.export_service import (
    ExportIGTLine,
    ExportRecordingBundle,
    ExportSegment,
    generate_csv_lexicon,
    generate_elan_eaf,
    generate_latex_igt,
)
from app.utils.deps import get_current_user

router = APIRouter(prefix="/api/v1/export", tags=["export"])


@router.post("/jobs", response_model=ExportJobRead, status_code=status.HTTP_201_CREATED)
async def create_export_job(
    payload: ExportJobCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ArchiveExportJob:
    language = await db.get(Language, payload.language_id)
    if not language:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Language not found.")

    job = ArchiveExportJob(
        language_id=payload.language_id,
        requested_by_user_id=current_user.id,
        export_format=payload.export_format,
        target_archive=payload.target_archive,
        status=ExportStatus.QUEUED,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job


@router.get("/jobs/{job_id}", response_model=ExportJobRead)
async def get_export_job(job_id: UUID, db: AsyncSession = Depends(get_db)) -> ArchiveExportJob:
    job = await db.get(ArchiveExportJob, job_id)
    if not job:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Export job not found.")
    return job


@router.get("/recordings/{recording_id}/eaf")
async def export_recording_as_eaf(
    recording_id: UUID, db: AsyncSession = Depends(get_db)
) -> Response:
    """Synchronous, on-demand ELAN (.eaf) export for a single recording —
    convenient for quick checks; bulk/archive-scale exports should use the
    async `/export/jobs` queue instead.
    """
    result = await db.execute(
        select(Recording)
        .options(selectinload(Recording.transcriptions).selectinload(Transcription.segments))
        .where(Recording.id == recording_id)
    )
    recording = result.scalar_one_or_none()
    if not recording:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Recording not found.")

    language = await db.get(Language, recording.language_id)
    transcription = next(iter(recording.transcriptions), None)
    segments = (
        [ExportSegment(s.start_ms, s.end_ms, s.text) for s in transcription.segments]
        if transcription
        else []
    )

    igt_lines: list[ExportIGTLine] = []
    if transcription:
        igt_result = await db.execute(
            select(InterlinearGloss).where(InterlinearGloss.transcription_id == transcription.id)
        )
        igt_lines = [
            ExportIGTLine(i.surface_form, i.morpheme_breakdown, i.gloss_line, i.free_translation)
            for i in igt_result.scalars().all()
        ]

    bundle = ExportRecordingBundle(
        recording_title=recording.title,
        language_name=language.name if language else "unknown",
        speaker_display_name=None,
        media_filename=f"{recording.id}.{recording.file_format or 'wav'}",
        segments=segments,
        igt_lines=igt_lines,
    )
    eaf_xml = generate_elan_eaf(bundle)
    return Response(
        content=eaf_xml,
        media_type="application/xml",
        headers={"Content-Disposition": f'attachment; filename="{recording.id}.eaf"'},
    )


@router.get("/languages/{language_id}/lexicon.csv")
async def export_language_lexicon_csv(
    language_id: UUID, db: AsyncSession = Depends(get_db)
) -> Response:
    from app.models.language import PhonemeInventoryEntry  # local import avoids cycle

    result = await db.execute(
        select(PhonemeInventoryEntry).where(PhonemeInventoryEntry.language_id == language_id)
    )
    entries = [
        {
            "ipa": e.ipa_symbol,
            "community_spelling": e.community_spelling or "",
            "gloss": "",
            "example_sentence": e.example_word or "",
        }
        for e in result.scalars().all()
    ]
    csv_text = generate_csv_lexicon(entries)
    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{language_id}-lexicon.csv"'},
    )


@router.get("/transcriptions/{transcription_id}/latex")
async def export_transcription_as_latex(
    transcription_id: UUID, db: AsyncSession = Depends(get_db)
) -> Response:
    result = await db.execute(
        select(InterlinearGloss)
        .where(InterlinearGloss.transcription_id == transcription_id)
        .order_by(InterlinearGloss.line_number)
    )
    igt_lines = [
        ExportIGTLine(i.surface_form, i.morpheme_breakdown, i.gloss_line, i.free_translation)
        for i in result.scalars().all()
    ]
    if not igt_lines:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No IGT lines found for this transcription.")

    latex = generate_latex_igt(igt_lines)
    return Response(
        content=latex,
        media_type="text/plain",
        headers={"Content-Disposition": f'attachment; filename="{transcription_id}.tex"'},
    )
