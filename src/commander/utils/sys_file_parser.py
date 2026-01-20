"""
SYS File Parser - Parses _sys configuration files to extract node tokens

The _sys file format contains hardware address mappings for Application Servers.
Format: ":e:hw:<hex_address>   <LID>   <config_file>"

Where:
- <hex_address> is a 3-digit hex value (e.g., 501, 5aa)
- <LID> is the Logical ID (e.g., AL01, AD01, AP01_main)
- <config_file> can be:
  - "-" (dash) for no config
  - "pxe:sys-csg2" for CSG2 config
  - "pxe:sys-csg3" for CSG3 config  
  - "pxe:sys-lite" for lite config
  - Other pxe:* variants
"""

import re
import os
import logging
from typing import List, Dict, Optional, Tuple, NamedTuple
from dataclasses import dataclass


class SysEntry(NamedTuple):
    """Represents a parsed entry from a _sys file"""
    hardware_address: str  # Hex address (e.g., "501", "5aa")
    lid: str               # Logical ID (e.g., "AL01", "AD01")
    config: str            # Configuration (e.g., "-", "pxe:sys-csg2")
    comment: str           # Optional trailing comment
    line_number: int       # Source line number for debugging


@dataclass
class SysFileInfo:
    """Information about a parsed _sys file"""
    file_path: str
    bus_unit: str  # Extracted from filename (e.g., "AB01" from "AB01_10.1_sys")
    entries: List[SysEntry]
    parse_errors: List[str]
    
    @property
    def token_count(self) -> int:
        return len(self.entries)
    
    def get_entries_by_type(self, lid_prefix: str) -> List[SysEntry]:
        """Get entries by LID prefix (e.g., 'AL' for LIS, 'AD' for DIA)"""
        return [e for e in self.entries if e.lid.startswith(lid_prefix)]
    
    def get_entry_by_lid(self, lid: str) -> Optional[SysEntry]:
        """Get a specific entry by LID"""
        for entry in self.entries:
            if entry.lid == lid:
                return entry
        return None


class SysFileParser:
    """
    Parser for _sys configuration files.
    
    Supports multiple configuration formats:
    - :e:hw:501   AL01   pxe:sys-csg2    // Comment
    - :e:hw:501   AL01   pxe:sys-csg3
    - :e:hw:501   AL01   pxe:sys-lite
    - :e:hw:501   AL01   -
    """
    
    # Pattern to match valid _sys entries
    # Format: :e:hw:<hex>   <LID>   <config>   [// comment]
    ENTRY_PATTERN = re.compile(
        r'^:e:hw:([0-9a-fA-F]{2,4})\s+'  # Hardware address (2-4 hex digits)
        r'(\w+)\s+'                       # LID (alphanumeric with underscores)
        r'([\w:\-]+)'                     # Config (pxe:*, or just -)
        r'(?:\s*//\s*(.*))?$'             # Optional comment
    )
    
    # Alternative pattern for entries with tabs and irregular spacing
    ENTRY_PATTERN_FLEXIBLE = re.compile(
        r'^:e:hw:([0-9a-fA-F]{2,4})'      # Hardware address
        r'[\s\t]+'                         # Any whitespace
        r'(\w+)'                           # LID
        r'[\s\t]+'                         # Any whitespace  
        r'([\w:\-]+)'                      # Config
        r'(?:[\s\t]*//[\s\t]*(.*))?'       # Optional comment
    )
    
    # Known LID prefixes and their node types
    LID_TYPE_MAPPING = {
        'AD': 'DIA',      # DIA nodes
        'BD': 'DIA',      # DIA nodes (B bus)
        'AC': 'CIS',      # CIS nodes
        'NW': 'NETWATCH', # NetWatch
        'AM': 'MAINT',    # Maintenance Server
        'AL': 'LIS',      # LIS nodes
        'AP': 'PCS',      # PCS nodes
        'A1O': 'OPS',     # OPS nodes
        'B1O': 'OPS',     # OPS nodes (B bus)
        'A1A': 'ALP',     # ALP nodes
        'B1A': 'ALP',     # ALP nodes (B bus)
        'INFO': 'HISTORY' # History Server
    }
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def parse_file(self, file_path: str) -> SysFileInfo:
        """
        Parse a _sys file and extract all valid entries.
        
        Args:
            file_path: Path to the _sys file
            
        Returns:
            SysFileInfo containing parsed entries and metadata
        """
        entries = []
        parse_errors = []
        bus_unit = self._extract_bus_unit(file_path)
        
        if not os.path.exists(file_path):
            self.logger.error(f"SYS file not found: {file_path}")
            parse_errors.append(f"File not found: {file_path}")
            return SysFileInfo(file_path, bus_unit, entries, parse_errors)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except Exception as e:
            self.logger.error(f"Error reading SYS file: {e}")
            parse_errors.append(f"Error reading file: {e}")
            return SysFileInfo(file_path, bus_unit, entries, parse_errors)
        
        for line_num, line in enumerate(lines, 1):
            # Skip empty lines
            line = line.rstrip('\n\r')
            if not line.strip():
                continue
                
            # Skip pure comment lines
            if line.strip().startswith('//'):
                continue
            
            # Try to parse the entry
            entry = self._parse_line(line, line_num)
            if entry:
                entries.append(entry)
                self.logger.debug(f"Parsed entry: {entry}")
            elif line.strip().startswith(':e:hw:'):
                # Log unparseable entries that look like they should be valid
                parse_errors.append(f"Line {line_num}: Could not parse '{line.strip()}'")
                self.logger.warning(f"Could not parse SYS entry at line {line_num}: {line}")
        
        self.logger.info(f"Parsed {len(entries)} entries from {file_path}")
        return SysFileInfo(file_path, bus_unit, entries, parse_errors)
    
    def _parse_line(self, line: str, line_num: int) -> Optional[SysEntry]:
        """
        Parse a single line from a _sys file.
        
        Args:
            line: The line to parse
            line_num: Line number for debugging
            
        Returns:
            SysEntry if valid, None otherwise
        """
        # Try the standard pattern first
        match = self.ENTRY_PATTERN.match(line.strip())
        if not match:
            # Try the flexible pattern for irregular spacing
            match = self.ENTRY_PATTERN_FLEXIBLE.match(line.strip())
        
        if match:
            hw_address = match.group(1).lower()
            lid = match.group(2)
            config = match.group(3)
            comment = match.group(4) or ""
            
            return SysEntry(
                hardware_address=hw_address,
                lid=lid,
                config=config,
                comment=comment.strip(),
                line_number=line_num
            )
        
        return None
    
    def _extract_bus_unit(self, file_path: str) -> str:
        """
        Extract bus unit identifier from filename.
        
        Args:
            file_path: Path to the _sys file
            
        Returns:
            Bus unit identifier (e.g., "AB01") or "UNKNOWN"
        """
        filename = os.path.basename(file_path)
        # Match patterns like AB01_10.1_sys, AB01_sys, etc.
        match = re.match(r'^([A-Z]{2}\d{2})', filename)
        if match:
            return match.group(1)
        return "UNKNOWN"
    
    def get_token_id_from_hardware_address(self, hw_address: str) -> str:
        """
        Convert hardware address to token ID format.
        
        Args:
            hw_address: Hex hardware address (e.g., "501", "5aa")
            
        Returns:
            Token ID (normalized hex string)
        """
        # Normalize to lowercase and ensure 3 digits
        return hw_address.lower().zfill(3)
    
    def get_node_type_from_lid(self, lid: str) -> str:
        """
        Determine node type from LID prefix.
        
        Args:
            lid: Logical ID (e.g., "AL01", "AP01_main")
            
        Returns:
            Node type string or "UNKNOWN"
        """
        # Check for exact matches first (like INFO)
        if lid in self.LID_TYPE_MAPPING:
            return self.LID_TYPE_MAPPING[lid]
        
        # Check prefixes (longest match first)
        for prefix in sorted(self.LID_TYPE_MAPPING.keys(), key=len, reverse=True):
            if lid.startswith(prefix):
                return self.LID_TYPE_MAPPING[prefix]
        
        return "UNKNOWN"
    
    def entries_to_tokens(self, entries: List[SysEntry]) -> List[Dict]:
        """
        Convert SysEntry list to token data format compatible with NodeManager.
        
        Args:
            entries: List of SysEntry objects
            
        Returns:
            List of token dictionaries
        """
        tokens = []
        for entry in entries:
            token_data = {
                'token_id': self.get_token_id_from_hardware_address(entry.hardware_address),
                'lid': entry.lid,
                'config': entry.config,
                'token_type': self.get_node_type_from_lid(entry.lid),
                'port': 23,  # Default telnet port
                'protocol': 'telnet'
            }
            tokens.append(token_data)
        return tokens


# Singleton instance for global use
sys_file_parser = SysFileParser()


def parse_sys_file(file_path: str) -> SysFileInfo:
    """
    Parse a _sys file using the singleton parser.
    
    Args:
        file_path: Path to the _sys file
        
    Returns:
        SysFileInfo containing parsed entries
    """
    return sys_file_parser.parse_file(file_path)


def get_tokens_from_sys_file(file_path: str) -> List[Dict]:
    """
    Parse a _sys file and return token data.
    
    Args:
        file_path: Path to the _sys file
        
    Returns:
        List of token dictionaries
    """
    info = sys_file_parser.parse_file(file_path)
    return sys_file_parser.entries_to_tokens(info.entries)
