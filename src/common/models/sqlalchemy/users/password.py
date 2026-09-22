"""Modèles SQLAlchemy pour la gestion des mots de passe des utilisateurs."""

from typing import TYPE_CHECKING
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import Integer, String, Boolean, DateTime, ForeignKey, UUID as PG_UUID
from sqlalchemy.orm import mapped_column, Mapped, relationship

from common.config.db import BaseUsers, CASCADE_OPTION
from common.models.sqlalchemy.common import UserMixin

if TYPE_CHECKING:
    from common.models.sqlalchemy.users.user import Users

class UsersPassword(UserMixin, BaseUsers):
    """
    Modèle représentant le mot de passe d'un utilisateur dans la base de données des utilisateurs.
    """
    __tablename__ = "users_password"
    __table_args__ = {"schema": "auth_schema"}

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="Identifiant unique du mot de passe"
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("auth_schema.users.id", ondelete=CASCADE_OPTION),
        nullable=False,
        comment="Identifiant de l'utilisateur associé"
    )
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Hash du mot de passe de l'utilisateur"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Indique si le mot de passe est actif"
    )
    change_needed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Indique si le mot de passe doit être changé"
    )
    from_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now(timezone.utc),
        nullable=False,
        comment="Date de début de validité du mot de passe"
    )
    to_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Date de fin de validité du mot de passe"
    )

    user: Mapped["Users"] = relationship(
        "Users",
        back_populates="passwords",
        cascade=CASCADE_OPTION,
        passive_deletes=True
    )
