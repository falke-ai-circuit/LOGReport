"""
Command Generator - Generates protocol-specific commands for token execution.

This module handles command generation for FBC and RPC protocols,
following the protocol-specific formatting rules.

Usage:
    from commander.services.command_generator import CommandGenerator
    
    generator = CommandGenerator()
    command = generator.generate_fbc_command("162", "print")
"""

import logging
from typing import Dict, Optional
from dataclasses import dataclass
from enum import Enum


class CommandAction(Enum):
    """Supported command actions."""
    PRINT = "print"
    CLEAR = "clear"


@dataclass
class GeneratedCommand:
    """Result of command generation."""
    command: str
    action: CommandAction
    token_id: str
    protocol: str
    is_valid: bool
    error_message: Optional[str] = None


class CommandGenerator:
    """
    Generates protocol-specific commands for token execution.
    
    Supports FBC and RPC protocols with various actions like
    print and clear.
    
    Example:
        >>> generator = CommandGenerator()
        >>> result = generator.generate_fbc_command("162", "print")
        >>> print(result.command)  # "print from fbc io structure 1620000"
    """
    
    # Command templates for each protocol and action
    FBC_TEMPLATES: Dict[str, str] = {
        "print": "print from fbc io structure {token}0000",
        "clear": "clear fbc io structure {token}0000",
    }
    
    RPC_TEMPLATES: Dict[str, str] = {
        "print": "print from fbc rupi counters {token}0000",
        "clear": "clear fbc rupi counters {token}0000",
    }
    
    def __init__(self):
        """Initialize the command generator."""
        self.logger = logging.getLogger(__name__)
    
    def normalize_token_id(self, token_id: str) -> str:
        """
        Normalize token ID to standard format.
        
        Args:
            token_id: Raw token identifier
            
        Returns:
            Normalized token ID (3 digits if numeric)
        """
        token_str = str(token_id).strip()
        if token_str.isdigit():
            return token_str.zfill(3)
        return token_str
    
    def generate_fbc_command(self, token_id: str,
                            action: str = "print") -> GeneratedCommand:
        """
        Generate an FBC protocol command.
        
        Args:
            token_id: Token identifier
            action: Command action (print, clear)
            
        Returns:
            GeneratedCommand with the formatted command string
        """
        normalized_id = self.normalize_token_id(token_id)
        
        if action not in self.FBC_TEMPLATES:
            return GeneratedCommand(
                command="",
                action=CommandAction.PRINT,
                token_id=token_id,
                protocol="FBC",
                is_valid=False,
                error_message=f"Unknown action: {action}"
            )
        
        template = self.FBC_TEMPLATES[action]
        command = template.format(token=normalized_id)
        
        return GeneratedCommand(
            command=command,
            action=CommandAction(action),
            token_id=token_id,
            protocol="FBC",
            is_valid=True
        )
    
    def generate_rpc_command(self, token_id: str,
                            action: str = "print") -> GeneratedCommand:
        """
        Generate an RPC protocol command.
        
        Args:
            token_id: Token identifier
            action: Command action (print, clear)
            
        Returns:
            GeneratedCommand with the formatted command string
        """
        normalized_id = self.normalize_token_id(token_id)
        
        if action not in self.RPC_TEMPLATES:
            return GeneratedCommand(
                command="",
                action=CommandAction.PRINT,
                token_id=token_id,
                protocol="RPC",
                is_valid=False,
                error_message=f"Unknown action: {action}"
            )
        
        template = self.RPC_TEMPLATES[action]
        command = template.format(token=normalized_id)
        
        return GeneratedCommand(
            command=command,
            action=CommandAction(action),
            token_id=token_id,
            protocol="RPC",
            is_valid=True
        )
    
    def generate_command(self, token_id: str, protocol: str,
                        action: str = "print") -> GeneratedCommand:
        """
        Generate a command based on protocol type.
        
        Args:
            token_id: Token identifier
            protocol: Protocol type (FBC, RPC)
            action: Command action (print, clear)
            
        Returns:
            GeneratedCommand with the formatted command string
        """
        protocol_upper = protocol.upper()
        
        if protocol_upper == "FBC":
            return self.generate_fbc_command(token_id, action)
        elif protocol_upper == "RPC":
            return self.generate_rpc_command(token_id, action)
        else:
            return GeneratedCommand(
                command="",
                action=CommandAction.PRINT,
                token_id=token_id,
                protocol=protocol,
                is_valid=False,
                error_message=f"Unknown protocol: {protocol}"
            )
