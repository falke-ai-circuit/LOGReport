"""
Log Path Service - Generates consistent log file paths

This service provides centralized path generation for log files, ensuring
consistent naming conventions and directory structure across the application.

Usage:
    from commander.services.log_path_service import LogPathService
    
    service = LogPathService(root_path="/var/logs")
    path = service.get_log_path(token, node_name="AP01")
"""

import os
import re
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, Protocol

from ..models import NodeToken


@dataclass
class LogPathConfig:
    """Configuration for log path generation."""
    
    root: Path = field(default_factory=lambda: Path("test_logs"))
    include_node_name: bool = True
    include_ip_prefix: bool = True
    include_timestamp: bool = False
    create_directories: bool = True
    
    # File naming patterns
    date_format: str = "%Y%m%d"
    time_format: str = "%H%M%S"
    timestamp_separator: str = "_"
    
    def __post_init__(self) -> None:
        """Ensure root is a Path object."""
        if isinstance(self.root, str):
            self.root = Path(self.root)


class ILogPathService(Protocol):
    """Interface for log path generation services."""
    
    def get_log_path(
        self,
        token: NodeToken,
        node_name: str,
        action: str = "print"
    ) -> Path:
        """Generate log file path for a token."""
        ...
    
    def get_log_directory(
        self,
        protocol: str,
        node_name: Optional[str] = None
    ) -> Path:
        """Get directory for log files."""
        ...


class LogPathService:
    """
    Service for generating consistent log file paths.
    
    This service centralizes all log path generation logic, ensuring
    consistent naming conventions and directory structure.
    
    Attributes:
        config: Configuration for path generation
        logger: Logger instance for this service
    
    Example:
        >>> config = LogPathConfig(root=Path("/logs"))
        >>> service = LogPathService(config)
        >>> token = NodeToken("001", "FBC", "AP01", "192.168.1.1")
        >>> path = service.get_log_path(token, "AP01")
        >>> print(path)
        /logs/FBC/AP01/001.FBC
    """
    
    # Protocol directory mapping
    PROTOCOL_DIRS = {
        "FBC": "FBC",
        "RPC": "RPC",
        "LOG": "LOG",
        "LIS": "LIS",
    }
    
    # File extensions by protocol
    PROTOCOL_EXTENSIONS = {
        "FBC": ".FBC",
        "RPC": ".RPC",
        "LOG": ".log",
        "LIS": ".LIS",
    }
    
    def __init__(self, config: Optional[LogPathConfig] = None) -> None:
        """
        Initialize the log path service.
        
        Args:
            config: Configuration for path generation. Uses defaults if not provided.
        """
        self.config = config or LogPathConfig()
        self.logger = logging.getLogger(__name__)
        
        # Ensure root directory exists
        if self.config.create_directories:
            self.config.root.mkdir(parents=True, exist_ok=True)
    
    def get_log_path(
        self,
        token: NodeToken,
        node_name: str,
        action: str = "print"
    ) -> Path:
        """
        Generate the log file path for a token.
        
        This method generates a consistent path for log files based on
        the token type, node name, and configuration settings.
        
        Args:
            token: The node token to generate a path for
            node_name: Name of the node containing the token
            action: Action being performed (print, compare, etc.)
        
        Returns:
            Path object for the log file
        
        Example:
            >>> token = NodeToken("001", "FBC", "AP01", "192.168.1.1")
            >>> path = service.get_log_path(token, "AP01")
            >>> print(path)
            /logs/FBC/AP01/001.FBC
        """
        # Get the protocol directory
        protocol = token.token_type.upper()
        protocol_dir = self.PROTOCOL_DIRS.get(protocol, protocol)
        
        # Build the directory path
        directory = self.get_log_directory(protocol, node_name)
        
        # Generate the filename
        filename = self._generate_filename(token, node_name, protocol)
        
        return directory / filename
    
    def get_log_directory(
        self,
        protocol: str,
        node_name: Optional[str] = None
    ) -> Path:
        """
        Get the directory for log files.
        
        Args:
            protocol: Protocol type (FBC, RPC, etc.)
            node_name: Optional node name for subdirectory
        
        Returns:
            Path object for the directory
        """
        protocol_dir = self.PROTOCOL_DIRS.get(protocol.upper(), protocol.upper())
        
        # Build path components
        parts = [self.config.root, protocol_dir]
        
        if self.config.include_node_name and node_name:
            # Sanitize node name for use in path
            safe_node_name = self._sanitize_path_component(node_name)
            parts.append(safe_node_name)
        
        directory = Path(*parts)
        
        # Create directory if needed
        if self.config.create_directories:
            directory.mkdir(parents=True, exist_ok=True)
        
        return directory
    
    def _generate_filename(
        self,
        token: NodeToken,
        node_name: str,
        protocol: str
    ) -> str:
        """
        Generate the filename for a log file.
        
        Args:
            token: The token to generate a filename for
            node_name: Name of the node
            protocol: Protocol type
        
        Returns:
            Filename string
        """
        parts = []
        
        # Add IP prefix if configured
        if self.config.include_ip_prefix and token.ip_address:
            ip_safe = token.ip_address.replace(".", "-")
            parts.append(ip_safe)
        
        # Add token ID
        token_id = self._normalize_token_id(token.token_id, protocol)
        parts.append(token_id)
        
        # Add timestamp if configured
        if self.config.include_timestamp:
            timestamp = datetime.now().strftime(
                f"{self.config.date_format}{self.config.timestamp_separator}{self.config.time_format}"
            )
            parts.append(timestamp)
        
        # Join parts with underscore
        base_name = "_".join(parts) if len(parts) > 1 else parts[0]
        
        # Add extension
        extension = self.PROTOCOL_EXTENSIONS.get(protocol, f".{protocol}")
        
        return f"{base_name}{extension}"
    
    def _normalize_token_id(self, token_id: str, protocol: str) -> str:
        """
        Normalize a token ID for use in a filename.
        
        Args:
            token_id: Raw token ID
            protocol: Protocol type
        
        Returns:
            Normalized token ID
        """
        token_str = str(token_id).strip()
        
        # For FBC and RPC, pad numeric tokens to 3 digits
        if protocol in ("FBC", "RPC") and token_str.isdigit():
            return token_str.zfill(3)
        
        return token_str
    
    def _sanitize_path_component(self, name: str) -> str:
        """
        Sanitize a string for use as a path component.
        
        Args:
            name: Raw name string
        
        Returns:
            Sanitized name safe for use in file paths
        """
        # Remove or replace invalid characters
        safe_name = re.sub(r'[<>:"/\\|?*]', '_', name)
        # Remove leading/trailing whitespace and dots
        safe_name = safe_name.strip('. ')
        # Limit length
        max_length = 255
        if len(safe_name) > max_length:
            safe_name = safe_name[:max_length]
        
        return safe_name or "unnamed"
    
    def validate_path(self, path: Path) -> bool:
        """
        Validate that a path is within the configured root.
        
        This is a security measure to prevent path traversal attacks.
        
        Args:
            path: Path to validate
        
        Returns:
            True if path is valid and within root
        """
        try:
            # Resolve both paths to absolute
            resolved_path = path.resolve()
            resolved_root = self.config.root.resolve()
            
            # Check if path is under root
            return str(resolved_path).startswith(str(resolved_root))
        except (OSError, ValueError):
            return False
    
    def get_existing_logs(
        self,
        protocol: str,
        node_name: Optional[str] = None
    ) -> list[Path]:
        """
        Get list of existing log files.
        
        Args:
            protocol: Protocol type to search for
            node_name: Optional node name to filter by
        
        Returns:
            List of paths to existing log files
        """
        directory = self.get_log_directory(protocol, node_name)
        
        if not directory.exists():
            return []
        
        extension = self.PROTOCOL_EXTENSIONS.get(protocol.upper(), f".{protocol}")
        pattern = f"*{extension}"
        
        return list(directory.glob(pattern))
    
    def cleanup_old_logs(
        self,
        max_age_days: int = 30,
        dry_run: bool = True
    ) -> list[Path]:
        """
        Clean up old log files.
        
        Args:
            max_age_days: Maximum age of log files to keep
            dry_run: If True, only return files that would be deleted
        
        Returns:
            List of paths to deleted (or would-be-deleted) files
        """
        import time
        
        now = time.time()
        max_age_seconds = max_age_days * 24 * 60 * 60
        
        files_to_delete = []
        
        for protocol in self.PROTOCOL_DIRS.values():
            protocol_dir = self.config.root / protocol
            if not protocol_dir.exists():
                continue
            
            for log_file in protocol_dir.rglob("*"):
                if not log_file.is_file():
                    continue
                
                try:
                    file_age = now - log_file.stat().st_mtime
                    if file_age > max_age_seconds:
                        files_to_delete.append(log_file)
                        if not dry_run:
                            log_file.unlink()
                            self.logger.info(f"Deleted old log: {log_file}")
                except OSError as e:
                    self.logger.warning(f"Could not process {log_file}: {e}")
        
        return files_to_delete


# Singleton instance for global use
_default_service: Optional[LogPathService] = None


def get_log_path_service(config: Optional[LogPathConfig] = None) -> LogPathService:
    """
    Get the default log path service instance.
    
    Args:
        config: Optional configuration to use if creating new instance
    
    Returns:
        LogPathService instance
    """
    global _default_service
    
    if _default_service is None or config is not None:
        _default_service = LogPathService(config)
    
    return _default_service
