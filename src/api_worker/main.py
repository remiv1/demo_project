"""Point d'entrée du worker d'ingestion Redis."""

import json
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, cast

from redis import Redis
from redis.exceptions import RedisError, ResponseError

from common.config.redis import RedisConfig, RedisUser
from common.repositories import (
    REPOSITORIES,
    RepositoryNotImplementedError,
)

from .config import StreamConfig, load_streams


LOGGER = logging.getLogger(__name__)


def create_redis_client() -> Redis:
    """
    Crée le client Redis avec le rôle du worker.

    Returns:
        Redis: Le client Redis configuré pour le worker.
    """
    return Redis(
        **RedisConfig(RedisUser.WORKER).as_dict(),
        socket_timeout=10,
    )


def create_consumer_group(
    redis_client: Redis,
    stream: StreamConfig,
) -> None:
    """
    Crée le groupe Redis s'il n'existe pas encore.

    Args:
        redis_client (Redis): Le client Redis.
        stream (StreamConfig): La configuration du flux Redis.
    """
    try:
        redis_client.xgroup_create(stream.name, stream.group, id="0-0", mkstream=True)
    except ResponseError as error:
        if "BUSYGROUP" not in str(error):
            raise


def get_repository(
    stream: StreamConfig,
):
    """
    Retourne le repository associé à un flux configuré.

    Args:
        stream (StreamConfig): La configuration du flux Redis.

    Returns:
        IngestionRepository: Le repository associé au flux.
    """
    try:
        return REPOSITORIES[stream.repository]
    except KeyError as error:
        raise ValueError(
            f"Repository inconnu pour le flux {stream.name}: {stream.repository}"
        ) from error


def ingest_message(
    redis_client: Redis,
    stream: StreamConfig,
    repository: object,
    message_id: str,
    fields: dict[str, str],
) -> None:
    """
    Ingère un message puis l'acquitte après validation.
    
    Args:
        redis_client (Redis): Le client Redis.
        stream (StreamConfig): La configuration du flux Redis.
        repository (object): Le repository pour ingérer les messages.
        message_id (str): L'identifiant du message.
        fields (dict[str, str]): Les champs du message.

    Returns:
        None
    """
    payload: Any = json.loads(fields["payload"])
    if not isinstance(payload, dict):
        raise ValueError("Objet JSON attendu dans le message Redis")
    if stream.repository == "earthquakes":
        payload = payload.get("data")
        if not isinstance(payload, dict):
            raise ValueError("Objet JSON attendu dans data pour le flux EMSC")
    event = repository.ingest(payload)  # type: ignore
    if stream.repository == "earthquakes":
        properties = payload["properties"]
        geographic_zones = repository.get_geographic_zones(  # type: ignore[attr-defined]
            properties["lon"], properties["lat"]
        )
        notification_event = {
            **payload,
            "properties": {**properties, **geographic_zones},
        }
    else:
        notification_event = event
    redis_client.xadd(
        stream.notification_stream,
        {
            "payload": json.dumps(
                {"type": stream.repository, "event": notification_event},
                separators=(",", ":"),
            )
        },
    )
    redis_client.xack(stream.name, stream.group, message_id)


def process_entries(
    redis_client: Redis,
    stream: StreamConfig,
    repository: object,
    entries: list[tuple[str, list[tuple[str, dict[str, str]]]]],
) -> str | None:
    """Traite les entrées reçues et retourne l'identifiant de la dernière."""
    last_id = None
    for _, messages in entries:
        for message_id, fields in messages:
            last_id = message_id
            try:
                ingest_message(redis_client, stream, repository, message_id, fields)
            except (KeyError, ValueError, RepositoryNotImplementedError, RedisError):
                LOGGER.exception(
                    "Message non acquitté: flux=%s id=%s",
                    stream.name,
                    message_id,
                )
    return last_id


def consume_stream(
    redis_client: Redis,
    stream: StreamConfig,
    repository: object,
) -> None:
    """
    Consomme continuellement un flux Redis.
    Args:
        redis_client (Redis): Le client Redis.
        stream (StreamConfig): La configuration du flux Redis.
        repository (IngestionRepository): Le repository pour ingérer les messages.

    Returns:
        None
    """
    pending_id = "0"
    while True:
        pending = cast(
            list[tuple[str, list[tuple[str, dict[str, str]]]]],
            redis_client.xreadgroup(
                stream.group,
                stream.consumer,
                {stream.name: pending_id},
                count=stream.count,
            ),
        )
        pending_id = process_entries(redis_client, stream, repository, pending)
        if pending_id is None:
            break

    while True:
        entries = cast(
            list[tuple[str, list[tuple[str, dict[str, str]]]]],
            redis_client.xreadgroup(
                stream.group,
                stream.consumer,
                {stream.name: ">"},
                count=stream.count,
                block=stream.block_ms,
            ),
        )
        process_entries(redis_client, stream, repository, entries)


def main() -> None:
    """Initialise Redis et lance les consommateurs configurés."""
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    config_path = Path(os.getenv("WORKER_CONFIG", "/etc/worker/worker.conf"))
    streams = load_streams(config_path)
    redis_client = create_redis_client()
    redis_client.ping()

    for stream in streams:
        create_consumer_group(redis_client, stream)

    with ThreadPoolExecutor(max_workers=len(streams)) as executor:
        futures = [
            executor.submit(consume_stream, redis_client, stream, get_repository(stream))
            for stream in streams
        ]
        for future in futures:
            future.result()


if __name__ == "__main__":
    main()
