"""Modèles SQLAlchemy pour la base de données des utilisateurs."""

from typing import TYPE_CHECKING
from datetime import datetime, timezone
from uuid import uuid7, UUID
from sqlalchemy import Integer, String, Boolean, DateTime, UUID as PG_UUID
from sqlalchemy.orm import mapped_column, Mapped, relationship
from common.models.sqlalchemy.common import UserMixin
from common.config.db import BaseUsers, CASCADE_OPTION
if TYPE_CHECKING:
    from common.models.sqlalchemy.users.session import UserSession

class Users(UserMixin, BaseUsers):
    """
    Modèle représentant un utilisateur dans la base de données des utilisateurs.
    
    """
    __tablename__ = "users"
    __table_args__ = {"schema": "auth_schema"}

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid7,
        comment="Identifiant unique de l'utilisateur"
    )
    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        comment="Nom d'utilisateur unique"
    )
    email: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        comment="Adresse email unique de l'utilisateur"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Indique si l'utilisateur est actif"
    )
    nb_failed_logins: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Nombre de tentatives de connexion échouées"
    )
    is_locked: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Indique si l'utilisateur est verrouillé"
    )
    permissions: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Permissions de l'utilisateur"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now(timezone.utc),
        nullable=False,
        comment="Date de création de l'utilisateur"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
        nullable=False,
        comment="Date de la dernière mise à jour de l'utilisateur"
    )

    sessions: Mapped[list["UserSession"]] = relationship(
        "UserSession",
        back_populates="user",
        cascade=CASCADE_OPTION,
        passive_deletes=True
    )
