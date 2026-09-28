"""Chargement de la configuration TOML du worker."""

from dataclasses import dataclass
from pathlib import Path
from tomllib import load


@dataclass(frozen=True)
class StreamConfig:
    """
    Configuration d'un flux Redis consommé par le worker.
    
    Parameters:
        name: Nom du flux Redis.
        group: Nom du groupe de consommateurs.
        consumer: Nom du consommateur.
        repository: Référentiel associé au flux.
        count: Nombre maximum d'éléments à récupérer par lecture (par défaut 10).
        block_ms: Durée maximale de blocage en millisecondes lors de la lecture (par défaut 5 000).
    """
    name: str
    group: str
    consumer: str
    repository: str
    notification_stream: str = "new_event"
    count: int = 10
    block_ms: int = 5_000


def load_streams(config_path: Path) -> list[StreamConfig]:
    """Charge les flux déclarés dans un fichier TOML.

    Args:
        config_path: Chemin du fichier de configuration.

    Returns:
        Les configurations des flux à consommer.
    """
    with config_path.open("rb") as config_file:
        raw_config = load(config_file)

    return [
        StreamConfig(
            name=stream["name"],
            group=stream["group"],
            consumer=stream["consumer"],
            repository=stream["repository"],
            notification_stream=stream.get("notification_stream", "new_event"),
            count=stream.get("count", 10),
            block_ms=stream.get("block_ms", 5_000),
        )
        for stream in raw_config.get("streams", [])
    ]
