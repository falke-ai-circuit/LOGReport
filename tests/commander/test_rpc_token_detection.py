import os
import sys
import pytest

# Add src directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

from commander.node_manager import NodeManager
from commander.models import Node

class TestRpcTokenDetection:
    @pytest.fixture
    def node_manager(self):
        manager = NodeManager()
        test_config_path = os.path.join(os.path.dirname(__file__), '..', 'test_nodes.json')
        manager.set_config_path(test_config_path)
        manager.load_configuration()
        test_logs_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'test_logs')
        manager.set_log_root(test_logs_dir)
        return manager

    def test_ap01m_rpc_tokens_detection(self, node_manager):
        # Scan log files
        node_manager.scan_log_files()

        # Get AP01m node
        node = node_manager.get_node("AP01m")
        assert node is not None, "AP01m node should exist"

        # Check that all RPC tokens are detected
        rpc_tokens = [t for t in node.tokens.values() if t.token_type == "RPC"]
        token_ids = [t.token_id for t in rpc_tokens]

        # Verify all three RPC tokens are present
        expected_tokens = {"162", "163", "164"}
        detected_tokens = set(token_ids)

        assert expected_tokens.issubset(detected_tokens), \
            f"Expected RPC tokens {expected_tokens}, but got {detected_tokens}"

        # Verify each token has the correct properties
        for token_id in expected_tokens:
            token = next((t for t in rpc_tokens if t.token_id == token_id), None)
            assert token is not None, f"Token {token_id} should exist"
            assert token.token_type == "RPC", f"Token {token_id} should be RPC type"
            assert token.ip_address == "192.168.0.11", f"Token {token_id} should have correct IP"