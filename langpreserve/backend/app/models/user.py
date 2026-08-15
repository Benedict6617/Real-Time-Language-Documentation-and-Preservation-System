import enum
import uuid

from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDPKMixin


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    LINGUIST = "linguist"
    COMMUNITY_ANNOTATOR = "community_annotator"
    VIEWER = "viewer"


class User(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255))
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role"), default=UserRole.VIEWER
    )
    is_active: Mapped[bool] = mapped_column(default=True)
    primary_community_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("communities.id"), nullable=True
    )

    primary_community: Mapped["Community | None"] = relationship(
        back_populates="members"
    )


class Community(UUIDPKMixin, TimestampMixin, Base):
    """A speaker community associated with one or more documented languages."""

    __tablename__ = "communities"

    name: Mapped[str] = mapped_column(String(255))
    region: Mapped[str | None] = mapped_column(String(255), nullable=True)
    country: Mapped[str | None] = mapped_column(String(120), nullable=True)
    contact_notes: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    data_sovereignty_agreement: Mapped[str | None] = mapped_column(
        String(2000),
        nullable=True,
        doc="Summary of the consent / data-ownership agreement with this community.",
    )

    members: Mapped[list["User"]] = relationship(back_populates="primary_community")
