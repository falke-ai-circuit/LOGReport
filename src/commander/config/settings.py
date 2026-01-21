"""
Settings Module - Centralized configuration management

This module provides a centralized configuration system for the LOGReport application,
with support for environment variables, type safety, and validation.

Usage:
    from commander.config import get_settings
    
    settings = get_settings()
    print(settings.network.default_timeout)
"""

import os
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional, Dict


def _get_env_path(key: str, default: str) -> Path:
    """Get a path from environment variable or use default."""
    value = os.environ.get(key, default)
    return Path(value)


def _get_env_int(key: str, default: int) -> int:
    """Get an integer from environment variable or use default."""
    value = os.environ.get(key)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _get_env_bool(key: str, default: bool) -> bool:
    """Get a boolean from environment variable or use default."""
    value = os.environ.get(key)
    if value is None:
        return default
    return value.lower() in ('true', '1', 'yes', 'on')


def _get_env_str(key: str, default: str) -> str:
    """Get a string from environment variable or use default."""
    return os.environ.get(key, default)


@dataclass
class LoggingConfig:
    """Configuration for logging."""
    
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format: str = "%Y-%m-%d %H:%M:%S"
    log_to_file: bool = False
    log_file_path: Optional[Path] = None
    max_file_size_mb: int = 10
    backup_count: int = 5
    
    def __post_init__(self) -> None:
        """Load from environment variables."""
        self.level = _get_env_str("LOGREPORT_LOG_LEVEL", self.level)
        self.log_to_file = _get_env_bool("LOGREPORT_LOG_TO_FILE", self.log_to_file)
        if self.log_to_file and not self.log_file_path:
            self.log_file_path = _get_env_path(
                "LOGREPORT_LOG_FILE",
                "logs/logreport.log"
            )


@dataclass
class NetworkConfig:
    """Configuration for network operations."""
    
    default_timeout: int = 30
    connection_timeout: int = 10
    max_retries: int = 3
    retry_delay: float = 1.0
    socket_buffer_size: int = 4096
    
    def __post_init__(self) -> None:
        """Load from environment variables."""
        self.default_timeout = _get_env_int(
            "LOGREPORT_NETWORK_TIMEOUT",
            self.default_timeout
        )
        self.max_retries = _get_env_int(
            "LOGREPORT_NETWORK_RETRIES",
            self.max_retries
        )


@dataclass
class TelnetConfig:
    """Configuration for Telnet connections."""
    
    default_port: int = 23
    read_timeout: float = 5.0
    newline: str = "\n"
    encoding: str = "utf-8"
    
    def __post_init__(self) -> None:
        """Load from environment variables."""
        self.default_port = _get_env_int(
            "LOGREPORT_TELNET_PORT",
            self.default_port
        )


@dataclass
class PathsConfig:
    """Configuration for file paths."""
    
    log_root: Path = field(default_factory=lambda: Path("test_logs"))
    config_path: Path = field(default_factory=lambda: Path("nodes.json"))
    templates_path: Path = field(default_factory=lambda: Path("templates"))
    output_path: Path = field(default_factory=lambda: Path("output"))
    
    def __post_init__(self) -> None:
        """Load from environment variables."""
        self.log_root = _get_env_path("LOGREPORT_LOG_ROOT", str(self.log_root))
        self.config_path = _get_env_path(
            "LOGREPORT_CONFIG_PATH",
            str(self.config_path)
        )
    
    def ensure_directories(self) -> None:
        """Ensure all configured directories exist."""
        for path in [self.log_root, self.templates_path, self.output_path]:
            path.mkdir(parents=True, exist_ok=True)


@dataclass
class UIConfig:
    """Configuration for UI settings."""
    
    window_width: int = 1200
    window_height: int = 800
    font_size: int = 10
    theme: str = "system"
    confirm_on_exit: bool = True
    auto_refresh_interval: int = 5000  # milliseconds
    
    def __post_init__(self) -> None:
        """Load from environment variables."""
        self.theme = _get_env_str("LOGREPORT_THEME", self.theme)
        self.confirm_on_exit = _get_env_bool(
            "LOGREPORT_CONFIRM_EXIT",
            self.confirm_on_exit
        )


@dataclass
class ProcessingConfig:
    """Configuration for command processing."""
    
    max_concurrent_commands: int = 5
    command_queue_size: int = 100
    batch_size: int = 50
    progress_update_interval: int = 100  # milliseconds
    circuit_breaker_threshold: int = 3
    circuit_breaker_timeout: int = 60
    
    def __post_init__(self) -> None:
        """Load from environment variables."""
        self.max_concurrent_commands = _get_env_int(
            "LOGREPORT_MAX_COMMANDS",
            self.max_concurrent_commands
        )
        self.batch_size = _get_env_int(
            "LOGREPORT_BATCH_SIZE",
            self.batch_size
        )


@dataclass
class Settings:
    """
    Main settings class containing all configuration sections.
    
    This is the central configuration object for the LOGReport application.
    All settings can be overridden via environment variables with the
    LOGREPORT_ prefix.
    
    Attributes:
        logging: Logging configuration
        network: Network configuration
        telnet: Telnet configuration
        paths: File paths configuration
        ui: UI configuration
        processing: Processing configuration
    
    Example:
        >>> settings = Settings()
        >>> print(settings.network.default_timeout)
        30
        >>> print(settings.paths.log_root)
        test_logs
    """
    
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    network: NetworkConfig = field(default_factory=NetworkConfig)
    telnet: TelnetConfig = field(default_factory=TelnetConfig)
    paths: PathsConfig = field(default_factory=PathsConfig)
    ui: UIConfig = field(default_factory=UIConfig)
    processing: ProcessingConfig = field(default_factory=ProcessingConfig)
    
    # Application metadata
    app_name: str = "LOGReport"
    version: str = "1.0.0"
    debug: bool = False
    
    def __post_init__(self) -> None:
        """Load from environment variables."""
        self.debug = _get_env_bool("LOGREPORT_DEBUG", self.debug)
        self.version = _get_env_str("LOGREPORT_VERSION", self.version)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary."""
        return {
            "app_name": self.app_name,
            "version": self.version,
            "debug": self.debug,
            "logging": {
                "level": self.logging.level,
                "format": self.logging.format,
                "log_to_file": self.logging.log_to_file,
            },
            "network": {
                "default_timeout": self.network.default_timeout,
                "connection_timeout": self.network.connection_timeout,
                "max_retries": self.network.max_retries,
            },
            "telnet": {
                "default_port": self.telnet.default_port,
                "read_timeout": self.telnet.read_timeout,
            },
            "paths": {
                "log_root": str(self.paths.log_root),
                "config_path": str(self.paths.config_path),
            },
            "ui": {
                "window_width": self.ui.window_width,
                "window_height": self.ui.window_height,
                "theme": self.ui.theme,
            },
            "processing": {
                "max_concurrent_commands": self.processing.max_concurrent_commands,
                "batch_size": self.processing.batch_size,
            },
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Settings":
        """Create settings from dictionary."""
        settings = cls()
        
        if "logging" in data:
            log_data = data["logging"]
            settings.logging.level = log_data.get("level", settings.logging.level)
            settings.logging.log_to_file = log_data.get(
                "log_to_file",
                settings.logging.log_to_file
            )
        
        if "network" in data:
            net_data = data["network"]
            settings.network.default_timeout = net_data.get(
                "default_timeout",
                settings.network.default_timeout
            )
            settings.network.max_retries = net_data.get(
                "max_retries",
                settings.network.max_retries
            )
        
        if "paths" in data:
            path_data = data["paths"]
            if "log_root" in path_data:
                settings.paths.log_root = Path(path_data["log_root"])
            if "config_path" in path_data:
                settings.paths.config_path = Path(path_data["config_path"])
        
        if "ui" in data:
            ui_data = data["ui"]
            settings.ui.theme = ui_data.get("theme", settings.ui.theme)
        
        if "processing" in data:
            proc_data = data["processing"]
            settings.processing.batch_size = proc_data.get(
                "batch_size",
                settings.processing.batch_size
            )
        
        return settings
    
    @classmethod
    def from_json_file(cls, path: Path) -> "Settings":
        """Load settings from a JSON file."""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_dict(data)
    
    def to_json_file(self, path: Path) -> None:
        """Save settings to a JSON file."""
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    def configure_logging(self) -> None:
        """Configure Python logging based on settings."""
        log_level = getattr(logging, self.logging.level.upper(), logging.INFO)
        
        handlers = []
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(logging.Formatter(
            self.logging.format,
            datefmt=self.logging.date_format
        ))
        handlers.append(console_handler)
        
        # File handler (if configured)
        if self.logging.log_to_file and self.logging.log_file_path:
            from logging.handlers import RotatingFileHandler
            
            # Ensure log directory exists
            self.logging.log_file_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = RotatingFileHandler(
                self.logging.log_file_path,
                maxBytes=self.logging.max_file_size_mb * 1024 * 1024,
                backupCount=self.logging.backup_count
            )
            file_handler.setLevel(log_level)
            file_handler.setFormatter(logging.Formatter(
                self.logging.format,
                datefmt=self.logging.date_format
            ))
            handlers.append(file_handler)
        
        # Configure root logger
        logging.basicConfig(
            level=log_level,
            format=self.logging.format,
            datefmt=self.logging.date_format,
            handlers=handlers
        )


# Singleton instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Get the global settings instance.
    
    Returns a singleton Settings instance that is lazily initialized
    on first access.
    
    Returns:
        Settings instance
    
    Example:
        >>> settings = get_settings()
        >>> print(settings.network.default_timeout)
        30
    """
    global _settings
    
    if _settings is None:
        _settings = Settings()
    
    return _settings


def reset_settings() -> None:
    """Reset the global settings to default values."""
    global _settings
    _settings = None


def configure_settings(settings: Settings) -> None:
    """
    Set custom settings as the global instance.
    
    Args:
        settings: Settings instance to use globally
    """
    global _settings
    _settings = settings
