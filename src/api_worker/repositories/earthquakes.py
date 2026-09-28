"""Repository d'ingestion des tremblements de terre."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, scoped_session

from common.models.sqlalchemy.emsc import EMSC, EMSCDetails
from common.models.pydantics.events import Feature

class EarthquakesRepo():
    """Repository des tremblements de terre."""

    def __init__(self, session: Session | scoped_session[Session]) -> None:
        self.session = session

    def __upset_event(self, feature: Feature) -> "EMSC":
        emsc = self.get_by_ext_id(feature.id)
        if not emsc:
            emsc = EMSC(
                ext_id=feature.id,
                initial_datetime=feature.properties.time,
            )
            self.session.add(emsc)
            self.session.flush()
        return emsc

    def __add_event_details(self, emsc_id: int, feature: Feature) -> "EMSCDetails":
        emsc_details = EMSCDetails(
            emsc_id=emsc_id,
            magnitude=feature.properties.mag,
            location=feature.geometry.coordinates,
            latitude=feature.properties.lat,
            longitude=feature.properties.lon,
            event_datetime=feature.properties.lastupdate,
            depth=feature.properties.depth,
            additional_data={
                "source_id": feature.properties.source_id,
                "source_catalog": feature.properties.source_catalog,
                "flynn_region": feature.properties.flynn_region,
                "evtype": feature.properties.evtype,
                "auth": feature.properties.auth,
                "mag": feature.properties.mag,
                "mag_type": feature.properties.magtype,
                "unid": feature.properties.unid,
            }
        )
        self.session.add(emsc_details)
        self.session.flush()
        return emsc_details

    def get_by_ext_id(self, ext_id: str) -> EMSC | None:
        """Récupère un tremblement de terre par son identifiant externe."""
        stmt = select(EMSC).where(EMSC.ext_id == ext_id)
        return self.session.execute(stmt).scalar_one_or_none()

    def ingest(self, payload: dict[str, Any], *, commit: bool = True) -> dict[str, Any]:
        """Ingère un tremblement de terre en base de données.

        Args:
            payload: Événement EMSC au format GeoJSON.
            commit: Valide immédiatement la transaction si vrai.

        Returns:
            Enregistrement EMSC et ses détails.
        """
        feature = Feature(**payload)
        emsc = self.__upset_event(feature)
        emsc_details = self.__add_event_details(emsc.id, feature)
        if commit:
            self.session.commit()
        return {
            "emsc": emsc,
            "emsc_details": emsc_details,
        }
