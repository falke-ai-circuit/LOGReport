"""
Node Manager Facade - Clean interface for node management operations.

This module provides a simplified interface to the NodeManager,
following the Facade pattern to reduce complexity.

Usage:
    from commander.services.node_manager_facade import NodeManagerFacade
    
    facade = NodeManagerFacade(node_manager)
    nodes = facade.get_all_nodes()
    node = facade.get_node("AP01m")
"""

import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field

from ..models import NodeToken


@dataclass
class NodeInfo:
    """
    Simplified node information for external use.
    
    Provides a clean interface to node data without exposing
    internal implementation details.
    """
    name: str
    ip_address: str
    tokens: List[str] = field(default_factory=list)
    token_types: List[str] = field(default_factory=list)
    is_valid: bool = True
    
    def has_token(self, token_id: str) -> bool:
        """Check if node has a specific token."""
        return token_id in self.tokens
    
    def has_token_type(self, token_type: str) -> bool:
        """Check if node has a specific token type."""
        return token_type in self.token_types


class NodeManagerFacade:
    """
    Facade for NodeManager operations.
    
    Provides a simplified, clean interface to the NodeManager,
    hiding implementation details and reducing coupling.
    
    Example:
        >>> facade = NodeManagerFacade(node_manager)
        >>> nodes = facade.get_all_node_names()
        >>> node = facade.get_node_info("AP01m")
    """
    
    def __init__(self, node_manager=None):
        """
        Initialize the facade.
        
        Args:
            node_manager: NodeManager instance to wrap
        """
        self._node_manager = node_manager
        self._logger = logging.getLogger(__name__)
    
    @property
    def node_manager(self):
        """Get the underlying node manager."""
        return self._node_manager
    
    @node_manager.setter
    def node_manager(self, value):
        """Set the underlying node manager."""
        self._node_manager = value
    
    def get_all_node_names(self) -> List[str]:
        """
        Get names of all configured nodes.
        
        Returns:
            List of node names
        """
        if not self._node_manager:
            return []
        
        try:
            nodes = self._node_manager.get_nodes()
            return list(nodes.keys()) if nodes else []
        except Exception as e:
            self._logger.error(f"Error getting node names: {e}")
            return []
    
    def get_node_info(self, node_name: str) -> Optional[NodeInfo]:
        """
        Get information about a specific node.
        
        Args:
            node_name: Name of the node
            
        Returns:
            NodeInfo object or None if node not found
        """
        if not self._node_manager:
            return None
        
        try:
            node = self._node_manager.get_node(node_name)
            if not node:
                return None
            
            # Extract token information
            tokens = []
            token_types = set()
            
            if hasattr(node, 'tokens') and node.tokens:
                for token_id, token in node.tokens.items():
                    tokens.append(token_id)
                    if hasattr(token, 'token_type'):
                        token_types.add(token.token_type)
            
            return NodeInfo(
                name=node.name if hasattr(node, 'name') else node_name,
                ip_address=node.ip_address if hasattr(node, 'ip_address') else "",
                tokens=tokens,
                token_types=list(token_types)
            )
        except Exception as e:
            self._logger.error(f"Error getting node info for {node_name}: {e}")
            return None
    
    def get_all_nodes(self) -> List[NodeInfo]:
        """
        Get information about all configured nodes.
        
        Returns:
            List of NodeInfo objects
        """
        names = self.get_all_node_names()
        nodes = []
        
        for name in names:
            info = self.get_node_info(name)
            if info:
                nodes.append(info)
        
        return nodes
    
    def get_node_ip(self, node_name: str) -> Optional[str]:
        """
        Get the IP address for a specific node.
        
        Args:
            node_name: Name of the node
            
        Returns:
            IP address string or None if not found
        """
        info = self.get_node_info(node_name)
        return info.ip_address if info else None
    
    def get_node_tokens(self, node_name: str, token_type: Optional[str] = None) -> List[str]:
        """
        Get token IDs for a specific node.
        
        Args:
            node_name: Name of the node
            token_type: Optional filter by token type
            
        Returns:
            List of token IDs
        """
        if not self._node_manager:
            return []
        
        try:
            node = self._node_manager.get_node(node_name)
            if not node or not hasattr(node, 'tokens'):
                return []
            
            tokens = []
            for token_id, token in node.tokens.items():
                if token_type:
                    if hasattr(token, 'token_type') and token.token_type == token_type:
                        tokens.append(token_id)
                else:
                    tokens.append(token_id)
            
            return tokens
        except Exception as e:
            self._logger.error(f"Error getting tokens for {node_name}: {e}")
            return []
    
    def node_exists(self, node_name: str) -> bool:
        """
        Check if a node exists.
        
        Args:
            node_name: Name of the node
            
        Returns:
            True if node exists, False otherwise
        """
        if not self._node_manager:
            return False
        
        node = self._node_manager.get_node(node_name)
        return node is not None
    
    def get_node_count(self) -> int:
        """
        Get the total number of configured nodes.
        
        Returns:
            Number of nodes
        """
        return len(self.get_all_node_names())
    
    def reload_configuration(self) -> bool:
        """
        Reload node configuration from file.
        
        Returns:
            True if reload successful, False otherwise
        """
        if not self._node_manager:
            return False
        
        try:
            if hasattr(self._node_manager, 'load_config'):
                self._node_manager.load_config()
            elif hasattr(self._node_manager, 'load_nodes'):
                self._node_manager.load_nodes()
            return True
        except Exception as e:
            self._logger.error(f"Error reloading configuration: {e}")
            return False
