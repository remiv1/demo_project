"""Repository d'ingestion des tremblements de terre."""

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session, scoped_session

from common.models.sqlalchemy.emsc import EMSC, EMSCDetails, GeographicZone
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

    def get_geographic_zones(self, longitude: float, latitude: float) -> dict[str, str | None]:
        """Recherche les noms du pays et du continent contenant un point.

        Args:
            longitude: Longitude du point en degrés.
            latitude: Latitude du point en degrés.

        Returns:
            Les noms des zones trouvées, ou None lorsqu'aucune zone ne correspond.
        """
        point = func.ST_SetSRID(func.ST_Point(longitude, latitude), 4326)
        stmt = (
            select(GeographicZone.kind, GeographicZone.name)
            .where(
                GeographicZone.kind.in_(("country", "continent")),
                func.ST_Covers(GeographicZone.boundary, point),
            )
            .order_by(GeographicZone.id)
        )
        zones: dict[str, str] = {}
        for kind, name in self.session.execute(stmt):
            zones.setdefault(kind, name)
        return {
            "country": zones.get("country"),
            "continent": zones.get("continent"),
        }

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

    def map_events(self, start: datetime, stop: datetime) -> dict[str, Any]:
        """Retourne la dernière version des séismes sur une période UTC.

        Args:
            start: Début inclus de la période, en UTC sans fuseau SQL.
            stop: Fin exclusive de la période, en UTC sans fuseau SQL.

        Returns:
            Collection GeoJSON sans troncature des événements.
        """
        latest_id = (
            select(EMSCDetails.id)
            .where(EMSCDetails.emsc_id == EMSC.id)
            .order_by(EMSCDetails.event_datetime.desc(), EMSCDetails.id.desc())
            .limit(1)
            .correlate(EMSC)
            .scalar_subquery()
        )
        zones = [
            select(GeographicZone.name)
            .where(
                GeographicZone.kind == kind,
                func.ST_Covers(GeographicZone.boundary, EMSCDetails.position),
            )
            .order_by(GeographicZone.id)
            .limit(1)
            .correlate(EMSCDetails)
            .scalar_subquery()
            .label(kind)
            for kind in ("country", "continent")
        ]
        stmt = (
            select(
                EMSC.ext_id, EMSC.initial_datetime,
                EMSCDetails.latitude, EMSCDetails.longitude,
                EMSCDetails.magnitude, EMSCDetails.depth,
                EMSCDetails.additional_data, EMSCDetails.event_datetime,
                *zones,
            )
            .select_from(EMSC)
            .join(EMSCDetails, EMSCDetails.id == latest_id)
            .where(EMSC.initial_datetime >= start, EMSC.initial_datetime < stop)
            .order_by(EMSC.initial_datetime.desc(), EMSC.id.desc())
        )
        features: list[dict[str, Any]] = []
        for row in self.session.execute(stmt).mappings():
            extra = row["additional_data"] or {}
            features.append({
                "type": "Feature",
                "id": f"earthquakes:{row['ext_id']}",
                "geometry": {
                    "type": "Point",
                    "coordinates": [row["longitude"], row["latitude"]],
                },
                "properties": {
                    "type": "earthquakes",
                    "time": row["initial_datetime"].replace(tzinfo=timezone.utc).isoformat(),
                    "lastupdate": row["event_datetime"].replace(tzinfo=timezone.utc).isoformat(),
                    "mag": row["magnitude"],
                    "magtype": extra.get("mag_type"),
                    "depth": row["depth"],
                    "flynn_region": extra.get("flynn_region"),
                    "country": row["country"],
                    "continent": row["continent"],
                },
            })
        return {"type": "FeatureCollection", "features": features}
