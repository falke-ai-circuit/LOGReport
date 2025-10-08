import pytest
import os
import json
from unittest.mock import patch, mock_open
from src.sys_file_loader import SysFileLoader, SysFileParser

# Fixture for a valid configuration
@pytest.fixture
def mock_config_content():
    return {
        "regex_patterns": {
            "ip_address": r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b",
            "ap_node": r"AP\d{2}(_main|_reserve)?",
            "al_node": r"AL\d{2}",
            "token_entry": r":e:hw:(?P<token>\w+)\s+(?P<lid>AP\d{2}[mr]?|AL\d{2}[t]?\d?)\s+.*//\s*(?P<comment>.*)",
            "token_detection_line": r"^(?P<node_id>AP\d{2}[mr]?|AL\d{2}[t]?\d?)\s+tokens:\s*(?P<tokens>[\w,\s]+)$"
        },
        "node_types": {
            "AP": ["FBC", "RPC", "LOG"],
            "AL": ["LOG", "LIS"]
        },
        "token_suffixes": {
            "_m": "m",
            "_r": "r",
            "_t": "t"
        }
    }

@pytest.fixture
def mock_config_path():
    return "config/sys_parsing_rules.json"

class TestSysFileLoader:
    @pytest.fixture(autouse=True)
    def setup(self, mock_config_content, mock_config_path):
        with patch("builtins.open", mock_open(read_data=json.dumps(mock_config_content))):
            self.loader = SysFileLoader(config_path=mock_config_path)

    # Test cases for _load_config method
    def test_load_config_success(self, mock_config_content, mock_config_path):
        with patch("builtins.open", mock_open(read_data=json.dumps(mock_config_content))) as mock_file:
            loader = SysFileLoader(config_path=mock_config_path)
            assert loader.config == mock_config_content
            mock_file.assert_called_once_with(mock_config_path, 'r')

    def test_load_config_file_not_found(self, mock_config_path):
        with patch("builtins.open", side_effect=FileNotFoundError) as mock_file:
            with pytest.raises(FileNotFoundError, match=f"Configuration file not found at {mock_config_path}"):
                SysFileLoader(config_path=mock_config_path)
            mock_file.assert_called_once_with(mock_config_path, 'r')

    def test_load_config_json_decode_error(self, mock_config_path):
        with patch("builtins.open", mock_open(read_data="invalid json")) as mock_file:
            with pytest.raises(ValueError, match=f"Error decoding JSON from configuration file at {mock_config_path}"):
                SysFileLoader(config_path=mock_config_path)
            mock_file.assert_called_once_with(mock_config_path, 'r')

    # Test cases for load_sys_files_from_directory method
    def test_load_sys_files_from_directory_success(self, tmp_path):
        # Create dummy sys files
        (tmp_path / "file1.sys").write_text("content1")
        (tmp_path / "file2.sys").write_text("content2")
        (tmp_path / "other.txt").write_text("not a sys file")

        loaded_files = self.loader.load_sys_files_from_directory(str(tmp_path))
        assert loaded_files == {"file1.sys": "content1", "file2.sys": "content2"}

    def test_load_sys_files_from_directory_empty(self, tmp_path):
        loaded_files = self.loader.load_sys_files_from_directory(str(tmp_path))
        assert loaded_files == {}

    def test_load_sys_files_from_directory_not_found(self):
        with pytest.raises(FileNotFoundError, match="Directory not found"):
            self.loader.load_sys_files_from_directory("/nonexistent/path")

    def test_load_sys_files_from_directory_with_unreadable_file(self, tmp_path, capsys):
        (tmp_path / "readable.sys").write_text("readable content")
        unreadable_file = tmp_path / "unreadable.sys"
        unreadable_file.write_text("unreadable content")
        # Simulate permission error by changing permissions (might not work on all OS)
        os.chmod(unreadable_file, 0o000) 

        loaded_files = self.loader.load_sys_files_from_directory(str(tmp_path))
        assert loaded_files == {"readable.sys": "readable content"}
        
        # Capture stderr to check for the warning message
        captured = capsys.readouterr()
        assert f"Error reading file {unreadable_file}:" in captured.out
        
        # Restore permissions for cleanup
        os.chmod(unreadable_file, 0o777)

    # Test cases for detect_tokens_from_content method
    def test_detect_tokens_from_content_success(self):
        content = """
AP01 tokens: 162,163
AL01 tokens: 502,503
AP02m tokens: 182, 183
"""
        expected_tokens = {
            "AP01": ["162", "163"],
            "AL01": ["502", "503"],
            "AP02m": ["182", "183"]
        }
        assert self.loader.detect_tokens_from_content(content) == expected_tokens

    def test_detect_tokens_from_content_no_tokens(self):
        content = """
Some random line
Another line without tokens
"""
        assert self.loader.detect_tokens_from_content(content) == {}

    def test_detect_tokens_from_content_multiple_lines_same_node(self):
        content = """
AP01 tokens: 162
AP01 tokens: 163, 164
"""
        expected_tokens = {
            "AP01": ["162", "163", "164"]
        }
        assert self.loader.detect_tokens_from_content(content) == expected_tokens

    def test_detect_tokens_from_content_empty_content(self):
        assert self.loader.detect_tokens_from_content("") == {}

    # Test cases for parse_token_sys_files method
    @patch("src.sys_file_loader.SysFileParser.parse_sys_files")
    def test_parse_token_sys_files_success(self, mock_parse_sys_files, tmp_path):
        token_ids = ["162", "163"]
        (tmp_path / "162.sys").write_text("token 162 content")
        (tmp_path / "163.sys").write_text("token 163 content")

        mock_parse_sys_files.return_value = [{"name": "Node162"}, {"name": "Node163"}]

        result = self.loader.parse_token_sys_files(token_ids, str(tmp_path))
        
        expected_paths = [
            os.path.join(str(tmp_path), "162.sys"),
            os.path.join(str(tmp_path), "163.sys")
        ]
        mock_parse_sys_files.assert_called_once_with(expected_paths)
        assert result == [{"name": "Node162"}, {"name": "Node163"}]

    @patch("src.sys_file_loader.SysFileParser.parse_sys_files")
    def test_parse_token_sys_files_non_existent_token_file(self, mock_parse_sys_files, tmp_path, capsys):
        token_ids = ["162", "999"] # 999.sys does not exist
        (tmp_path / "162.sys").write_text("token 162 content")

        mock_parse_sys_files.return_value = [{"name": "Node162"}]

        result = self.loader.parse_token_sys_files(token_ids, str(tmp_path))
        
        expected_paths = [
            os.path.join(str(tmp_path), "162.sys")
        ]
        mock_parse_sys_files.assert_called_once_with(expected_paths)
        assert result == [{"name": "Node162"}]

        captured = capsys.readouterr()
        assert f"Warning: Token sys file not found for token ID: 999 at {os.path.join(str(tmp_path), '999.sys')}" in captured.out

    @patch("src.sys_file_loader.SysFileParser.parse_sys_files")
    def test_parse_token_sys_files_empty_token_ids(self, mock_parse_sys_files, tmp_path):
        token_ids = []
        result = self.loader.parse_token_sys_files(token_ids, str(tmp_path))
        mock_parse_sys_files.assert_called_once_with([])
        assert result == []