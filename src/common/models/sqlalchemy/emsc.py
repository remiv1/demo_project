"""Modèle SQLAlchemy pour les données EMSC."""

from sqlalchemy import Float, Integer, String, JSON
from sqlalchemy.orm import mapped_column, Mapped

from .common import CommonMixin

class EMSC(CommonMixin):
    """Modèle représentant les données EMSC."""
    __tablename__ = "emsc"
    __table_args__ = {
        "schema": "app_schema",
    }

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ext_id: Mapped[str] = mapped_column(String, nullable=False)
    magnitude: Mapped[float] = mapped_column(Float, nullable=False)
    location: Mapped[str] = mapped_column(String, nullable=False)
    additional_data: Mapped[dict] = mapped_column(JSON, nullable=True)
