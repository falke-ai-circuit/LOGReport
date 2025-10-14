"""
Unit tests for FBC Comparison Service

Tests telnet command execution, response parsing, table comparison algorithms,
and error handling for Phase 3 live comparison functionality.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from dataclasses import dataclass

from src.commander.services.fbc_comparison_service import (
    FbcComparisonService,
    ComparisonResult,
    CellDifference,
    CellError
)
from src.commander.services.fbc_parser_service import FbcTableData


# Fixtures

@pytest.fixture
def mock_telnet_service():
    """Mock TelnetService with telnet_session"""
    service = Mock()
    service.telnet_session = Mock()
    service._ensure_debugger_connection = Mock(return_value=True)
    return service


@pytest.fixture
def mock_fbc_parser():
    """Mock FbcParserService"""
    return Mock()


@pytest.fixture
def comparison_service(mock_telnet_service, mock_fbc_parser):
    """FbcComparisonService instance with mocked dependencies"""
    return FbcComparisonService(mock_telnet_service, mock_fbc_parser)


@pytest.fixture
def sample_fbc_file_data():
    """Sample FBC file data for testing"""
    return FbcTableData(
        timestamp="2025-10-14 10:30:00",
        command="print from fbc io structure 0010000",
        agent_id="1",
        file_type="FBC",
        headers=["PIC", "5", "6", "7", "sum"],
        rows=[
            {"PIC": "0", "5": "AI8", "6": "16", "7": "0", "sum": "16"},
            {"PIC": "1", "5": "BI8", "6": "8", "7": "0", "sum": "8"},
            {"PIC": "2", "5": "BO8", "6": "0", "7": "8", "sum": "8"}
        ],
        totals={"io_units": 3, "channels": 32},
        raw_content=""
    )


@pytest.fixture
def sample_rpc_file_data():
    """Sample RPC file data for testing"""
    return FbcTableData(
        timestamp="2025-10-14 10:30:00",
        command="print from fbc rupi counters 0010000",
        agent_id="1",
        file_type="RPC",
        headers=["pic", "IREX ERROR", "POLL ERROR", "RESP FAIL", "IREX COUNT", "TIMEOUT"],
        rows=[
            {"pic": "0", "IREX ERROR": "0", "POLL ERROR": "0", "RESP FAIL": "0", "IREX COUNT": "1234", "TIMEOUT": "0"},
            {"pic": "1", "IREX ERROR": "0", "POLL ERROR": "0", "RESP FAIL": "0", "IREX COUNT": "5678", "TIMEOUT": "0"}
        ],
        totals={},
        raw_content=""
    )


# Test Class 1: Telnet Command Execution

class TestTelnetCommandExecution:
    """Test telnet command generation and execution"""
    
    def test_fbc_command_generation(self, comparison_service, mock_telnet_service, sample_fbc_file_data):
        """Test FBC command is generated correctly"""
        mock_telnet_service.telnet_session.send_command.return_value = "FBC agent 1\nPIC  5    6    7    sum\n0    AI8  16   0    16\n"
        comparison_service.fbc_parser.parse_content.return_value = sample_fbc_file_data
        
        comparison_service.compare_with_live("AP01m", "001", sample_fbc_file_data)
        
        # Verify command was called with correct FBC format
        mock_telnet_service.telnet_session.send_command.assert_called_once()
        call_args = mock_telnet_service.telnet_session.send_command.call_args
        assert "print from fbc io structure 0010000" in call_args[0][0]
    
    def test_rpc_command_generation(self, comparison_service, mock_telnet_service, sample_rpc_file_data):
        """Test RPC command is generated correctly"""
        mock_telnet_service.telnet_session.send_command.return_value = "pic  IREX ERROR  POLL ERROR\n0    0           0\n"
        comparison_service.fbc_parser.parse_content.return_value = sample_rpc_file_data
        
        comparison_service.compare_with_live("AP01m", "045", sample_rpc_file_data)
        
        # Verify command was called with correct RPC format
        mock_telnet_service.telnet_session.send_command.assert_called_once()
        call_args = mock_telnet_service.telnet_session.send_command.call_args
        assert "print from fbc rupi counters 0450000" in call_args[0][0]
    
    def test_connection_failure_handling(self, comparison_service, mock_telnet_service, sample_fbc_file_data):
        """Test handling of connection failures"""
        mock_telnet_service._ensure_debugger_connection.return_value = False
        
        result = comparison_service.compare_with_live("AP01m", "001", sample_fbc_file_data)
        
        assert result.success is False
        assert "Connection error" in result.error_message


# Test Class 2: Response Parsing

class TestResponseParsing:
    """Test telnet response parsing"""
    
    def test_parse_fbc_response(self, comparison_service, mock_fbc_parser, sample_fbc_file_data):
        """Test parsing of valid FBC response"""
        fbc_response = """FBC agent 1
PIC  5    6    7    sum
0    AI8  16   0    16
1    BI8  8    0    8
2    BO8  0    8    8
Total sum: 3 I/O-units, 32 Channels (24 input, 8 output)"""
        
        mock_fbc_parser.parse_content.return_value = sample_fbc_file_data
        
        result = comparison_service._parse_telnet_response(fbc_response, "FBC")
        
        assert result is not None
        assert result.file_type == "FBC"
        assert len(result.rows) == 3
        mock_fbc_parser.parse_content.assert_called_once_with(fbc_response, "FBC")
    
    def test_parse_rpc_response(self, comparison_service, mock_fbc_parser, sample_rpc_file_data):
        """Test parsing of valid RPC response"""
        rpc_response = """pic  IREX ERROR  POLL ERROR  RESP FAIL  IREX COUNT  TIMEOUT
0    0           0           0          1234        0
1    0           0           0          5678        0"""
        
        mock_fbc_parser.parse_content.return_value = sample_rpc_file_data
        
        result = comparison_service._parse_telnet_response(rpc_response, "RPC")
        
        assert result is not None
        assert result.file_type == "RPC"
        assert len(result.rows) == 2
    
    def test_parse_malformed_response(self, comparison_service, mock_fbc_parser):
        """Test handling of malformed response"""
        mock_fbc_parser.parse_content.return_value = None
        
        result = comparison_service._parse_telnet_response("Invalid data", "FBC")
        
        assert result is None
    
    def test_parse_empty_response(self, comparison_service, mock_fbc_parser):
        """Test handling of empty response"""
        empty_data = FbcTableData(
            timestamp="", command="", agent_id="", file_type="FBC",
            headers=[], rows=[], totals={}, raw_content=""
        )
        mock_fbc_parser.parse_content.return_value = empty_data
        
        result = comparison_service._parse_telnet_response("", "FBC")
        
        assert result is None


# Test Class 3: Table Comparison

class TestTableComparison:
    """Test cell-by-cell comparison algorithms"""
    
    def test_perfect_match(self, comparison_service):
        """Test comparison with perfect match"""
        file_data = FbcTableData(
            timestamp="", command="", agent_id="1", file_type="FBC",
            headers=["PIC", "Type", "Count"],
            rows=[
                {"PIC": "0", "Type": "AI8", "Count": "16"},
                {"PIC": "1", "Type": "BI8", "Count": "8"}
            ],
            totals={}, raw_content=""
        )
        
        live_data = FbcTableData(
            timestamp="", command="", agent_id="1", file_type="FBC",
            headers=["PIC", "Type", "Count"],
            rows=[
                {"PIC": "0", "Type": "AI8", "Count": "16"},
                {"PIC": "1", "Type": "BI8", "Count": "8"}
            ],
            totals={}, raw_content=""
        )
        
        result = comparison_service._compare_tables(file_data, live_data)
        
        assert result.success is True
        assert result.match_percentage == 100.0
        assert len(result.matches) == 6  # 2 rows * 3 columns
        assert len(result.differences) == 0
        assert len(result.errors) == 0
    
    def test_partial_differences(self, comparison_service):
        """Test comparison with some differences"""
        file_data = FbcTableData(
            timestamp="", command="", agent_id="1", file_type="FBC",
            headers=["PIC", "Type", "Count"],
            rows=[
                {"PIC": "0", "Type": "AI8", "Count": "16"},
                {"PIC": "1", "Type": "BI8", "Count": "8"}
            ],
            totals={}, raw_content=""
        )
        
        live_data = FbcTableData(
            timestamp="", command="", agent_id="1", file_type="FBC",
            headers=["PIC", "Type", "Count"],
            rows=[
                {"PIC": "0", "Type": "AI8", "Count": "20"},  # Different count
                {"PIC": "1", "Type": "BO8", "Count": "8"}   # Different type
            ],
            totals={}, raw_content=""
        )
        
        result = comparison_service._compare_tables(file_data, live_data)
        
        assert result.success is True
        assert result.match_percentage < 100.0
        assert len(result.differences) == 2  # Count and Type differences
        assert len(result.matches) == 4  # 4 matching cells
        assert result.differences[0].file_value == "16"
        assert result.differences[0].live_value == "20"
    
    def test_missing_column_in_live(self, comparison_service):
        """Test handling of missing columns in live data"""
        file_data = FbcTableData(
            timestamp="", command="", agent_id="1", file_type="FBC",
            headers=["PIC", "Type", "Count", "Extra"],
            rows=[
                {"PIC": "0", "Type": "AI8", "Count": "16", "Extra": "data"}
            ],
            totals={}, raw_content=""
        )
        
        live_data = FbcTableData(
            timestamp="", command="", agent_id="1", file_type="FBC",
            headers=["PIC", "Type", "Count"],  # Missing "Extra" column
            rows=[
                {"PIC": "0", "Type": "AI8", "Count": "16"}
            ],
            totals={}, raw_content=""
        )
        
        result = comparison_service._compare_tables(file_data, live_data)
        
        assert result.success is True
        assert len(result.errors) == 1  # Missing column error
        assert "Extra" in result.errors[0].error_message
    
    def test_missing_row_in_live(self, comparison_service):
        """Test handling of missing rows in live data"""
        file_data = FbcTableData(
            timestamp="", command="", agent_id="1", file_type="FBC",
            headers=["PIC", "Type"],
            rows=[
                {"PIC": "0", "Type": "AI8"},
                {"PIC": "1", "Type": "BI8"},
                {"PIC": "2", "Type": "BO8"}  # This row missing in live
            ],
            totals={}, raw_content=""
        )
        
        live_data = FbcTableData(
            timestamp="", command="", agent_id="1", file_type="FBC",
            headers=["PIC", "Type"],
            rows=[
                {"PIC": "0", "Type": "AI8"},
                {"PIC": "1", "Type": "BI8"}
            ],
            totals={}, raw_content=""
        )
        
        result = comparison_service._compare_tables(file_data, live_data)
        
        assert result.success is True
        assert len(result.errors) == 2  # 2 cells in missing row
        assert "Row missing" in result.errors[0].error_message
    
    def test_case_insensitive_text_comparison(self, comparison_service):
        """Test case-insensitive comparison for text values"""
        file_data = FbcTableData(
            timestamp="", command="", agent_id="1", file_type="FBC",
            headers=["Type"],
            rows=[{"Type": "ai8"}],
            totals={}, raw_content=""
        )
        
        live_data = FbcTableData(
            timestamp="", command="", agent_id="1", file_type="FBC",
            headers=["Type"],
            rows=[{"Type": "AI8"}],  # Different case
            totals={}, raw_content=""
        )
        
        result = comparison_service._compare_tables(file_data, live_data)
        
        assert result.success is True
        assert len(result.matches) == 1  # Should match despite case difference
        assert len(result.differences) == 0


# Test Class 4: Error Handling

class TestErrorHandling:
    """Test error handling scenarios"""
    
    def test_telnet_timeout_error(self, comparison_service, mock_telnet_service, sample_fbc_file_data):
        """Test handling of telnet timeout"""
        mock_telnet_service.telnet_session.send_command.return_value = "Error: Command timed out - socket.timeout"
        
        result = comparison_service.compare_with_live("AP01m", "001", sample_fbc_file_data)
        
        assert result.success is False
        assert "Telnet command failed" in result.error_message
    
    def test_connection_refused_error(self, comparison_service, mock_telnet_service, sample_fbc_file_data):
        """Test handling of connection refused"""
        mock_telnet_service.telnet_session.send_command.side_effect = ConnectionError("Connection refused")
        
        result = comparison_service.compare_with_live("AP01m", "001", sample_fbc_file_data)
        
        assert result.success is False
        assert "Connection error" in result.error_message
    
    def test_parse_error_handling(self, comparison_service, mock_telnet_service, mock_fbc_parser, sample_fbc_file_data):
        """Test handling of parse errors"""
        mock_telnet_service.telnet_session.send_command.return_value = "Valid response"
        mock_fbc_parser.parse_content.side_effect = Exception("Parse error")
        
        result = comparison_service.compare_with_live("AP01m", "001", sample_fbc_file_data)
        
        assert result.success is False
        assert "Failed to parse telnet response" in result.error_message
    
    def test_invalid_file_type(self, comparison_service, mock_telnet_service):
        """Test handling of invalid file type"""
        invalid_data = FbcTableData(
            timestamp="", command="", agent_id="1", file_type="INVALID",
            headers=[], rows=[], totals={}, raw_content=""
        )
        
        result = comparison_service.compare_with_live("AP01m", "001", invalid_data)
        
        assert result.success is False
        assert "Unknown file type" in result.error_message or "Comparison failed" in result.error_message


# Test Class 5: Integration Tests

class TestIntegration:
    """Integration tests with realistic scenarios"""
    
    def test_full_fbc_comparison_workflow(self, comparison_service, mock_telnet_service, mock_fbc_parser):
        """Test complete FBC comparison workflow"""
        # Setup file data
        file_data = FbcTableData(
            timestamp="2025-10-14 10:30:00",
            command="print from fbc io structure 0010000",
            agent_id="1",
            file_type="FBC",
            headers=["PIC", "5", "6"],
            rows=[
                {"PIC": "0", "5": "AI8", "6": "16"},
                {"PIC": "1", "5": "BI8", "6": "8"}
            ],
            totals={}, raw_content=""
        )
        
        # Setup live data (with one difference)
        live_data = FbcTableData(
            timestamp="2025-10-14 10:35:00",
            command="print from fbc io structure 0010000",
            agent_id="1",
            file_type="FBC",
            headers=["PIC", "5", "6"],
            rows=[
                {"PIC": "0", "5": "AI8", "6": "16"},
                {"PIC": "1", "5": "BI8", "6": "10"}  # Different value
            ],
            totals={}, raw_content=""
        )
        
        # Mock telnet response
        mock_telnet_service.telnet_session.send_command.return_value = "FBC response"
        mock_fbc_parser.parse_content.return_value = live_data
        
        # Execute comparison
        result = comparison_service.compare_with_live("AP01m", "001", file_data)
        
        # Verify results
        assert result.success is True
        assert result.file_type == "FBC"
        assert result.total_cells == 6
        assert len(result.matches) == 5
        assert len(result.differences) == 1
        assert result.differences[0].row == 1
        assert result.differences[0].col == 2
        assert result.differences[0].file_value == "8"
        assert result.differences[0].live_value == "10"
        assert result.match_percentage > 80.0
    
    def test_result_to_dict_conversion(self, comparison_service):
        """Test ComparisonResult.to_dict() method"""
        result = ComparisonResult(
            success=True,
            file_type="FBC",
            match_percentage=95.5,
            total_cells=100,
            matches=[(0, 0), (0, 1)],
            differences=[CellDifference(1, 2, "old", "new")],
            errors=[CellError(2, 3, "Error msg")],
            error_message=None
        )
        
        result_dict = result.to_dict()
        
        assert result_dict['success'] is True
        assert result_dict['match_percentage'] == 95.5
        assert len(result_dict['matches']) == 2
        assert result_dict['differences'][0] == (1, 2, "old", "new")
        assert result_dict['errors'][0] == (2, 3, "Error msg")
