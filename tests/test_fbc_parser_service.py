"""
Unit tests for FBC Parser Service

Tests FBC and RPC file parsing functionality including:
- File type detection
- Header extraction
- Row parsing
- Totals calculation
- Error handling
"""

import pytest
from pathlib import Path
from src.commander.services.fbc_parser_service import FbcParserService, FbcTableData


@pytest.fixture
def parser():
    """Create FbcParserService instance"""
    return FbcParserService()


@pytest.fixture
def sample_fbc_content():
    """Sample FBC file content"""
    return """[2025-10-12 12:12:08]
Command executed: print from fbc io structure 1620000
Getting FIELD BUS configuration from FBC agent 1620000

FBC Utilization Rate: 92%

 PIC    5    6    7    8    9   10   11   12   13   14   15   16   17   18   19   20  sum
----------------------------------------------------------------------------------------------
  0   AI8  BI8  BO8  BI8  BI8  BI8  BO8  BI8  BI8  BI8  BI8  BI8  BI8  BI8  TI6  AO4   15
  1   AI8  BI8  BI8  BI8  BO8  BI8  BO8  BI8  BI8  BI8  BI8  BI8  BI8  BI8  TI6  BI8   15
  2   AI8  BI8  BI8  BI8  BO8  BI8  BO8  BI8  BI8  BI8  BI8  BI8  BI8  BI8  BI8  BI8   15
  3   AI8  BI8  BO8  BI8  BO8  BI8  BO8  BI8  BI8  BI8  BI8  BI8  BI8  BI8  TI6  BI8   15

Total sum: 238 I/O-units, 1843 Channels (1323 input, 520 output)
AIU8: 15, AOU4: 4, BIU8: 131, BI8N: 6, BOU8: 63, FIU1: 2, AIU4: 1, TIU6: 16
"""


@pytest.fixture
def sample_rpc_content():
    """Sample RPC file content"""
    return """[2025-10-12 12:12:34]
Command executed: print from fbc rupi counters 1620000
Getting FIELD BUS error counters from RUPI(8344) from FBC agent 1620000

 pic   IREX ERROR   POLL ERROR   RESP FAIL   IREX COUNT   TIMEOUT
---------------------------------------------------------------------
  0         0            0            0            0          14
  1         0            0            0            0          69
  2         0            0            0            0         138
  3         0            0            0            0          95
  4         0            0            0            0         101
  5         0            0            0            0          86

Unknown command: 0
"""


class TestFileTypeDetection:
    """Tests for file type detection"""
    
    def test_detect_fbc_file(self, parser):
        """Should detect .fbc extension as FBC type"""
        file_type = parser._detect_file_type("/path/to/file.fbc")
        assert file_type == 'FBC'
    
    def test_detect_rpc_file(self, parser):
        """Should detect .rpc extension as RPC type"""
        file_type = parser._detect_file_type("/path/to/file.rpc")
        assert file_type == 'RPC'
    
    def test_detect_unknown_defaults_to_fbc(self, parser):
        """Should default to FBC for unknown extensions"""
        file_type = parser._detect_file_type("/path/to/file.txt")
        assert file_type == 'FBC'


class TestFBCParsing:
    """Tests for FBC file parsing"""
    
    def test_parse_fbc_content_basic(self, parser, sample_fbc_content):
        """Should parse valid FBC content"""
        result = parser.parse_content(sample_fbc_content, 'FBC')
        
        assert isinstance(result, FbcTableData)
        assert result.file_type == 'FBC'
        assert result.timestamp == '2025-10-12 12:12:08'
        assert result.agent_id == '1620000'
        assert len(result.rows) == 4  # 4 PIC rows
    
    def test_parse_fbc_headers(self, parser, sample_fbc_content):
        """Should extract FBC column headers"""
        result = parser.parse_content(sample_fbc_content, 'FBC')
        
        assert 'PIC' in result.headers
        assert '5' in result.headers
        assert '20' in result.headers
        assert 'sum' in result.headers
        assert len(result.headers) == 18  # PIC + 5-20 + sum
    
    def test_parse_fbc_rows(self, parser, sample_fbc_content):
        """Should parse FBC data rows correctly"""
        result = parser.parse_content(sample_fbc_content, 'FBC')
        
        # Check first row
        first_row = result.rows[0]
        assert first_row['PIC'] == '0'
        assert first_row['5'] == 'AI8'
        assert first_row['6'] == 'BI8'
        assert first_row['20'] == 'AO4'
        assert first_row['sum'] == '15'
    
    def test_parse_fbc_totals(self, parser, sample_fbc_content):
        """Should extract FBC totals section"""
        result = parser.parse_content(sample_fbc_content, 'FBC')
        
        assert result.totals['total_units'] == 238
        assert result.totals['total_channels'] == 1843
        assert result.totals['input_channels'] == 1323
        assert result.totals['output_channels'] == 520
    
    def test_parse_fbc_unit_breakdown(self, parser, sample_fbc_content):
        """Should extract unit type breakdown"""
        result = parser.parse_content(sample_fbc_content, 'FBC')
        
        breakdown = result.totals['unit_breakdown']
        assert breakdown['AIU8'] == 15
        assert breakdown['BOU8'] == 63
        assert breakdown['TIU6'] == 16
    
    def test_parse_fbc_empty_content(self, parser):
        """Should handle empty FBC content gracefully"""
        result = parser.parse_content("", 'FBC')
        
        assert result.file_type == 'FBC'
        assert len(result.rows) == 0
        assert len(result.headers) == 0


class TestRPCParsing:
    """Tests for RPC file parsing"""
    
    def test_parse_rpc_content_basic(self, parser, sample_rpc_content):
        """Should parse valid RPC content"""
        result = parser.parse_content(sample_rpc_content, 'RPC')
        
        assert isinstance(result, FbcTableData)
        assert result.file_type == 'RPC'
        assert result.timestamp == '2025-10-12 12:12:34'
        assert result.agent_id == '1620000'
        assert len(result.rows) == 6  # 6 PIC rows
    
    def test_parse_rpc_headers(self, parser, sample_rpc_content):
        """Should have fixed RPC headers"""
        result = parser.parse_content(sample_rpc_content, 'RPC')
        
        expected_headers = ['pic', 'IREX ERROR', 'POLL ERROR', 'RESP FAIL', 'IREX COUNT', 'TIMEOUT']
        assert result.headers == expected_headers
    
    def test_parse_rpc_rows(self, parser, sample_rpc_content):
        """Should parse RPC data rows correctly"""
        result = parser.parse_content(sample_rpc_content, 'RPC')
        
        # Check first row
        first_row = result.rows[0]
        assert first_row['pic'] == '0'
        assert first_row['IREX ERROR'] == '0'
        assert first_row['TIMEOUT'] == '14'
        
        # Check second row
        second_row = result.rows[1]
        assert second_row['pic'] == '1'
        assert second_row['TIMEOUT'] == '69'
    
    def test_parse_rpc_unknown_command(self, parser, sample_rpc_content):
        """Should extract unknown command count"""
        result = parser.parse_content(sample_rpc_content, 'RPC')
        
        assert result.totals['unknown_command'] == 0
    
    def test_parse_rpc_empty_content(self, parser):
        """Should handle empty RPC content gracefully"""
        result = parser.parse_content("", 'RPC')
        
        assert result.file_type == 'RPC'
        assert len(result.rows) == 0


class TestMetadataExtraction:
    """Tests for metadata extraction"""
    
    def test_extract_timestamp_standard_format(self, parser):
        """Should extract timestamp in [YYYY-MM-DD HH:MM:SS] format"""
        lines = ["[2025-10-12 14:30:45]", "some content"]
        timestamp = parser._extract_timestamp(lines)
        assert timestamp == "2025-10-12 14:30:45"
    
    def test_extract_timestamp_missing(self, parser):
        """Should return 'Unknown' if timestamp not found"""
        lines = ["no timestamp here"]
        timestamp = parser._extract_timestamp(lines)
        assert timestamp == "Unknown"
    
    def test_extract_fbc_command(self, parser):
        """Should extract FBC command"""
        lines = ["print from fbc io structure 1620000"]
        command = parser._extract_command(lines, 'FBC')
        assert "print from fbc io structure 1620000" in command
    
    def test_extract_rpc_command(self, parser):
        """Should extract RPC command"""
        lines = ["print from fbc rupi counters 1620000"]
        command = parser._extract_command(lines, 'RPC')
        assert "print from fbc rupi counters 1620000" in command
    
    def test_extract_agent_id(self, parser):
        """Should extract agent ID"""
        lines = ["from FBC agent 1620000"]
        agent_id = parser._extract_agent(lines)
        assert agent_id == "1620000"


class TestEdgeCases:
    """Tests for edge cases and error handling"""
    
    def test_parse_fbc_with_missing_header(self, parser):
        """Should handle FBC content with missing table header"""
        content = """[2025-10-12 12:12:08]
No table header here
Some random content
"""
        result = parser.parse_content(content, 'FBC')
        assert len(result.rows) == 0
        assert len(result.headers) == 0
    
    def test_parse_rpc_with_missing_header(self, parser):
        """Should handle RPC content with missing table header"""
        content = """[2025-10-12 12:12:08]
No table header here
"""
        result = parser.parse_content(content, 'RPC')
        assert len(result.rows) == 0
    
    def test_parse_malformed_fbc_row(self, parser):
        """Should skip malformed FBC rows"""
        content = """[2025-10-12 12:12:08]
 PIC    5    6   sum
---------------------
  0   AI8  BI8   2
malformed row without proper format
  1   AI8  BI8   2
"""
        result = parser.parse_content(content, 'FBC')
        assert len(result.rows) == 2  # Only valid rows
    
    def test_parse_whitespace_variations(self, parser):
        """Should handle various whitespace patterns"""
        content = """[2025-10-12 12:12:08]
 PIC    5    6   sum
---------------------
    0     AI8    BI8     2  
  1   AI8  BI8   2
"""
        result = parser.parse_content(content, 'FBC')
        assert len(result.rows) == 2
        assert result.rows[0]['PIC'] == '0'
    
    def test_parse_file_not_found(self, parser):
        """Should raise FileNotFoundError for non-existent file"""
        with pytest.raises(FileNotFoundError):
            parser.parse_file("/nonexistent/path/file.fbc")
    
    def test_parse_invalid_file_type(self, parser):
        """Should raise ValueError for invalid file type"""
        with pytest.raises(ValueError, match="Unknown file type"):
            parser.parse_content("content", 'INVALID')


class TestRealFileIntegration:
    """Integration tests with real FBC/RPC files if available"""
    
    def test_parse_real_fbc_file(self, parser):
        """Should parse real FBC file from _DIA directory"""
        # Try to find a real FBC file
        fbc_path = Path("d:/_APP/LOGReport/_DIA/FBC")
        if not fbc_path.exists():
            pytest.skip("FBC directory not found")
        
        fbc_files = list(fbc_path.rglob("*.fbc"))
        if not fbc_files:
            pytest.skip("No FBC files found")
        
        # Parse first available file
        result = parser.parse_file(str(fbc_files[0]))
        
        assert result.file_type == 'FBC'
        assert result.timestamp != "Unknown"
        assert len(result.rows) > 0
        assert 'PIC' in result.headers
    
    def test_parse_real_rpc_file(self, parser):
        """Should parse real RPC file from _DIA directory"""
        # Try to find a real RPC file
        rpc_path = Path("d:/_APP/LOGReport/_DIA/RPC")
        if not rpc_path.exists():
            pytest.skip("RPC directory not found")
        
        rpc_files = list(rpc_path.rglob("*.rpc"))
        if not rpc_files:
            pytest.skip("No RPC files found")
        
        # Parse first available file
        result = parser.parse_file(str(rpc_files[0]))
        
        assert result.file_type == 'RPC'
        assert result.timestamp != "Unknown"
        assert len(result.rows) > 0
        assert result.headers == ['pic', 'IREX ERROR', 'POLL ERROR', 'RESP FAIL', 'IREX COUNT', 'TIMEOUT']


class TestRawContentPreservation:
    """Tests for raw content preservation"""
    
    def test_raw_content_preserved_fbc(self, parser, sample_fbc_content):
        """Should preserve raw FBC content"""
        result = parser.parse_content(sample_fbc_content, 'FBC')
        assert result.raw_content == sample_fbc_content
    
    def test_raw_content_preserved_rpc(self, parser, sample_rpc_content):
        """Should preserve raw RPC content"""
        result = parser.parse_content(sample_rpc_content, 'RPC')
        assert result.raw_content == sample_rpc_content
