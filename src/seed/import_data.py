"""Import initial rejouable des contours Natural Earth et des événements EMSC."""

import io
import json
import logging
from os import getenv, environ
import tomllib
import zipfile
from datetime import datetime, timedelta, timezone
from collections.abc import Iterator
from typing import Any
from pathlib import Path

import psycopg2
import requests
import shapefile
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import Session

from api_worker.repositories.earthquakes import EarthquakesRepo


LOGGER = logging.getLogger(__name__)
NATURAL_EARTH = "https://naturalearth.s3.amazonaws.com"
FDSN_URL = "https://www.seismicportal.eu/fdsnws/event/1/query"
DATASETS = {
    "country": "110m_cultural/ne_110m_admin_0_countries",
    "ocean": "110m_physical/ne_110m_ocean",
    "marine": "110m_physical/ne_110m_geography_marine_polys",
}


def download_shapes(session: requests.Session, dataset: str) -> shapefile.Reader:
    """Charge une archive Natural Earth en mémoire.

    Args:
        session: Session HTTP réutilisable.
        dataset: Chemin du jeu Natural Earth sans extension.

    Returns:
        Lecteur des géométries et attributs du jeu.
    """
    response = session.get(f"{NATURAL_EARTH}/{dataset}.zip", timeout=90)
    response.raise_for_status()
    archive = zipfile.ZipFile(io.BytesIO(response.content))
    base_name = dataset.rsplit("/", 1)[-1]
    return shapefile.Reader(
        shp=io.BytesIO(archive.read(f"{base_name}.shp")),
        shx=io.BytesIO(archive.read(f"{base_name}.shx")),
        dbf=io.BytesIO(archive.read(f"{base_name}.dbf")),
    )


def iter_geometries(reader: shapefile.Reader) -> Iterator[tuple[dict[str, Any], str]]:
    """Parcourt les attributs et géométries présents dans une archive.

    Args:
        reader: Lecteur des contours Natural Earth.

    Yields:
        Attributs et géométrie GeoJSON des enregistrements complets.
    """
    for record in reader.iterShapeRecords():
        if record.record is not None and record.shape is not None:
            yield record.record.as_dict(), json.dumps(record.shape.__geo_interface__)


def import_zones(connection: psycopg2.extensions.connection, session: requests.Session) -> None:
    """Importe les terres, continents et océans dans des zones spatiales.

    Args:
        connection: Connexion à la base principale migrée.
        session: Session HTTP réutilisable.
    """
    countries = download_shapes(session, DATASETS["country"])
    oceans = download_shapes(session, DATASETS["ocean"])
    marine = download_shapes(session, DATASETS["marine"])
    continent_codes: dict[str, list[str]] = {}
    with connection.cursor() as cursor:
        for properties, geometry in iter_geometries(countries):
            code = properties["ADM0_A3"]
            name = properties["NAME"]
            continent = properties["CONTINENT"]
            if not isinstance(code, str) or code == "-99" or not isinstance(continent, str):
                continue
            continent_codes.setdefault(continent, []).append(f"C:{code}")
            cursor.execute(
                """INSERT INTO app_schema.geographic_zone (kind, code, name, boundary)
                   VALUES ('country', %s, %s, ST_Multi(ST_GeomFromGeoJSON(%s)))
                   ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name,
                       boundary = EXCLUDED.boundary""",
                (f"C:{code}", name, geometry),
            )

        for name, codes in sorted(continent_codes.items()):
            cursor.execute(
                """INSERT INTO app_schema.geographic_zone (kind, code, name, boundary)
                   SELECT 'continent', %s, %s, ST_Multi(ST_UnaryUnion(ST_Collect(boundary)))
                   FROM app_schema.geographic_zone
                   WHERE kind = 'country' AND code = ANY(%s)
                   ON CONFLICT (code) DO UPDATE SET boundary = EXCLUDED.boundary""",
                (f"T:{name}", name, codes),
            )

        for index, (_, geometry) in enumerate(iter_geometries(oceans)):
            cursor.execute(
                """INSERT INTO app_schema.geographic_zone (kind, code, name, boundary)
                   VALUES ('ocean', %s, 'Océan (sans pays)', ST_Multi(ST_GeomFromGeoJSON(%s)))
                   ON CONFLICT (code) DO UPDATE SET boundary = EXCLUDED.boundary""",
                (f"O:global:{index}", geometry),
            )

        for properties, geometry in iter_geometries(marine):
            name = properties.get("name") or properties.get("NAME")
            if not isinstance(name, str) or "ocean" not in name.lower():
                continue
            cursor.execute(
                """INSERT INTO app_schema.geographic_zone (kind, code, name, boundary)
                   VALUES ('ocean', %s, %s, ST_Multi(ST_GeomFromGeoJSON(%s)))
                   ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name,
                       boundary = EXCLUDED.boundary""",
                (f"O:{name}", name, geometry),
            )
    connection.commit()
    LOGGER.info("Contours Natural Earth importés")


def import_history(
    db_session: Session,
    session: requests.Session,
    start: datetime,
    end: datetime,
    timeout: int,
) -> None:
    """Importe l'historique FDSN par intervalles d'une journée.

    Args:
        db_session: Session SQLAlchemy pour la base principale migrée.
        session: Session HTTP réutilisable.
        start: Début inclus en UTC.
        end: Fin exclue en UTC.
        timeout: Délai maximal des requêtes FDSN en secondes.
    """
    date = start
    while date < end:
        next_date = min(date + timedelta(days=1), end)
        response = session.get(
            FDSN_URL,
            params={"start": date.isoformat(), "end": next_date.isoformat(),
                    "format": "json", "limit": 10000, "nodata": 204},
            timeout=timeout,
        )
        response.raise_for_status()
        if response.status_code == 204:
            date = next_date
            continue
        features = response.json()["features"]
        if len(features) >= 10000:
            raise ValueError(f"Limite FDSN atteinte pour {date.date()} : découper la période")

        repository = EarthquakesRepo(db_session)
        imported = 0
        with db_session.begin():
            for feature in features:
                properties = feature["properties"]
                if properties.get("mag") is None:
                    continue
                repository.ingest(feature, commit=False)
                imported += 1
        LOGGER.info("%s : %s événements importés", date.date(), imported)
        date = next_date


def main() -> None:
    """Charge les contours puis l'historique selon la période configurée."""
    logging.basicConfig(level=logging.INFO)
    with Path(__file__).with_name("infra.conf").open("rb") as configuration_file:
        ingestion = tomllib.load(configuration_file)["ingestion"]
    start = datetime.fromisoformat(getenv("HISTORY_START", ingestion["history_start"]))
    end = datetime.fromisoformat(getenv("HISTORY_END", datetime.now(timezone.utc).isoformat()))
    if start.tzinfo is None or end.tzinfo is None or start >= end:
        raise ValueError("HISTORY_START et HISTORY_END doivent définir une période UTC valide")
    database_options = {
        "host": getenv("POSTGRES_HOST", "postgres"),
        "port": getenv("POSTGRES_PORT", "5432"),
        "dbname": getenv("POSTGRES_DB_MAIN"),
        "user": getenv("POSTGRES_USER_APP"),
        "password": environ["POSTGRES_PASSWORD_APP"],
    }
    engine = create_engine(URL.create(
        "postgresql+psycopg2",
        username=database_options["user"],
        password=database_options["password"],
        host=database_options["host"],
        port=int(database_options["port"]),
        database=database_options["dbname"],
    ))
    try:
        with requests.Session() as session, psycopg2.connect(**database_options) as connection:
            import_zones(connection, session)
            with Session(engine) as db_session:
                import_history(db_session, session, start, end, ingestion["timeout"])
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
