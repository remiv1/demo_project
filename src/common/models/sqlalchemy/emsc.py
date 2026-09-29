"""Modèle SQLAlchemy pour les données EMSC."""

from typing import TYPE_CHECKING
from datetime import datetime

from geoalchemy2 import Geometry
from sqlalchemy import (
    CheckConstraint,
    Computed,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    JSON,
    DateTime,
)
from sqlalchemy.orm import mapped_column, Mapped, relationship

from .common import CommonMixin

if TYPE_CHECKING:
    from common.models.pydantics.events import Feature

class EMSC(CommonMixin):
    """
    Modèle représentant les données EMSC.
    
    Ce modèle contient les informations de base sur les événements EMSC.
    Il est lié aux détails spécifiques de chaque événement via la table EMSCDetails.

    arguments:
        id: Identifiant unique de l'enregistrement EMSC.
        ext_id: Identifiant externe de l'enregistrement EMSC.
    """
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
        unique=True,
        comment="Identifiant externe de l'enregistrement"
    )
    emsc_details: Mapped[list["EMSCDetails"]] = relationship(
        "EMSCDetails",
        back_populates="emsc",
        uselist=True,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    initial_datetime: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        comment="Date et heure initiale de l'événement"
    )


class EMSCDetails(CommonMixin):
    """
    Table représentant les détails des événements EMSC.

    arguments:
        id: Identifiant unique de l'enregistrement EMSCDetails.
        emsc_id: Identifiant de l'enregistrement EMSC associé.
        magnitude: Magnitude de l'événement.
        location: Localisation de l'événement.
        additional_data: Données supplémentaires de l'événement.
    """
    __tablename__ = "emsc_details"
    __table_args__ = (
        CheckConstraint("longitude BETWEEN -180 AND 180", name="emsc_longitude"),
        CheckConstraint("latitude BETWEEN -90 AND 90", name="emsc_latitude"),
        Index(
            "ix_emsc_details_latest_version",
            "emsc_id",
            "event_datetime",
            "id",
        ),
        Index("ix_emsc_details_position", "position", postgresql_using="gist"),
        {"schema": "app_schema"},
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="Identifiant unique de l'enregistrement"
    )
    emsc_id: Mapped[int] = mapped_column(
        ForeignKey("app_schema.emsc.id", ondelete="CASCADE"),
        nullable=False,
        comment="Identifiant de l'enregistrement EMSC associé"
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
    longitude: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Longitude de l'événement"
    )
    latitude: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Latitude de l'événement",
    )
    position: Mapped[object] = mapped_column(
        Geometry(geometry_type="POINT", srid=4326, spatial_index=False),
        Computed("ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)", persisted=True),
        nullable=False,
    )
    depth: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Profondeur de l'événement"
    )
    additional_data: Mapped[dict] = mapped_column(
        JSON,
        nullable=True,
        comment="Données supplémentaires de l'événement"
    )
    event_datetime: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        comment="Date et heure de l'événement"
    )

    # Relations
    emsc: Mapped["EMSC"] = relationship(
        "EMSC",
        back_populates="emsc_details",
        passive_deletes=True,
    )


class GeographicZone(CommonMixin):
    """Zone Natural Earth utilisable pour les recherches spatiales."""

    __tablename__ = "geographic_zone"
    __table_args__ = (
        CheckConstraint("kind IN ('country', 'continent', 'ocean')", name="zone_kind"),
        Index("ix_geographic_zone_boundary", "boundary", postgresql_using="gist"),
        {"schema": "app_schema"},
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="Identifiant unique de la zone géographique",
    )
    kind: Mapped[str] = mapped_column(
        String,
        nullable=False,
        comment="Type de la zone géographique (pays, continent, océan)"
    )
    code: Mapped[str] = mapped_column(
        String,
        nullable=False,
        unique=True,
        comment="Code unique de la zone géographique"
    )
    name: Mapped[str] = mapped_column(
        String,
        nullable=False,
        comment="Nom de la zone géographique"
    )
    boundary: Mapped[object] = mapped_column(
        Geometry(geometry_type="MULTIPOLYGON", srid=4326, spatial_index=False),
        nullable=False,
        comment="Limite géographique de la zone"
    )
