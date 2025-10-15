"""
FBC Comparison Service

Service for comparing file-based FBC/RPC data with live telnet responses.
Executes telnet commands, parses responses, and performs cell-by-cell comparison
to identify matches, differences, and errors.

Phase 3 Implementation - Live Comparison & Auto-Refresh
"""

from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
import logging
import re

from ..services.fbc_parser_service import FbcParserService, FbcTableData


@dataclass
class CellDifference:
    """Represents a single cell difference between file and live data"""
    row: int
    col: int
    file_value: str
    live_value: str


@dataclass
class CellError:
    """Represents an error in cell comparison"""
    row: int
    col: int
    error_message: str


@dataclass
class ComparisonResult:
    """Result of comparing file data with live telnet response"""
    success: bool
    file_type: str  # 'FBC' or 'RPC'
    match_percentage: float
    total_cells: int
    matches: List[Tuple[int, int]]  # List of (row, col) for matching cells
    differences: List[CellDifference]  # List of cell differences
    errors: List[CellError]  # List of cell errors
    error_message: Optional[str] = None  # Overall comparison error (telnet/parse failure)
    
    def to_dict(self) -> dict:
        """Convert to dictionary format for UI consumption"""
        return {
            'success': self.success,
            'file_type': self.file_type,
            'match_percentage': self.match_percentage,
            'total_cells': self.total_cells,
            'matches': self.matches,
            'differences': [
                (d.row, d.col, d.file_value, d.live_value) 
                for d in self.differences
            ],
            'errors': [
                (e.row, e.col, e.error_message) 
                for e in self.errors
            ],
            'error_message': self.error_message
        }


class FbcComparisonService:
    """Service for comparing file data with live telnet responses"""
    
    def __init__(self, telnet_service, fbc_parser_service: Optional[FbcParserService] = None):
        """
        Initialize comparison service.
        
        Args:
            telnet_service: TelnetService instance for command execution
            fbc_parser_service: Optional FbcParserService instance (creates new if None)
        """
        self.telnet_service = telnet_service
        self.fbc_parser = fbc_parser_service or FbcParserService()
        self.logger = logging.getLogger(__name__)
    
    def compare_with_live(
        self, 
        node_name: str, 
        token_id: str, 
        file_data: FbcTableData
    ) -> ComparisonResult:
        """
        Compare file data with live telnet response.
        
        Args:
            node_name: Node name for telnet connection
            token_id: Token ID (3-digit format: '001', '045', etc.)
            file_data: Parsed file data from FbcParserService
            
        Returns:
            ComparisonResult with matches, differences, errors, and match percentage
        """
        self.logger.info(f"Starting comparison for node {node_name}, token {token_id}, type {file_data.file_type}")
        
        try:
            # Step 1: Execute telnet command
            telnet_response = self._execute_telnet_command(node_name, token_id, file_data.file_type)
            
            # Check for telnet errors
            if telnet_response.startswith("Error:") or telnet_response.startswith("ERROR:"):
                return ComparisonResult(
                    success=False,
                    file_type=file_data.file_type,
                    match_percentage=0.0,
                    total_cells=0,
                    matches=[],
                    differences=[],
                    errors=[],
                    error_message=f"Telnet command failed: {telnet_response}"
                )
            
            # Step 2: Parse telnet response
            live_data = self._parse_telnet_response(telnet_response, file_data.file_type)
            
            if not live_data:
                return ComparisonResult(
                    success=False,
                    file_type=file_data.file_type,
                    match_percentage=0.0,
                    total_cells=0,
                    matches=[],
                    differences=[],
                    errors=[],
                    error_message="Failed to parse telnet response"
                )
            
            # Step 3: Compare tables
            comparison = self._compare_tables(file_data, live_data)
            
            return comparison
            
        except ConnectionError as e:
            self.logger.error(f"Connection error during comparison: {e}")
            return ComparisonResult(
                success=False,
                file_type=file_data.file_type,
                match_percentage=0.0,
                total_cells=0,
                matches=[],
                differences=[],
                errors=[],
                error_message=f"Connection error: {str(e)}"
            )
        except Exception as e:
            self.logger.error(f"Unexpected error during comparison: {e}", exc_info=True)
            return ComparisonResult(
                success=False,
                file_type=file_data.file_type,
                match_percentage=0.0,
                total_cells=0,
                matches=[],
                differences=[],
                errors=[],
                error_message=f"Comparison failed: {str(e)}"
            )
    
    def _execute_telnet_command(self, node_name: str, token_id: str, file_type: str) -> str:
        """
        Execute telnet command to retrieve live data.
        
        Args:
            node_name: Node name for logging
            token_id: Token ID (3-digit format)
            file_type: 'FBC' or 'RPC'
            
        Returns:
            Raw telnet response string
            
        Raises:
            ConnectionError: If telnet connection fails
        """
        self.logger.debug(f"Executing telnet command for {file_type} token {token_id}")
        
        # Ensure debugger connection is established
        if not self.telnet_service._ensure_debugger_connection():
            raise ConnectionError("Failed to establish debugger connection")
        
        # Normalize token to 3-digit format
        normalized_token = str(token_id).zfill(3) if token_id.isdigit() else token_id
        
        # Generate command based on file type
        if file_type == 'FBC':
            command = f"print from fbc io structure {normalized_token}0000"
        elif file_type == 'RPC':
            command = f"print from fbc rupi counters {normalized_token}0000"
        else:
            raise ValueError(f"Unknown file type: {file_type}")
        
        self.logger.debug(f"Generated command: {command}")
        
        # Execute command via telnet session
        try:
            response = self.telnet_service.telnet_session.send_command(command, timeout=5.0)
            self.logger.debug(f"Received response length: {len(response)} characters")
            return response
        except Exception as e:
            self.logger.error(f"Telnet command execution failed: {e}")
            raise ConnectionError(f"Telnet command failed: {str(e)}")
    
    def _parse_telnet_response(self, response: str, file_type: str) -> Optional[FbcTableData]:
        """
        Parse telnet response using FbcParserService.
        
        Args:
            response: Raw telnet response
            file_type: 'FBC' or 'RPC'
            
        Returns:
            FbcTableData if parsing succeeds, None otherwise
        """
        self.logger.debug(f"Parsing telnet response as {file_type}")
        
        try:
            # Use FbcParserService.parse_content() for telnet responses
            live_data = self.fbc_parser.parse_content(response, file_type)
            
            if not live_data or not live_data.rows:
                self.logger.warning(f"Telnet response parsing returned empty data")
                return None
            
            self.logger.debug(f"Successfully parsed {len(live_data.rows)} rows with {len(live_data.headers)} columns")
            return live_data
            
        except Exception as e:
            self.logger.error(f"Failed to parse telnet response: {e}", exc_info=True)
            return None
    
    def _compare_tables(self, file_data: FbcTableData, live_data: FbcTableData) -> ComparisonResult:
        """
        Compare file data with live data cell-by-cell.
        
        Compares rows by matching PIC values (not by row index) to handle cases where
        telnet response has extra header lines. Compares only data columns (PIC to sum).
        
        Args:
            file_data: Parsed file table data
            live_data: Parsed live table data
            
        Returns:
            ComparisonResult with detailed comparison statistics
        """
        self.logger.debug(f"Comparing tables: file has {len(file_data.rows)} rows, live has {len(live_data.rows)} rows")
        self.logger.debug(f"File headers: {file_data.headers}")
        self.logger.debug(f"Live headers: {live_data.headers}")
        
        matches: List[Tuple[int, int]] = []
        differences: List[CellDifference] = []
        errors: List[CellError] = []
        
        # Create PIC-based row mapping for live data (PIC value -> row dict)
        live_pic_map = {}
        for live_row in live_data.rows:
            pic_value = live_row.get('PIC') or live_row.get('pic')
            if pic_value is not None:  # Allow 0 as valid PIC
                # Normalize PIC value (strip whitespace, convert to string)
                pic_normalized = str(pic_value).strip()
                live_pic_map[pic_normalized] = live_row
                self.logger.debug(f"Added live PIC: '{pic_normalized}' (original: {repr(pic_value)})")
        
        self.logger.debug(f"Live data PIC map keys: {list(live_pic_map.keys())}")
        
        # Create header name to index mapping
        live_header_map = {header: idx for idx, header in enumerate(live_data.headers)}
        
        # Iterate through ALL file table rows
        for row_idx, file_row in enumerate(file_data.rows):
            # Get PIC value from file row
            file_pic = file_row.get('PIC') or file_row.get('pic')
            
            if file_pic is None:  # Check for None specifically (allow 0)
                # No PIC value - skip row
                self.logger.warning(f"File row {row_idx} has no PIC value, skipping")
                continue
            
            # Normalize PIC value for lookup (strip whitespace, convert to string)
            file_pic_normalized = str(file_pic).strip()
            self.logger.debug(f"Processing file row {row_idx}: PIC='{file_pic_normalized}' (original: {repr(file_pic)})")
            self.logger.debug(f"  File row data: {dict(list(file_row.items())[:5])}...")  # Show first 5 columns
            
            # Find corresponding row in live data by PIC value
            if file_pic_normalized not in live_pic_map:
                # Row missing in live data - mark all cells as errors
                self.logger.warning(f"File PIC '{file_pic_normalized}' not found in live data. Available: {list(live_pic_map.keys())}")
                for col_idx, file_header in enumerate(file_data.headers):
                    # Skip PIC column for error marking
                    if file_header.upper() != 'PIC':
                        errors.append(CellError(
                            row=row_idx,
                            col=col_idx,
                            error_message=f"PIC {file_pic_normalized} missing in live data"
                        ))
                continue
            
            live_row = live_pic_map[file_pic_normalized]
            self.logger.debug(f"  Live row data: {dict(list(live_row.items())[:5])}...")  # Show first 5 columns
            
            # Iterate through columns in file row (skip only PIC column)
            # Track display_col_idx separately (PIC is removed from table display)
            display_col_idx = 0
            for col_idx, file_header in enumerate(file_data.headers):
                # Skip PIC column (only compare actual I/O data and sum)
                if file_header.upper() == 'PIC':
                    continue
                
                file_value = file_row.get(file_header, "")
                
                # Find corresponding column in live data by header name
                if file_header not in live_header_map:
                    # Column missing in live data
                    errors.append(CellError(
                        row=row_idx,
                        col=display_col_idx,  # Use display column index
                        error_message=f"Column '{file_header}' missing in live data"
                    ))
                    display_col_idx += 1
                    continue
                
                live_col_idx = live_header_map[file_header]
                live_value = live_row.get(file_header, "")
                
                # Normalize values for comparison (strip whitespace, case-insensitive for non-numeric)
                file_val_norm = self._normalize_cell_value(file_value)
                live_val_norm = self._normalize_cell_value(live_value)
                
                # Compare values (use display_col_idx for UI mapping)
                if file_val_norm == live_val_norm:
                    matches.append((row_idx, display_col_idx))
                else:
                    self.logger.debug(f"DIFFERENCE at row {row_idx} display_col {display_col_idx} ({file_header}): file='{file_val_norm}' vs live='{live_val_norm}'")
                    differences.append(CellDifference(
                        row=row_idx,
                        col=display_col_idx,  # Use display column index
                        file_value=file_value,
                        live_value=live_value
                    ))
                
                display_col_idx += 1
        
        # Calculate statistics
        total_cells = len(matches) + len(differences) + len(errors)
        match_percentage = (len(matches) / total_cells * 100) if total_cells > 0 else 0.0
        
        self.logger.info(
            f"Comparison complete: {len(matches)} matches, {len(differences)} differences, "
            f"{len(errors)} errors, {match_percentage:.1f}% match"
        )
        
        return ComparisonResult(
            success=True,
            file_type=file_data.file_type,
            match_percentage=match_percentage,
            total_cells=total_cells,
            matches=matches,
            differences=differences,
            errors=errors,
            error_message=None
        )
    
    def _normalize_cell_value(self, value: str) -> str:
        """
        Normalize cell value for comparison.
        
        Args:
            value: Raw cell value
            
        Returns:
            Normalized value (stripped whitespace, uppercase for text)
        """
        if not value:
            return ""
        
        normalized = str(value).strip()
        
        # For numeric values, keep as-is (preserve case for hex, etc.)
        if normalized.isdigit():
            return normalized
        
        # For text values, convert to uppercase for case-insensitive comparison
        return normalized.upper()
