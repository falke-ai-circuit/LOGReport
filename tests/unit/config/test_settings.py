"""
Unit tests for the Settings configuration module.

Tests configuration loading, environment variable support, and validation.
"""

import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src'))

import json
import tempfile
from pathlib import Path
import pytest

from commander.config.settings import (
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


class TestLoggingConfig:
    """Tests for LoggingConfig."""
    
    def test_default_values(self):
        """Test default configuration values."""
        config = LoggingConfig()
        assert config.level == "INFO"
        assert config.log_to_file is False
    
    def test_env_override(self, monkeypatch):
        """Test environment variable override."""
        monkeypatch.setenv("LOGREPORT_LOG_LEVEL", "DEBUG")
        config = LoggingConfig()
        assert config.level == "DEBUG"


class TestNetworkConfig:
    """Tests for NetworkConfig."""
    
    def test_default_values(self):
        """Test default configuration values."""
        config = NetworkConfig()
        assert config.default_timeout == 30
        assert config.max_retries == 3
    
    def test_env_override(self, monkeypatch):
        """Test environment variable override."""
        monkeypatch.setenv("LOGREPORT_NETWORK_TIMEOUT", "60")
        config = NetworkConfig()
        assert config.default_timeout == 60


class TestTelnetConfig:
    """Tests for TelnetConfig."""
    
    def test_default_values(self):
        """Test default configuration values."""
        config = TelnetConfig()
        assert config.default_port == 23
        assert config.encoding == "utf-8"


class TestPathsConfig:
    """Tests for PathsConfig."""
    
    def test_default_values(self):
        """Test default configuration values."""
        config = PathsConfig()
        assert config.log_root == Path("test_logs")
        assert config.config_path == Path("nodes.json")
    
    def test_ensure_directories(self, tmp_path):
        """Test directory creation."""
        config = PathsConfig(
            log_root=tmp_path / "logs",
            output_path=tmp_path / "output"
        )
        config.ensure_directories()
        assert config.log_root.exists()
        assert config.output_path.exists()


class TestUIConfig:
    """Tests for UIConfig."""
    
    def test_default_values(self):
        """Test default configuration values."""
        config = UIConfig()
        assert config.window_width == 1200
        assert config.theme == "system"
        assert config.confirm_on_exit is True


class TestProcessingConfig:
    """Tests for ProcessingConfig."""
    
    def test_default_values(self):
        """Test default configuration values."""
        config = ProcessingConfig()
        assert config.max_concurrent_commands == 5
        assert config.batch_size == 50


class TestSettings:
    """Tests for main Settings class."""
    
    def test_default_settings(self):
        """Test creating settings with defaults."""
        settings = Settings()
        assert settings.app_name == "LOGReport"
        assert isinstance(settings.logging, LoggingConfig)
        assert isinstance(settings.network, NetworkConfig)
    
    def test_debug_mode(self, monkeypatch):
        """Test debug mode from environment."""
        monkeypatch.setenv("LOGREPORT_DEBUG", "true")
        settings = Settings()
        assert settings.debug is True
    
    def test_to_dict(self):
        """Test converting settings to dictionary."""
        settings = Settings()
        data = settings.to_dict()
        assert data["app_name"] == "LOGReport"
        assert "logging" in data
        assert "network" in data
    
    def test_from_dict(self):
        """Test creating settings from dictionary."""
        data = {
            "logging": {"level": "DEBUG"},
            "network": {"default_timeout": 60},
            "paths": {"log_root": "/custom/logs"},
        }
        settings = Settings.from_dict(data)
        assert settings.logging.level == "DEBUG"
        assert settings.network.default_timeout == 60
        assert settings.paths.log_root == Path("/custom/logs")
    
    def test_json_round_trip(self, tmp_path):
        """Test saving and loading settings from JSON."""
        settings = Settings()
        settings.logging.level = "DEBUG"
        
        json_path = tmp_path / "settings.json"
        settings.to_json_file(json_path)
        
        loaded = Settings.from_json_file(json_path)
        assert loaded.logging.level == "DEBUG"


class TestSettingsSingleton:
    """Tests for settings singleton functions."""
    
    def test_get_settings_returns_same_instance(self):
        """Test singleton behavior."""
        reset_settings()
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2
    
    def test_reset_settings(self):
        """Test resetting settings."""
        settings1 = get_settings()
        reset_settings()
        settings2 = get_settings()
        assert settings1 is not settings2
    
    def test_configure_settings(self):
        """Test setting custom settings."""
        custom = Settings()
        custom.app_name = "CustomApp"
        
        configure_settings(custom)
        
        settings = get_settings()
        assert settings.app_name == "CustomApp"
        
        # Clean up
        reset_settings()


class TestSettingsIntegration:
    """Integration tests for settings."""
    
    def test_full_configuration_flow(self, tmp_path, monkeypatch):
        """Test complete configuration flow."""
        # Set environment variables
        monkeypatch.setenv("LOGREPORT_DEBUG", "true")
        monkeypatch.setenv("LOGREPORT_LOG_LEVEL", "DEBUG")
        monkeypatch.setenv("LOGREPORT_NETWORK_TIMEOUT", "45")
        
        reset_settings()
        settings = get_settings()
        
        assert settings.debug is True
        assert settings.logging.level == "DEBUG"
        assert settings.network.default_timeout == 45
        
        # Convert to dict and verify
        data = settings.to_dict()
        assert data["debug"] is True
        
        # Clean up
        reset_settings()
