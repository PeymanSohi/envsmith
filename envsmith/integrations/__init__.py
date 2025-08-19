"""Framework integrations for smart-envloader."""

from .fastapi import Settings, get_settings
from .django import EnvAppConfig

__all__ = ["Settings", "get_settings", "EnvAppConfig"]
