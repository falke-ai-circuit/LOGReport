"""
FBC Parser Service

Service for parsing .fbc and .rpc file content into structured table data.
Supports dual file type parsing with separate algorithms for FBC (I/O configuration)
and RPC (error counter) formats.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from pathlib import Path
import re
import logging


@dataclass
class FbcTableData:
    """Structured representation of FBC/RPC table content"""
    timestamp: str
    command: str
    agent_id: str
    file_type: str  # 'FBC' or 'RPC'
    headers: List[str]  # Column headers: ['PIC', '5', '6', ...] or ['pic', 'IREX ERROR', ...]
    rows: List[Dict[str, str]]  # List of row dictionaries: [{'PIC': '0', '5': 'AI8', ...}, ...]
    totals: Dict[str, Any] = field(default_factory=dict)  # Summary statistics
    raw_content: str = ""


class FbcParserService:
    """Service for parsing .fbc and .rpc file content"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Common patterns
        self.TIMESTAMP_PATTERN = re.compile(r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]')
        self.COMMAND_FBC_PATTERN = re.compile(r'print from fbc io structure (\d+)')
        self.COMMAND_RPC_PATTERN = re.compile(r'print from fbc rupi counters (\d+)')
        self.AGENT_PATTERN = re.compile(r'FBC agent (\d+)')
        
        # FBC-specific patterns (supports both PIC and IBC formats)
        self.FBC_HEADER_PATTERN = re.compile(r'\s*(PIC|IBC)\s+(.+?)\s*sum\s*$')
        # Changed: Single space \s between PIC and IO units preserves leading spaces for empty slot detection
        self.FBC_ROW_PATTERN = re.compile(r'^\s*(\d+)\s(.+)\s(\d+)\s*$')
        self.FBC_TOTAL_PATTERN = re.compile(r'Total sum:\s*(\d+)\s*I/O-units,\s*(\d+)\s*Channels\s*\((\d+)\s*input,\s*(\d+)\s*output\)')
        self.IO_UNIT_PATTERN = re.compile(r'([A-Z]{2,3}\d)N?')  # Matches AI8, BI8, BO8, TI6, AO4, etc.
        
        # RPC-specific patterns
        self.RPC_HEADER_PATTERN = re.compile(r'pic\s+IREX ERROR\s+POLL ERROR\s+RESP FAIL\s+IREX COUNT\s+TIMEOUT')
        self.RPC_ROW_PATTERN = re.compile(r'^\s*(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s*$')
        self.RPC_UNKNOWN_CMD_PATTERN = re.compile(r'Unknown command:\s+(\d+)')
    
    def parse_file(self, file_path: str) -> FbcTableData:
        """Parse .fbc or .rpc file and extract structured data"""
        try:
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # Detect file type from extension
            file_type = self._detect_file_type(file_path)
            
            # Read file content
            with open(file_path_obj, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return self.parse_content(content, file_type)
            
        except Exception as e:
            self.logger.error(f"Failed to parse file {file_path}: {e}")
            raise
    
    def parse_content(self, content: str, file_type: str = 'FBC') -> FbcTableData:
        """Parse FBC/RPC output string (from file or telnet)"""
        lines = content.split('\n')
        
        # Extract metadata from header
        timestamp = self._extract_timestamp(lines[0:5])
        command = self._extract_command(lines[0:10], file_type)
        agent_id = self._extract_agent(lines[0:15])
        
        if file_type == 'FBC':
            return self._parse_fbc_content(lines, timestamp, command, agent_id, content)
        elif file_type == 'RPC':
            return self._parse_rpc_content(lines, timestamp, command, agent_id, content)
        else:
            raise ValueError(f"Unknown file type: {file_type}")
    
    def _parse_fbc_content(self, lines: List[str], timestamp: str, command: str, agent_id: str, raw_content: str) -> FbcTableData:
        """Parse FBC file content (I/O configuration table)"""
        # Find table section - support both PIC and IBC formats
        table_start = self._find_line_matching(r'^\s*(PIC|IBC)\s+', lines)
        if table_start == -1:
            self.logger.warning("FBC table header not found (looked for PIC or IBC)")
            return FbcTableData(
                timestamp=timestamp,
                command=command,
                agent_id=agent_id,
                file_type='FBC',
                headers=[],
                rows=[],
                totals={},
                raw_content=raw_content
            )
        
        table_end = self._find_line_matching(r'^\s*Total sum:', lines)
        
        # Parse header row
        header_line = lines[table_start]
        headers = self._parse_fbc_header(header_line)
        
        # Determine data start line: Check if line after header is a separator or data
        # In telnet responses, data starts immediately (no separator)
        # In .fbc files, there's usually an empty line or dashes
        data_start_line = table_start + 1
        if table_start + 1 < len(lines):
            next_line = lines[table_start + 1].strip()
            # Check if next line is data (matches PIC row pattern OR "Not Exists") vs separator
            is_data_row = (next_line and 
                          (self.FBC_ROW_PATTERN.match(next_line) or 
                           'Not Exists' in next_line or 
                           'not exists' in next_line.lower()))
            
            if is_data_row:
                # Next line is data - start parsing from table_start + 1
                data_start_line = table_start + 1
                self.logger.debug(f"No separator detected - data starts at line {data_start_line}")
            else:
                # Next line is separator or empty - start from table_start + 2
                data_start_line = table_start + 2
                self.logger.debug(f"Separator detected at line {table_start + 1} - data starts at line {data_start_line}")
        
        # Parse data rows
        rows = []
        for i in range(data_start_line, table_end if table_end != -1 else len(lines)):
            line = lines[i].strip()
            if not line or line.startswith('---') or line.startswith('==='):
                continue
            
            row_data = self._parse_fbc_row(line, headers)
            if row_data:
                rows.append(row_data)
                self.logger.debug(f"Parsed row: PIC={row_data.get('PIC')}, sum={row_data.get('sum')}")
            else:
                self.logger.warning(f"Failed to parse row {i}: {repr(line)}")
        
        # Parse totals section
        totals = self._parse_fbc_totals(lines[table_end:] if table_end != -1 else [])
        
        return FbcTableData(
            timestamp=timestamp,
            command=command,
            agent_id=agent_id,
            file_type='FBC',
            headers=headers,
            rows=rows,
            totals=totals,
            raw_content=raw_content
        )
    
    def _parse_rpc_content(self, lines: List[str], timestamp: str, command: str, agent_id: str, raw_content: str) -> FbcTableData:
        """Parse RPC file content (error counter table)"""
        # Find RPC table section
        table_start = self._find_line_matching(r'pic\s+IREX ERROR', lines)
        if table_start == -1:
            self.logger.warning("RPC table header not found")
            return FbcTableData(
                timestamp=timestamp,
                command=command,
                agent_id=agent_id,
                file_type='RPC',
                headers=[],
                rows=[],
                totals={},
                raw_content=raw_content
            )
        
        table_end = self._find_line_matching(r'Unknown command:', lines)
        
        # Fixed RPC headers
        headers = ['pic', 'IREX ERROR', 'POLL ERROR', 'RESP FAIL', 'IREX COUNT', 'TIMEOUT']
        
        # Parse RPC data rows
        rows = []
        for i in range(table_start + 2, table_end if table_end != -1 else len(lines)):
            line = lines[i].strip()
            if not line or line.startswith('---') or line.startswith('==='):
                continue
            
            match = self.RPC_ROW_PATTERN.match(line)
            if match:
                row_data = {
                    'pic': match.group(1),
                    'IREX ERROR': match.group(2),
                    'POLL ERROR': match.group(3),
                    'RESP FAIL': match.group(4),
                    'IREX COUNT': match.group(5),
                    'TIMEOUT': match.group(6)
                }
                rows.append(row_data)
        
        # Parse unknown command count
        unknown_cmd = 0
        if table_end != -1:
            match = self.RPC_UNKNOWN_CMD_PATTERN.search(lines[table_end])
            if match:
                unknown_cmd = int(match.group(1))
        
        return FbcTableData(
            timestamp=timestamp,
            command=command,
            agent_id=agent_id,
            file_type='RPC',
            headers=headers,
            rows=rows,
            totals={'unknown_command': unknown_cmd},
            raw_content=raw_content
        )
    
    def _parse_fbc_header(self, header_line: str) -> List[str]:
        """Extract column headers from FBC table header line (supports PIC and IBC formats)"""
        # Match pattern: "PIC  5  6  7  8  ... sum" or "IBC  0  1  2  3  ... sum"
        match = self.FBC_HEADER_PATTERN.match(header_line)
        if match:
            # Extract column numbers
            columns_part = match.group(2)  # Changed from group(1) to group(2) since we added (PIC|IBC) capture
            column_numbers = re.findall(r'\d+', columns_part)
            return ['PIC'] + column_numbers + ['sum']  # Always use 'PIC' as key for consistency
        return ['PIC', 'sum']
    
    def _parse_fbc_row(self, line: str, headers: List[str]) -> Optional[Dict[str, str]]:
        """
        Parse a single FBC data row preserving empty slots and 'N' suffix.
        
        Format: "  PIC AI8 BI8 BO8 ... sum"
        Empty slots show as multiple spaces (4+ chars).
        I/O unit names can have 'N' suffix: BI8N, BO8N, etc.
        Sometimes units are concatenated: BI8NBI8 (no space between).
        "Not Exists" means hardware row is not used (display as N/E).
        """
        # Check for "Not Exists" rows
        if 'Not Exists' in line or 'not exists' in line.lower():
            # Extract PIC/IBC number from beginning of line
            pic_match = re.match(r'^\s*(\d+)\s+', line)
            if pic_match:
                pic_number = pic_match.group(1)
                # Create row with N/E in all card slots
                row_data = {'PIC': pic_number}
                for col_num in headers[1:-1]:  # Skip 'PIC' and 'sum'
                    row_data[col_num] = 'N/E'
                row_data['sum'] = '0'  # Not Exists means no units
                return row_data
            return None
        
        match = self.FBC_ROW_PATTERN.match(line)
        if not match:
            return None
        
        pic_number = match.group(1)
        io_units_str = match.group(2)
        sum_value = match.group(3)
        
        # Extract I/O units using enhanced regex that:
        # 1. Captures units with optional 'N' suffix: AI8, BI8N, etc. (PIC format)
        # 2. Captures units like Di16, Do16, Ai8 (IBC format - mixed case)
        # 3. Detects empty slots (4+ spaces)
        # Pattern: ([A-Z][a-z]?\d+N?) matches units (both PIC and IBC formats), (\s{4,}) matches empty slots
        io_units = []
        pattern = r'([A-Z][A-Za-z]\d+N?)|\s{4,}'
        
        for match_obj in re.finditer(pattern, io_units_str):
            if match_obj.group(1):
                # Valid I/O unit captured
                io_units.append(match_obj.group(1))
            else:
                # Empty slot (4+ spaces) - no card in that slot
                io_units.append('')
        
        # Build row dictionary
        row_data = {'PIC': pic_number}
        
        # Map I/O units to column numbers
        for i, col_num in enumerate(headers[1:-1]):  # Skip 'PIC' and 'sum'
            if i < len(io_units):
                row_data[col_num] = io_units[i]
            else:
                row_data[col_num] = ''
        
        row_data['sum'] = sum_value
        return row_data
    
    def _parse_fbc_totals(self, lines: List[str]) -> Dict[str, Any]:
        """Parse FBC totals section"""
        totals = {}
        
        for line in lines:
            # Total sum line
            match = self.FBC_TOTAL_PATTERN.search(line)
            if match:
                totals['total_units'] = int(match.group(1))
                totals['total_channels'] = int(match.group(2))
                totals['input_channels'] = int(match.group(3))
                totals['output_channels'] = int(match.group(4))
            
            # Unit breakdown (e.g., "AIU8: 15")
            unit_matches = re.findall(r'([A-Z]{3}\d):\s*(\d+)', line)
            if unit_matches:
                if 'unit_breakdown' not in totals:
                    totals['unit_breakdown'] = {}
                for unit_type, count in unit_matches:
                    totals['unit_breakdown'][unit_type] = int(count)
        
        return totals
    
    def _extract_timestamp(self, lines: List[str]) -> str:
        """Extract timestamp from header lines"""
        for line in lines:
            match = self.TIMESTAMP_PATTERN.search(line)
            if match:
                return match.group(1)
        return "Unknown"
    
    def _extract_command(self, lines: List[str], file_type: str) -> str:
        """Extract command from header lines"""
        pattern = self.COMMAND_FBC_PATTERN if file_type == 'FBC' else self.COMMAND_RPC_PATTERN
        for line in lines:
            match = pattern.search(line)
            if match:
                return line.strip()
        return "Unknown"
    
    def _extract_agent(self, lines: List[str]) -> str:
        """Extract agent ID from header lines"""
        for line in lines:
            match = self.AGENT_PATTERN.search(line)
            if match:
                return match.group(1)
        return "Unknown"
    
    def _find_line_matching(self, pattern: str, lines: List[str]) -> int:
        """Find first line matching regex pattern"""
        compiled_pattern = re.compile(pattern)
        for i, line in enumerate(lines):
            if compiled_pattern.search(line):
                return i
        return -1
    
    def _detect_file_type(self, file_path: str) -> str:
        """Determine file type from extension"""
        path = Path(file_path)
        ext = path.suffix.lower()
        
        if ext == '.fbc':
            return 'FBC'
        elif ext == '.rpc':
            return 'RPC'
        else:
            # Default to FBC if unknown
            self.logger.warning(f"Unknown file extension {ext}, defaulting to FBC")
            return 'FBC'
