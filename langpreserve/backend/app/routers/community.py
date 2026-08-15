from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.recording import Speaker
from app.models.user import Community
from app.schemas.recording import SpeakerCreate, SpeakerRead

router = APIRouter(prefix="/api/v1/community", tags=["community"])


@router.get("/communities")
async def list_communities(db: AsyncSession = Depends(get_db)) -> list[dict]:
    result = await db.execute(select(Community))
    return [
        {
            "id": str(c.id),
            "name": c.name,
            "region": c.region,
            "country": c.country,
        }
        for c in result.scalars().all()
    ]


@router.post("/speakers", response_model=SpeakerRead, status_code=status.HTTP_201_CREATED)
async def create_speaker(payload: SpeakerCreate, db: AsyncSession = Depends(get_db)) -> Speaker:
    speaker = Speaker(**payload.model_dump())
    db.add(speaker)
    await db.commit()
    await db.refresh(speaker)
    return speaker


@router.get("/speakers/{speaker_id}", response_model=SpeakerRead)
async def get_speaker(speaker_id: UUID, db: AsyncSession = Depends(get_db)) -> Speaker:
    speaker = await db.get(Speaker, speaker_id)
    if not speaker:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Speaker not found.")
    return speaker
