"""Redis configuration for the API backend and frontend."""

from os import getenv
from enum import Enum
from typing import Generator, Any

from pydantic import SecretStr

class RedisUser(Enum):
    """Enum representing different Redis users."""
    DEFAULT = "default"
    APPLICATION = "application"
    WORKER = "worker"
    MONITOR = "monitor"

class RedisConfig:
    """Configuration for connecting to Redis."""

    def __init__(self, user: RedisUser=RedisUser.DEFAULT) -> None:
        self.role: RedisUser = user
        self.host: str = getenv("REDIS_HOST", "redis-streams")
        self.port: int = int(getenv("REDIS_PORT", "6379"))
        self.db: int = int(getenv("REDIS_DB", "0"))
        self.__username: str | None
        self.__password: SecretStr | None
        self.decode_responses: bool = True

        match self.role:
            case RedisUser.APPLICATION:
                self.__username = getenv("REDIS_USERNAME", "")
                self.__password = SecretStr(getenv("REDIS_PASSWORD", ""))
            case RedisUser.WORKER:
                self.__username = getenv("REDIS_WORKER_USERNAME", "")
                self.__password = SecretStr(getenv("REDIS_WORKER_PASSWORD", ""))
            case RedisUser.MONITOR:
                self.__username = getenv("REDIS_MONITOR_USERNAME", "")
                self.__password = SecretStr(getenv("REDIS_MONITOR_PASSWORD", ""))
            case _:
                self.__username = None
                self.__password = None

    def __iter__(self) -> Generator[tuple[str, str | int | bool], None, None]:
        """
        Allows the RedisConfig instance to be iterated over as key-value pairs.
        """
        yield "host", self.host
        yield "port", self.port
        yield "db", self.db
        yield "username", self.get_username()
        yield "password", self.get_password()
        yield "decode_responses", self.decode_responses

    def __repr__(self) -> str:
        """Returns a string representation of the RedisConfig instance."""
        return (
            f"RedisConfig(host={self.host}, "
            f"port={self.port}, "
            f"db={self.db}, "
            f"username={self.__username}, "
            f"password={self.__password}, "
            f"decode_responses={self.decode_responses})"
        )

    def get_username(self) -> str:
        """
        Returns the Redis username. Prefers a getter to a property access, it
        ensure intention is clear when accessing the username.

        Returns:
            str: The Redis username.
        """
        return self.__username or ""

    def get_password(self) -> str:
        """
        Returns the Redis password. Prefers a getter to a property access, it
        ensure intention is clear when accessing the password.

        Returns:
            str: The Redis password.
        """
        return self.__password.get_secret_value() if self.__password else ""

    def as_dict(self) -> dict[str, Any]:
        """
        Returns a dictionary representation of the Redis connection parameters.

        Returns:
            dict[str, str | int | bool]: The Redis connection parameters as a dictionary.
        """
        return dict(self)
