"""
Node Configuration Repository - Handles file I/O for node configurations.

This module provides a clean interface for loading and saving node
configurations from JSON files.

Usage:
    from commander.repositories import NodeConfigRepository
    
    repo = NodeConfigRepository("nodes.json")
    nodes = repo.load()
    repo.save(nodes)
"""

import json
import logging
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class NodeConfigData:
    """
    Represents node configuration data.
    
    Attributes:
        name: Node name
        ip: IP address
        tokens: List of token IDs
        types: List of token types (FBC, RPC, etc.)
    """
    name: str
    ip: str = ""
    tokens: List[str] = field(default_factory=list)
    types: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "ip": self.ip,
            "tokens": self.tokens,
            "types": self.types
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NodeConfigData':
        """Create from dictionary."""
        return cls(
            name=data.get("name", ""),
            ip=data.get("ip", ""),
            tokens=data.get("tokens", []),
            types=data.get("types", [])
        )


class NodeConfigRepository:
    """
    Repository for node configuration persistence.
    
    Handles loading and saving node configurations to JSON files,
    with support for both old and new configuration formats.
    
    Example:
        >>> repo = NodeConfigRepository("nodes.json")
        >>> nodes = repo.load()
        >>> nodes.append(NodeConfigData(name="AP01m", ip="192.168.1.1"))
        >>> repo.save(nodes)
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the repository.
        
        Args:
            config_path: Path to the configuration file.
                        If None, uses default location.
        """
        self.logger = logging.getLogger(__name__)
        
        if config_path:
            self.config_path = Path(config_path)
        else:
            # Default path relative to src directory
            src_dir = Path(__file__).parent.parent.parent
            self.config_path = src_dir / "nodes.json"
    
    def load(self) -> List[NodeConfigData]:
        """
        Load node configurations from file.
        
        Returns:
            List of NodeConfigData objects
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            json.JSONDecodeError: If config file is invalid JSON
        """
        if not self.config_path.exists():
            self.logger.warning(f"Config file not found: {self.config_path}")
            return []
        
        with open(self.config_path, 'r') as f:
            raw_data = json.load(f)
        
        nodes = []
        for node in raw_data:
            converted = self._convert_from_file_format(node)
            nodes.append(NodeConfigData.from_dict(converted))
        
        self.logger.info(f"Loaded {len(nodes)} nodes from {self.config_path}")
        return nodes
    
    def save(self, nodes: List[NodeConfigData]) -> None:
        """
        Save node configurations to file.
        
        Args:
            nodes: List of NodeConfigData objects to save
        """
        # Convert to new format for saving
        output_data = []
        for node in nodes:
            output_data.append(self._convert_to_file_format(node))
        
        with open(self.config_path, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        self.logger.info(f"Saved {len(nodes)} nodes to {self.config_path}")
    
    def load_from_path(self, path: str) -> List[NodeConfigData]:
        """
        Load node configurations from a specific path.
        
        Args:
            path: Path to the configuration file
            
        Returns:
            List of NodeConfigData objects
        """
        original_path = self.config_path
        self.config_path = Path(path)
        try:
            return self.load()
        finally:
            self.config_path = original_path
    
    def save_to_path(self, nodes: List[NodeConfigData], path: str) -> None:
        """
        Save node configurations to a specific path.
        
        Args:
            nodes: List of NodeConfigData objects
            path: Path to save to
        """
        original_path = self.config_path
        self.config_path = Path(path)
        try:
            self.save(nodes)
        finally:
            self.config_path = original_path
    
    def _convert_from_file_format(self, node: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert from file format to internal format.
        
        Handles both old format (simple tokens list) and new format
        (detailed token objects with ip_address).
        """
        if "ip_address" in node:
            # New format - transform to internal format
            token_ids = []
            types = set()
            
            for token_obj in node.get("tokens", []):
                token_id = token_obj.get("token_id")
                token_type = token_obj.get("token_type")
                
                if token_id and token_id not in token_ids and token_id != "default_lis_token":
                    token_ids.append(token_id)
                
                if token_type:
                    types.add(token_type)
            
            return {
                "name": node.get("name", ""),
                "ip": node.get("ip_address", ""),
                "tokens": token_ids,
                "types": list(types)
            }
        else:
            # Old format - use as is
            return node
    
    def _convert_to_file_format(self, node: NodeConfigData) -> Dict[str, Any]:
        """
        Convert from internal format to file format.
        
        Produces the new format with detailed token objects.
        """
        tokens = []
        for token_id in node.tokens:
            for token_type in node.types:
                tokens.append({
                    "token_id": token_id,
                    "token_type": token_type,
                    "ip_address": node.ip
                })
        
        return {
            "name": node.name,
            "ip_address": node.ip,
            "tokens": tokens
        }
    
    def exists(self) -> bool:
        """Check if config file exists."""
        return self.config_path.exists()
