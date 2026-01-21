"""
Tests for NodeConfigRepository.
"""

import pytest
import tempfile
import json
from pathlib import Path
from src.commander.repositories import NodeConfigRepository, NodeConfigData


class TestNodeConfigData:
    """Test NodeConfigData dataclass."""
    
    def test_create_with_defaults(self):
        """Should create with default empty values."""
        data = NodeConfigData(name="AP01m")
        
        assert data.name == "AP01m"
        assert data.ip == ""
        assert data.tokens == []
        assert data.types == []
    
    def test_create_with_all_fields(self):
        """Should create with all fields."""
        data = NodeConfigData(
            name="AP01m",
            ip="192.168.1.1",
            tokens=["001", "002"],
            types=["FBC", "RPC"]
        )
        
        assert data.name == "AP01m"
        assert data.ip == "192.168.1.1"
        assert data.tokens == ["001", "002"]
        assert data.types == ["FBC", "RPC"]
    
    def test_to_dict(self):
        """Should convert to dictionary."""
        data = NodeConfigData(
            name="AP01m",
            ip="192.168.1.1",
            tokens=["001"],
            types=["FBC"]
        )
        
        result = data.to_dict()
        
        assert result["name"] == "AP01m"
        assert result["ip"] == "192.168.1.1"
        assert result["tokens"] == ["001"]
        assert result["types"] == ["FBC"]
    
    def test_from_dict(self):
        """Should create from dictionary."""
        data_dict = {
            "name": "AP01m",
            "ip": "192.168.1.1",
            "tokens": ["001", "002"],
            "types": ["FBC"]
        }
        
        data = NodeConfigData.from_dict(data_dict)
        
        assert data.name == "AP01m"
        assert data.ip == "192.168.1.1"
        assert data.tokens == ["001", "002"]
    
    def test_from_dict_missing_fields(self):
        """Should handle missing fields with defaults."""
        data = NodeConfigData.from_dict({"name": "test"})
        
        assert data.name == "test"
        assert data.ip == ""
        assert data.tokens == []


class TestNodeConfigRepository:
    """Test NodeConfigRepository."""
    
    @pytest.fixture
    def temp_config_file(self):
        """Create a temporary config file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump([], f)
            return f.name
    
    @pytest.fixture
    def repo(self, temp_config_file):
        """Create a repository with temp file."""
        return NodeConfigRepository(temp_config_file)
    
    def test_load_empty_file(self, repo):
        """Should return empty list for empty file."""
        nodes = repo.load()
        assert nodes == []
    
    def test_save_and_load(self, repo):
        """Should save and load nodes correctly."""
        nodes = [
            NodeConfigData(name="AP01m", ip="192.168.1.1", tokens=["001"], types=["FBC"]),
            NodeConfigData(name="AP02m", ip="192.168.1.2", tokens=["002"], types=["RPC"])
        ]
        
        repo.save(nodes)
        loaded = repo.load()
        
        assert len(loaded) == 2
        assert loaded[0].name == "AP01m"
        assert loaded[1].name == "AP02m"
    
    def test_load_old_format(self, temp_config_file):
        """Should load old format config."""
        old_format = [
            {"name": "AP01m", "ip": "192.168.1.1", "tokens": ["001"], "types": ["FBC"]}
        ]
        
        with open(temp_config_file, 'w') as f:
            json.dump(old_format, f)
        
        repo = NodeConfigRepository(temp_config_file)
        nodes = repo.load()
        
        assert len(nodes) == 1
        assert nodes[0].name == "AP01m"
        assert nodes[0].ip == "192.168.1.1"
    
    def test_load_new_format(self, temp_config_file):
        """Should load new format config with detailed tokens."""
        new_format = [
            {
                "name": "AP01m",
                "ip_address": "192.168.1.1",
                "tokens": [
                    {"token_id": "001", "token_type": "FBC", "ip_address": "192.168.1.1"},
                    {"token_id": "002", "token_type": "RPC", "ip_address": "192.168.1.1"}
                ]
            }
        ]
        
        with open(temp_config_file, 'w') as f:
            json.dump(new_format, f)
        
        repo = NodeConfigRepository(temp_config_file)
        nodes = repo.load()
        
        assert len(nodes) == 1
        assert nodes[0].name == "AP01m"
        assert nodes[0].ip == "192.168.1.1"
        assert "001" in nodes[0].tokens
        assert "002" in nodes[0].tokens
    
    def test_load_nonexistent_file(self):
        """Should return empty list for nonexistent file."""
        repo = NodeConfigRepository("/nonexistent/path.json")
        nodes = repo.load()
        
        assert nodes == []
    
    def test_exists(self, temp_config_file):
        """Should correctly check file existence."""
        repo = NodeConfigRepository(temp_config_file)
        assert repo.exists() is True
        
        repo2 = NodeConfigRepository("/nonexistent/path.json")
        assert repo2.exists() is False
    
    def test_save_to_path(self, repo, temp_config_file):
        """Should save to specific path."""
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            other_path = f.name
        
        nodes = [NodeConfigData(name="test", ip="1.1.1.1", tokens=[], types=[])]
        repo.save_to_path(nodes, other_path)
        
        # Load from other path
        with open(other_path, 'r') as f:
            data = json.load(f)
        
        assert len(data) == 1
        assert data[0]["name"] == "test"
    
    def test_convert_to_file_format(self, repo):
        """Should convert internal format to file format."""
        node = NodeConfigData(
            name="AP01m",
            ip="192.168.1.1",
            tokens=["001", "002"],
            types=["FBC"]
        )
        
        result = repo._convert_to_file_format(node)
        
        assert result["name"] == "AP01m"
        assert result["ip_address"] == "192.168.1.1"
        assert len(result["tokens"]) == 2
        assert result["tokens"][0]["token_id"] == "001"
        assert result["tokens"][0]["token_type"] == "FBC"
