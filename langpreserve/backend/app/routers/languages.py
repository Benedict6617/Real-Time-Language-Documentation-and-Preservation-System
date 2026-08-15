from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.language import Language, Orthography, PhonemeInventoryEntry
from app.models.user import User, UserRole
from app.schemas.language import (
    LanguageCreate,
    LanguageRead,
    LanguageUpdate,
    OrthographyCreate,
    OrthographyRead,
    PhonemeEntryRead,
)
from app.utils.deps import get_current_user, require_roles

router = APIRouter(prefix="/api/v1/languages", tags=["languages"])


@router.get("", response_model=list[LanguageRead])
async def list_languages(db: AsyncSession = Depends(get_db)) -> list[Language]:
    result = await db.execute(select(Language).order_by(Language.name))
    return list(result.scalars().all())


@router.post(
    "",
    response_model=LanguageRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.LINGUIST))],
)
async def create_language(payload: LanguageCreate, db: AsyncSession = Depends(get_db)) -> Language:
    language = Language(**payload.model_dump())
    db.add(language)
    await db.commit()
    await db.refresh(language)
    return language


@router.get("/{language_id}", response_model=LanguageRead)
async def get_language(language_id: UUID, db: AsyncSession = Depends(get_db)) -> Language:
    language = await db.get(Language, language_id)
    if not language:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Language not found.")
    return language


@router.patch(
    "/{language_id}",
    response_model=LanguageRead,
    dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.LINGUIST))],
)
async def update_language(
    language_id: UUID, payload: LanguageUpdate, db: AsyncSession = Depends(get_db)
) -> Language:
    language = await db.get(Language, language_id)
    if not language:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Language not found.")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(language, field, value)
    await db.commit()
    await db.refresh(language)
    return language


@router.get("/{language_id}/orthographies", response_model=list[OrthographyRead])
async def list_orthographies(
    language_id: UUID, db: AsyncSession = Depends(get_db)
) -> list[Orthography]:
    result = await db.execute(
        select(Orthography).where(Orthography.language_id == language_id)
    )
    return list(result.scalars().all())


@router.post(
    "/{language_id}/orthographies",
    response_model=OrthographyRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.LINGUIST))],
)
async def create_orthography(
    language_id: UUID, payload: OrthographyCreate, db: AsyncSession = Depends(get_db)
) -> Orthography:
    if payload.language_id != language_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "language_id mismatch.")
    orthography = Orthography(**payload.model_dump())
    db.add(orthography)
    await db.commit()
    await db.refresh(orthography)
    return orthography


@router.get("/{language_id}/phonemes", response_model=list[PhonemeEntryRead])
async def list_phoneme_inventory(
    language_id: UUID, db: AsyncSession = Depends(get_db)
) -> list[PhonemeInventoryEntry]:
    result = await db.execute(
        select(PhonemeInventoryEntry)
        .where(PhonemeInventoryEntry.language_id == language_id)
        .order_by(PhonemeInventoryEntry.frequency_rank)
    )
    return list(result.scalars().all())
