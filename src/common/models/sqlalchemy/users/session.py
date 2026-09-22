"""Modèles SQLAlchemy pour la base de données des sessions des utilisateurs."""

from typing import TYPE_CHECKING
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import Integer, String, DateTime, ForeignKey, UUID as PG_UUID
from sqlalchemy.orm import mapped_column, Mapped, relationship

from common.config.db import BaseUsers, CASCADE_OPTION
from common.models.sqlalchemy.common import UserMixin

if TYPE_CHECKING:
    from common.models.sqlalchemy.users.user import Users

class UserSession(UserMixin, BaseUsers):
    """
    Modèle représentant une session utilisateur dans la base de données des sessions des
    utilisateurs.
    """
    __tablename__ = "user_sessions"
    __table_args__ = {"schema": "auth_schema"}

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="Identifiant unique de la session utilisateur"
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("auth_schema.users.id", ondelete=CASCADE_OPTION),
        nullable=False,
        comment="Identifiant de l'utilisateur associé à la session"
    )
    token_hash: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        comment="Empreinte SHA-256 du jeton de session unique"
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="Date d'expiration absolue de la session"
    )
    last_accessed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now(timezone.utc),
        nullable=False,
        comment="Date du dernier accès à la session"
    )
    revoked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Date de révocation de la session"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now(timezone.utc),
        nullable=False,
        comment="Date de création de la session"
    )

    user: Mapped["Users"] = relationship(
        "Users",
        back_populates="sessions",
        cascade=CASCADE_OPTION,
        passive_deletes=True
    )

    @property
    def is_active(self) -> bool:
        """Indique si la session est active (non expirée et non révoquée)."""
        now = datetime.now(timezone.utc)
        return self.revoked_at is None and self.expires_at > now
