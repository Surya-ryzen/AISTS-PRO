from pathlib import Path
import yaml


class ConfigManager:
    """
    Centralized configuration loader.
    """

    _cache = {}

    @classmethod
    def get(cls, config_name: str):

        if config_name in cls._cache:
            return cls._cache[config_name]

        config_path = Path("configs") / f"{config_name}.yaml"

        with open(config_path, "r", encoding="utf-8") as file:
            config = yaml.safe_load(file)

        cls._cache[config_name] = config

        return config