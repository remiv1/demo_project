"""Collecte des événements EMSC vers le flux Redis d'ingestion."""

import asyncio
import json
import logging

from websockets.asyncio.client import connect
from websockets.exceptions import ConnectionClosed
from redis.asyncio import Redis
from redis.exceptions import RedisError

from common.config.redis import RedisConfig, RedisUser


LOGGER = logging.getLogger(__name__)
EMSC_WEBSOCKET = "wss://www.seismicportal.eu/standing_order/websocket"
INGEST_STREAM = "ingest:earthquakes:raw"


async def relay_emsc_events() -> None:
    """Transfère les messages EMSC vers Redis avec reconnexion automatique."""
    redis_client = Redis(**RedisConfig(RedisUser.WORKER).as_dict())
    try:
        while True:
            try:
                async with connect(EMSC_WEBSOCKET, ping_interval=20, ping_timeout=20) as websocket:
                    LOGGER.info("Connexion au WebSocket EMSC établie")
                    async for message in websocket:
                        event = json.loads(message)
                        if not isinstance(event, dict):
                            LOGGER.warning("Message EMSC ignoré : objet JSON attendu")
                            continue
                        await redis_client.xadd(
                            INGEST_STREAM,
                            {"payload": json.dumps(event, separators=(",", ":"))},
                        )
            except (OSError, ConnectionClosed, json.JSONDecodeError, RedisError) as error:
                LOGGER.warning("Flux EMSC interrompu : %s", error)
            await asyncio.sleep(5)
    finally:
        await redis_client.aclose()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(relay_emsc_events())
