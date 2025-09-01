import os
import sys
import pytest

# Add src directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

from commander.node_manager import NodeManager
from commander.models import Node

class TestTokenDetectionEndToEnd:
    """End-to-end test suite for token detection functionality"""

    @pytest.fixture
    def node_manager(self):
        """Create a node manager with test configuration"""
        manager = NodeManager()
        # Set test configuration path
        test_config_path = os.path.join(os.path.dirname(__file__), '..', 'test_nodes.json')
        manager.set_config_path(test_config_path)
        # Load configuration
        manager.load_configuration()
        # Set log root to test logs directory
        test_logs_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'test_logs')
        manager.set_log_root(test_logs_dir)
        return manager

    def test_ap01m_fbc_and_rpc_tokens_detection(self, node_manager):
        """Test that both FBC and RPC tokens are detected for node AP01m when they have the same token ID"""
        # Scan log files
        node_manager.scan_log_files()

        # Get AP01m node
        node = node_manager.get_node("AP01m")
        assert node is not None, "AP01m node should exist"

        # Check that both FBC and RPC tokens are detected
        fbc_tokens = []
        rpc_tokens = []
        for token_list in node.tokens.values():
            for token in token_list:
                if token.token_type == "FBC":
                    fbc_tokens.append(token)
                elif token.token_type == "RPC":
                    rpc_tokens.append(token)

        fbc_token_ids = {t.token_id for t in fbc_tokens}
        rpc_token_ids = {t.token_id for t in rpc_tokens}

        # Verify all three FBC tokens are present
        expected_fbc_tokens = {"162", "163", "164"}
        detected_fbc_tokens = set(fbc_token_ids)

        assert expected_fbc_tokens.issubset(detected_fbc_tokens), \
            f"Expected FBC tokens {expected_fbc_tokens}, but got {detected_fbc_tokens}"

        # Verify all three RPC tokens are present
        expected_rpc_tokens = {"162", "163", "164"}
        detected_rpc_tokens = set(rpc_token_ids)

        assert expected_rpc_tokens.issubset(detected_rpc_tokens), \
            f"Expected RPC tokens {expected_rpc_tokens}, but got {detected_rpc_tokens}"

        # Verify each token has the correct properties
        for token_id in expected_fbc_tokens:
            token = next((t for t in fbc_tokens if t.token_id == token_id), None)
            assert token is not None, f"FBC Token {token_id} should exist"
            assert token.token_type == "FBC", f"Token {token_id} should be FBC type"
            assert token.ip_address == "192.168.0.11", f"Token {token_id} should have correct IP"

        for token_id in expected_rpc_tokens:
            token = next((t for t in rpc_tokens if t.token_id == token_id), None)
            assert token is not None, f"RPC Token {token_id} should exist"
            assert token.token_type == "RPC", f"Token {token_id} should be RPC type"
            assert token.ip_address == "192.168.0.11", f"Token {token_id} should have correct IP"

    def test_same_token_id_different_types(self, node_manager):
        """Test that FBC and RPC tokens with the same ID are correctly distinguished and handled"""
        # Scan log files
        node_manager.scan_log_files()
        
        # Get AP01m node
        node = node_manager.get_node("AP01m")
        assert node is not None, "AP01m node should exist"
        
        # Get tokens with ID "162" - should have both FBC and RPC
        token_id = "162"
        assert token_id in node.tokens, f"Token ID {token_id} should exist in node tokens"
        
        # Filter tokens by type
        fbc_tokens = [t for t in node.tokens[token_id] if t.token_type == "FBC"]
        rpc_tokens = [t for t in node.tokens[token_id] if t.token_type == "RPC"]
        
        # Verify we have exactly one FBC token and one RPC token with the same ID
        assert len(fbc_tokens) == 1, f"Should have exactly one FBC token with ID {token_id}"
        assert len(rpc_tokens) == 1, f"Should have exactly one RPC token with ID {token_id}"
        
        # Verify token properties
        fbc_token = fbc_tokens[0]
        rpc_token = rpc_tokens[0]
        
        assert fbc_token.token_type == "FBC", f"FBC token should have FBC type"
        assert rpc_token.token_type == "RPC", f"RPC token should have RPC type"
        
        assert fbc_token.ip_address == "192.168.0.11", f"FBC token should have correct IP"
        assert rpc_token.ip_address == "192.168.0.11", f"RPC token should have correct IP"
        
        # Verify they are different objects
        assert fbc_token is not rpc_token, "FBC and RPC tokens should be different objects"
        
        # Verify they have the same node name
        assert fbc_token.name == "AP01m", "FBC token should have correct node name"
        assert rpc_token.name == "AP01m", "RPC token should have correct node name"