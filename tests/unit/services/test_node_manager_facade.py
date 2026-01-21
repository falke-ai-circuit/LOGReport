"""
Tests for NodeManagerFacade.
"""

import pytest
from unittest.mock import MagicMock, PropertyMock
from src.commander.services.node_manager_facade import NodeManagerFacade, NodeInfo


class TestNodeInfo:
    """Test NodeInfo dataclass."""
    
    def test_create_with_defaults(self):
        """Should create with default values."""
        info = NodeInfo(name="AP01m", ip_address="192.168.1.1")
        
        assert info.name == "AP01m"
        assert info.ip_address == "192.168.1.1"
        assert info.tokens == []
        assert info.token_types == []
        assert info.is_valid is True
    
    def test_create_with_all_fields(self):
        """Should create with all fields."""
        info = NodeInfo(
            name="AP01m",
            ip_address="192.168.1.1",
            tokens=["001", "002"],
            token_types=["FBC", "RPC"]
        )
        
        assert info.tokens == ["001", "002"]
        assert info.token_types == ["FBC", "RPC"]
    
    def test_has_token(self):
        """Should check token existence."""
        info = NodeInfo(
            name="AP01m",
            ip_address="192.168.1.1",
            tokens=["001", "002"]
        )
        
        assert info.has_token("001") is True
        assert info.has_token("003") is False
    
    def test_has_token_type(self):
        """Should check token type existence."""
        info = NodeInfo(
            name="AP01m",
            ip_address="192.168.1.1",
            token_types=["FBC", "RPC"]
        )
        
        assert info.has_token_type("FBC") is True
        assert info.has_token_type("BSTOOL") is False


class TestNodeManagerFacade:
    """Test NodeManagerFacade."""
    
    @pytest.fixture
    def mock_node_manager(self):
        """Create a mock node manager."""
        manager = MagicMock()
        
        # Mock node with tokens
        mock_node = MagicMock()
        mock_node.name = "AP01m"
        mock_node.ip_address = "192.168.1.1"
        
        # Create mock tokens
        mock_token_fbc = MagicMock()
        mock_token_fbc.token_type = "FBC"
        
        mock_token_rpc = MagicMock()
        mock_token_rpc.token_type = "RPC"
        
        mock_node.tokens = {
            "001": mock_token_fbc,
            "002": mock_token_rpc
        }
        
        manager.get_node.return_value = mock_node
        manager.get_nodes.return_value = {"AP01m": mock_node, "AP02m": MagicMock()}
        
        return manager
    
    @pytest.fixture
    def facade(self, mock_node_manager):
        """Create a NodeManagerFacade with mock manager."""
        return NodeManagerFacade(mock_node_manager)
    
    def test_get_all_node_names(self, facade):
        """Should return all node names."""
        names = facade.get_all_node_names()
        
        assert "AP01m" in names
        assert "AP02m" in names
    
    def test_get_all_node_names_empty(self):
        """Should return empty list when no manager."""
        facade = NodeManagerFacade(None)
        names = facade.get_all_node_names()
        
        assert names == []
    
    def test_get_node_info(self, facade):
        """Should return node info."""
        info = facade.get_node_info("AP01m")
        
        assert info is not None
        assert info.name == "AP01m"
        assert info.ip_address == "192.168.1.1"
        assert "001" in info.tokens
        assert "002" in info.tokens
        assert "FBC" in info.token_types
        assert "RPC" in info.token_types
    
    def test_get_node_info_not_found(self, facade, mock_node_manager):
        """Should return None when node not found."""
        mock_node_manager.get_node.return_value = None
        
        info = facade.get_node_info("nonexistent")
        
        assert info is None
    
    def test_get_node_ip(self, facade):
        """Should return node IP."""
        ip = facade.get_node_ip("AP01m")
        
        assert ip == "192.168.1.1"
    
    def test_get_node_ip_not_found(self, facade, mock_node_manager):
        """Should return None when node not found."""
        mock_node_manager.get_node.return_value = None
        
        ip = facade.get_node_ip("nonexistent")
        
        assert ip is None
    
    def test_get_node_tokens(self, facade):
        """Should return all node tokens."""
        tokens = facade.get_node_tokens("AP01m")
        
        assert "001" in tokens
        assert "002" in tokens
    
    def test_get_node_tokens_filtered(self, facade):
        """Should filter tokens by type."""
        tokens = facade.get_node_tokens("AP01m", token_type="FBC")
        
        assert "001" in tokens
        assert "002" not in tokens  # RPC token
    
    def test_node_exists(self, facade):
        """Should check if node exists."""
        assert facade.node_exists("AP01m") is True
    
    def test_node_exists_false(self, facade, mock_node_manager):
        """Should return False when node doesn't exist."""
        mock_node_manager.get_node.return_value = None
        
        assert facade.node_exists("nonexistent") is False
    
    def test_get_node_count(self, facade):
        """Should return node count."""
        count = facade.get_node_count()
        
        assert count == 2  # AP01m and AP02m
    
    def test_reload_configuration(self, facade, mock_node_manager):
        """Should reload configuration."""
        mock_node_manager.load_config = MagicMock()
        
        result = facade.reload_configuration()
        
        assert result is True
        mock_node_manager.load_config.assert_called_once()
    
    def test_reload_configuration_no_manager(self):
        """Should return False when no manager."""
        facade = NodeManagerFacade(None)
        
        result = facade.reload_configuration()
        
        assert result is False
    
    def test_get_all_nodes(self, facade, mock_node_manager):
        """Should return all nodes as NodeInfo."""
        # Setup second mock node
        mock_node2 = MagicMock()
        mock_node2.name = "AP02m"
        mock_node2.ip_address = "192.168.1.2"
        mock_node2.tokens = {}
        
        def get_node_side_effect(name):
            if name == "AP01m":
                return mock_node_manager.get_node.return_value
            elif name == "AP02m":
                return mock_node2
            return None
        
        mock_node_manager.get_node.side_effect = get_node_side_effect
        
        nodes = facade.get_all_nodes()
        
        assert len(nodes) == 2
        assert any(n.name == "AP01m" for n in nodes)
        assert any(n.name == "AP02m" for n in nodes)
