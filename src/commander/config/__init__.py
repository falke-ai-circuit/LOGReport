"""
Configuration module for LOGReport Commander.

Provides centralized configuration management with environment variable support.
"""

from .settings import (
    Settings,
    LoggingConfig,
    NetworkConfig,
    TelnetConfig,
    PathsConfig,
    UIConfig,
    ProcessingConfig,
    get_settings,
    reset_settings,
    configure_settings,
)

__all__ = [
    "Settings",
    "LoggingConfig",
    "NetworkConfig",
    "TelnetConfig",
    "PathsConfig",
    "UIConfig",
    "ProcessingConfig",
    "get_settings",
    "reset_settings",
    "configure_settings",
]
