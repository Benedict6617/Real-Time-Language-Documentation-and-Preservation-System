import hashlib
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.recording import Recording, RecordingStatus
from app.models.user import User
from app.schemas.recording import (
    OfflineSyncBatch,
    RecordingCreate,
    RecordingRead,
    RecordingStatusUpdate,
)
from app.services.storage_service import get_storage_service
from app.utils.deps import get_current_user

router = APIRouter(prefix="/api/v1/recordings", tags=["recordings"])


@router.get("", response_model=list[RecordingRead])
async def list_recordings(
    language_id: UUID | None = None, db: AsyncSession = Depends(get_db)
) -> list[Recording]:
    query = select(Recording)
    if language_id:
        query = query.where(Recording.language_id == language_id)
    result = await db.execute(query.order_by(Recording.created_at.desc()))
    return list(result.scalars().all())


@router.post("", response_model=RecordingRead, status_code=status.HTTP_201_CREATED)
async def upload_recording(
    metadata: RecordingCreate = Depends(),
    audio_file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Recording:
    """Upload a single field recording with its metadata (used by the web
    dashboard for direct uploads; the mobile app instead batches through
    `/recordings/sync`).
    """
    audio_bytes = await audio_file.read()
    if not audio_bytes:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Empty audio file.")

    storage = get_storage_service()
    extension = (audio_file.filename or "recording.wav").rsplit(".", 1)[-1]
    key = storage.build_key(
        language_id=str(metadata.language_id), kind="recordings", extension=extension
    )
    storage.put_object(key, audio_bytes, content_type=audio_file.content_type or "audio/wav")

    recording = Recording(
        **metadata.model_dump(),
        storage_key=key,
        checksum_sha256=hashlib.sha256(audio_bytes).hexdigest(),
        recorded_by_user_id=current_user.id,
        status=RecordingStatus.UPLOADED,
    )
    db.add(recording)
    await db.commit()
    await db.refresh(recording)
    return recording


@router.get("/{recording_id}", response_model=RecordingRead)
async def get_recording(recording_id: UUID, db: AsyncSession = Depends(get_db)) -> Recording:
    recording = await db.get(Recording, recording_id)
    if not recording:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Recording not found.")
    return recording


@router.patch("/{recording_id}/status", response_model=RecordingRead)
async def update_recording_status(
    recording_id: UUID, payload: RecordingStatusUpdate, db: AsyncSession = Depends(get_db)
) -> Recording:
    recording = await db.get(Recording, recording_id)
    if not recording:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Recording not found.")
    recording.status = payload.status
    await db.commit()
    await db.refresh(recording)
    return recording


@router.post("/sync", response_model=list[RecordingRead], status_code=status.HTTP_201_CREATED)
async def sync_offline_batch(
    batch: OfflineSyncBatch,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Recording]:
    """Reconcile a batch of recordings captured offline by the mobile field app.

    Audio bytes for offline-captured recordings are expected to have already
    been uploaded to a staging storage key by the mobile client (see
    `mobile/src/services/offlineSync.js`); this endpoint reconciles metadata
    only, so it stays fast even over a poor connection.
    """
    created: list[Recording] = []
    for item in batch.recordings:
        recording = Recording(
            **item.model_dump(),
            storage_key=f"pending-upload/{batch.device_id}",
            recorded_by_user_id=current_user.id,
            captured_offline=True,
            status=RecordingStatus.UPLOADED,
        )
        db.add(recording)
        created.append(recording)

    await db.commit()
    for recording in created:
        await db.refresh(recording)
    return created
