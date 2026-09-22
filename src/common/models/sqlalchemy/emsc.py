"""Modèle SQLAlchemy pour les données EMSC."""

from sqlalchemy import Float, Integer, String, JSON
from sqlalchemy.orm import mapped_column, Mapped

from .common import CommonMixin

class EMSC(CommonMixin):
    """
    Modèle représentant les données EMSC.
    
    TODO: Modifier les champs suivant les données récupérées"""
    __tablename__ = "emsc"
    __table_args__ = {
        "schema": "app_schema",
    }

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="Identifiant unique de l'enregistrement"
    )
    ext_id: Mapped[str] = mapped_column(
        String,
        nullable=False,
        comment="Identifiant externe de l'enregistrement"
    )
    magnitude: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Magnitude de l'événement"
    )
    location: Mapped[str] = mapped_column(
        String,
        nullable=False,
        comment="Localisation de l'événement"
    )
    additional_data: Mapped[dict] = mapped_column(
        JSON,
        nullable=True,
        comment="Données supplémentaires de l'événement"
    )
