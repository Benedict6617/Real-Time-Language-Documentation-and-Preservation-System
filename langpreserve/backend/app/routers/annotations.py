from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.linguistics import Annotation
from app.models.user import User
from app.schemas.transcription import AnnotationCreate, AnnotationRead
from app.utils.deps import get_current_user

router = APIRouter(prefix="/api/v1/annotations", tags=["annotations"])


@router.get("", response_model=list[AnnotationRead])
async def list_annotations(
    transcription_id: UUID | None = None,
    resolved: bool | None = None,
    db: AsyncSession = Depends(get_db),
) -> list[Annotation]:
    query = select(Annotation)
    if transcription_id:
        query = query.where(Annotation.transcription_id == transcription_id)
    if resolved is not None:
        query = query.where(Annotation.resolved == resolved)
    result = await db.execute(query.order_by(Annotation.created_at.desc()))
    return list(result.scalars().all())


@router.post("", response_model=AnnotationRead, status_code=status.HTTP_201_CREATED)
async def create_annotation(
    payload: AnnotationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Annotation:
    if not payload.transcription_id and not payload.igt_line_id:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Annotation must reference a transcription_id or igt_line_id.",
        )
    annotation = Annotation(**payload.model_dump(), author_user_id=current_user.id)
    db.add(annotation)
    await db.commit()
    await db.refresh(annotation)
    return annotation


@router.post("/{annotation_id}/upvote", response_model=AnnotationRead)
async def upvote_annotation(annotation_id: UUID, db: AsyncSession = Depends(get_db)) -> Annotation:
    annotation = await db.get(Annotation, annotation_id)
    if not annotation:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Annotation not found.")
    annotation.upvotes += 1
    await db.commit()
    await db.refresh(annotation)
    return annotation


@router.post("/{annotation_id}/resolve", response_model=AnnotationRead)
async def resolve_annotation(annotation_id: UUID, db: AsyncSession = Depends(get_db)) -> Annotation:
    annotation = await db.get(Annotation, annotation_id)
    if not annotation:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Annotation not found.")
    annotation.resolved = True
    await db.commit()
    await db.refresh(annotation)
    return annotation
