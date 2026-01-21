"""
Token Preparation Service - Prepares tokens for command execution.

This module handles token normalization, validation, and preparation
for FBC and RPC command execution.

Usage:
    from commander.services.token_preparation_service import TokenPreparationService
    
    service = TokenPreparationService(node_manager)
    prepared_token = service.prepare_fbc_token(token_id, node_name, ip_address)
"""

import logging
import re
from typing import Optional, Tuple
from dataclasses import dataclass

from ..models import NodeToken
from ..interfaces import INodeRepository


@dataclass
class PreparedToken:
    """Result of token preparation."""
    token: NodeToken
    normalized_id: str
    is_valid: bool
    error_message: Optional[str] = None


class TokenPreparationService:
    """
    Prepares tokens for command execution.
    
    Handles token normalization, validation, and creation of
    properly configured NodeToken objects for FBC and RPC commands.
    
    Example:
        >>> service = TokenPreparationService(node_manager)
        >>> result = service.prepare_fbc_token("162", "AP01m", "192.168.1.1")
        >>> if result.is_valid:
        ...     execute_command(result.token)
    """
    
    def __init__(self, node_manager=None):
        """
        Initialize the token preparation service.
        
        Args:
            node_manager: Optional NodeManager for looking up existing tokens
        """
        self.node_manager = node_manager
        self.logger = logging.getLogger(__name__)
    
    def normalize_token_id(self, token_id: str, token_type: str = "FBC") -> str:
        """
        Normalize token ID according to protocol rules.
        
        Args:
            token_id: Raw token identifier
            token_type: Protocol type (FBC, RPC)
            
        Returns:
            Normalized token ID (e.g., "001", "162")
        """
        token_str = str(token_id).strip()
        
        if token_type in ("FBC", "RPC"):
            # Pad numeric tokens to 3 digits
            if token_str.isdigit():
                return token_str.zfill(3)
        
        return token_str
    
    def is_valid_ip(self, ip_address: str) -> bool:
        """
        Validate IP address format.
        
        Args:
            ip_address: IP address string to validate
            
        Returns:
            True if valid IPv4 address, False otherwise
        """
        if not ip_address:
            return False
        
        pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        if not re.match(pattern, ip_address):
            return False
        
        try:
            parts = [int(p) for p in ip_address.split('.')]
            return all(0 <= p <= 255 for p in parts)
        except ValueError:
            return False
    
    def get_base_node_name(self, node_name: str) -> str:
        """
        Extract base node name from full node name.
        
        Args:
            node_name: Full node name (may include spaces)
            
        Returns:
            Base node name (first word)
        """
        if " " in node_name:
            return node_name.split()[0]
        return node_name
    
    def prepare_fbc_token(self, token_id: str, node_name: str,
                         ip_address: str = "0.0.0.0") -> PreparedToken:
        """
        Prepare an FBC token for command execution.
        
        Args:
            token_id: Token identifier
            node_name: Node name
            ip_address: IP address of the node
            
        Returns:
            PreparedToken with normalized ID and ready-to-use token
        """
        normalized_id = self.normalize_token_id(token_id, "FBC")
        base_name = self.get_base_node_name(node_name)
        
        # Validate IP address
        valid_ip = ip_address if self.is_valid_ip(ip_address) else "0.0.0.0"
        
        # Try to find existing token from node manager
        if self.node_manager:
            node = self.node_manager.get_node(node_name)
            if node:
                # Try to find existing FBC token with matching ID
                token_formats = [token_id, str(int(token_id)) if token_id.isdigit() else token_id]
                for fmt in token_formats:
                    if tok := node.tokens.get(fmt):
                        if tok.token_type == "FBC":
                            return PreparedToken(
                                token=tok,
                                normalized_id=normalized_id,
                                is_valid=True
                            )
                # Use node's IP if available
                valid_ip = node.ip_address or valid_ip
        
        # Create new FBC token
        token = NodeToken(
            token_id=token_id,
            token_type="FBC",
            name=base_name,
            ip_address=valid_ip
        )
        
        return PreparedToken(
            token=token,
            normalized_id=normalized_id,
            is_valid=True
        )
    
    def prepare_rpc_token(self, token_id: str, node_name: str,
                         ip_address: str = "0.0.0.0", port: int = 23) -> PreparedToken:
        """
        Prepare an RPC token for command execution.
        
        Args:
            token_id: Token identifier
            node_name: Node name
            ip_address: IP address of the node
            port: Port number for RPC connection
            
        Returns:
            PreparedToken with normalized ID and ready-to-use token
        """
        normalized_id = self.normalize_token_id(token_id, "RPC")
        base_name = self.get_base_node_name(node_name)
        
        # Validate IP address
        valid_ip = ip_address if self.is_valid_ip(ip_address) else "0.0.0.0"
        
        # Try to get IP from node manager
        if self.node_manager:
            node = self.node_manager.get_node(node_name)
            if node:
                valid_ip = node.ip_address or valid_ip
        
        # Create RPC token
        token = NodeToken(
            token_id=token_id,
            token_type="RPC",
            name=base_name,
            ip_address=valid_ip,
            port=port,
            protocol="telnet"
        )
        
        return PreparedToken(
            token=token,
            normalized_id=normalized_id,
            is_valid=True
        )
    
    def prepare_token(self, token: NodeToken, node_name: str,
                     ip_address: str = "0.0.0.0") -> PreparedToken:
        """
        Prepare a token based on its type.
        
        Args:
            token: Token to prepare
            node_name: Node name
            ip_address: IP address of the node
            
        Returns:
            PreparedToken with normalized ID and ready-to-use token
        """
        token_ip = getattr(token, 'node_ip', None) or ip_address
        
        if token.token_type == "FBC":
            return self.prepare_fbc_token(token.token_id, node_name, token_ip)
        elif token.token_type == "RPC":
            return self.prepare_rpc_token(token.token_id, node_name, token_ip)
        else:
            return PreparedToken(
                token=token,
                normalized_id=token.token_id,
                is_valid=False,
                error_message=f"Unknown token type: {token.token_type}"
            )
