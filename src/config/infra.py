"""Module for handling infrastructure configuration."""

from tomllib import load as toml_load
from tomli_w import dump as toml_write
from .models import InfraConfigModel

class InfraConfig:
    """Class representing the infrastructure configuration."""
    def __init__(self):
        self.__config = {}
        self.reload_config()

    def reload_config(self):
        """Reloads the infrastructure configuration from the TOML file."""
        with open("infra.conf", "rb") as f:
            self.__config = toml_load(f)
        self.config = InfraConfigModel(**self.__config)
        self.ingestion = self.config.ingestion

    def get_config(self):
        """Returns the loaded infrastructure configuration."""
        return self.__config

    def set_config(self, model: InfraConfigModel, conserve: bool = False):
        """Sets the infrastructure configuration."""
        self.__config = model.model_dump()
        if conserve:
            with open("infra.conf", "wb") as f:
                toml_write(
                    self.__config,
                    f,
                    multiline_strings=True,
                    indent=4,
                )
