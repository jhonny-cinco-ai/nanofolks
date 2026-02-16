"""Configuration module for nanofolks."""

from nanofolks.config.loader import load_config, get_config_path
from nanofolks.config.schema import Config

__all__ = ["Config", "load_config", "get_config_path"]
