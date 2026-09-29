"""Lecture authentifiée des événements pour la carte historique."""

from calendar import monthrange
from datetime import date, datetime, time, timedelta
from os import getenv
from typing import Annotated, Any

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import Session

from common.repositories.earthquakes import EarthquakesRepo
from .user.routes import current_session, database, internal_key


router = APIRouter(prefix="/events", tags=["events"], dependencies=[Depends(internal_key)])
engine = create_engine(URL.create(
    "postgresql+psycopg2",
    username=getenv("POSTGRES_USER_APP", "emsc"),
    password=getenv("POSTGRES_PASSWORD_APP"),
    host=getenv("POSTGRES_HOST", "db-main"),
    port=int(getenv("POSTGRES_PORT", "5432")),
    database=getenv("POSTGRES_DB_MAIN", "emsc_main"),
), pool_pre_ping=True)


def period_bounds(start: date, end: date) -> tuple[datetime, datetime]:
    """Valide un mois glissant et traduit la fin incluse en borne exclusive.

    Args:
        start: Première journée UTC incluse.
        end: Dernière journée UTC incluse.

    Returns:
        Bornes UTC sans fuseau pour les colonnes SQL existantes.

    Raises:
        ValueError: Si les dates ne définissent pas une période autorisée.
    """
    try:
        year = start.year + (start.month == 12)
        month = start.month % 12 + 1
        maximum = date(year, month, min(start.day, monthrange(year, month)[1]))
        if end < start or end > maximum:
            raise ValueError("La période doit être comprise entre un jour et un mois glissant.")
        return (
            datetime.combine(start, time.min),
            datetime.combine(end + timedelta(days=1), time.min),
        )
    except (OverflowError, ValueError) as error:
        raise ValueError(
            "La période doit être comprise entre un jour et un mois glissant."
        ) from error


@router.get(
    "",
    responses={
        403: {"description": "Validation TOTP requise"},
        422: {"description": "Période invalide"},
    },
)
def events(
    start: date,
    end: date,
    response: Response,
    db: Annotated[Session, Depends(database)],
    auth_session: Annotated[str | None, Cookie()] = None,
) -> dict[str, Any]:
    """Retourne le GeoJSON historique après validation de la session TOTP.

    Args:
        start: Date de début incluse.
        end: Date de fin incluse.
        response: Réponse HTTP à protéger de la mise en cache.
        auth_session: Cookie opaque transmis par le frontend.
        db: Session de consultation des comptes.

    Returns:
        Collection GeoJSON des dernières versions connues des séismes.
    """
    entry = current_session(db, auth_session)
    if entry.verified_at is None:
        raise HTTPException(status_code=403, detail="Validation TOTP requise")
    try:
        lower, upper = period_bounds(start, end)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    response.headers["Cache-Control"] = "no-store"
    with Session(engine) as main_db:
        return EarthquakesRepo(main_db).map_events(lower, upper)
