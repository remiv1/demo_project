"""
Redis commands for the API backend.
"""

from json import dumps, loads
from typing import cast

from fastapi import APIRouter, HTTPException, status
from redis import Redis
from redis.exceptions import ResponseError
from common.config.redis import RedisConfig, RedisUser

from .models import NewSeismMessage

router = APIRouter(
    prefix="/redis",
    tags=["api", "v1", "redis"],
)


def get_redis_client(user: RedisUser) -> Redis:
    """Crée un client Redis pour le rôle demandé."""
    return Redis(**RedisConfig(user).as_dict())


@router.post("/streams/{stream}/groups", status_code=status.HTTP_201_CREATED)
async def create_consumer_group(
    stream: str,
    group: str,
    start_id: str = "0-0",
) -> dict[str, str]:
    """Crée un groupe de consommateurs Redis Streams."""
    try:
        get_redis_client(RedisUser.WORKER).xgroup_create(
            stream,
            group,
            id=start_id,
            mkstream=True,
        )
    except ResponseError as error:
        if "BUSYGROUP" in str(error):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Le groupe existe déjà pour ce flux.",
            ) from error
        raise

    return {"stream": stream, "group": group, "start_id": start_id}


@router.post("/streams/{stream}/messages", status_code=status.HTTP_201_CREATED)
async def publish_seism_message(
    stream: str,
    message: NewSeismMessage,
) -> dict[str, str]:
    """Publie un événement sismique dans un Redis Stream."""
    payload = dumps(message.model_dump(mode="json"), separators=(",", ":"))
    message_id = get_redis_client(RedisUser.WORKER).xadd(
        stream,
        {"payload": payload},
    )
    return {"stream": stream, "message_id": str(message_id)}


@router.get("/streams/{stream}/groups/{group}/messages")
async def read_stream_messages(
    stream: str,
    group: str,
    consumer: str,
    pending: bool = False,
    count: int = 10,
) -> dict[str, object]:
    """Lit les nouveaux messages ou ceux en attente d'un consommateur."""
    stream_id = "0" if pending else ">"
    try:
        entries = cast(
            list[tuple[str, list[tuple[str, dict[str, str]]]]],
            get_redis_client(RedisUser.APPLICATION).xreadgroup(
                group,
                consumer,
                {stream: stream_id},
                count=count,
            ),
        )
    except ResponseError as error:
        if "NOGROUP" in str(error):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Le groupe n'existe pas pour ce flux.",
            ) from error
        raise

    messages = [
        {
            "id": message_id,
            "payload": loads(fields["payload"]),
        }
        for _, stream_entries in entries
        for message_id, fields in stream_entries
    ]
    return {"stream": stream, "group": group, "consumer": consumer, "messages": messages}


@router.post("/streams/{stream}/groups/{group}/messages/{message_id}/ack")
async def acknowledge_stream_message(
    stream: str,
    group: str,
    message_id: str,
) -> dict[str, str | int]:
    """Acquitte un message Redis Stream après son traitement."""
    acknowledged = get_redis_client(RedisUser.APPLICATION).xack(
        stream,
        group,
        message_id,
    )
    return {
        "stream": stream,
        "group": group,
        "message_id": message_id,
        "acknowledged": acknowledged,
    }
