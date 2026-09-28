"""Secret TOTP chiffré et état de l'enrôlement utilisateur."""

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, Text, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from common.models.sqlalchemy.common import UserMixin

if TYPE_CHECKING:
    from .user import Users


class UserOTP(UserMixin):
    """Clé TOTP chiffrée, activée après validation d'un premier code."""

    __tablename__ = "user_otp"
    __table_args__ = {"schema": "auth_schema"}

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey(
            "auth_schema.users.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
        comment="Identifiant de l'utilisateur associé à l'enrôlement TOTP"
    )
    secret_encrypted: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Clé TOTP chiffrée de l'utilisateur"
    )
    enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Indique si l'enrôlement TOTP est activé pour l'utilisateur"
    )
    last_counter: Mapped[int | None] = mapped_column(
        nullable=True,
        comment="Dernier compteur utilisé pour la validation TOTP",
    )
    user: Mapped["Users"] = relationship(
        "Users",
        back_populates="otp",
    )
