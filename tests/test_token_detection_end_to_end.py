import os
import pytest
import sys
from unittest.mock import MagicMock

# Add src directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from commander.node_manager import NodeManager
from commander.models import Node

# Define test log paths
TEST_LOGS_DIR = os.path.join(os.path.dirname(__file__), '..', 'test_logs')
TEST_CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'test_nodes.json')

# Test cases - (log_path, expected_tokens)
TEST_CASES = [
    # Valid FBC logs - expect all tokens for each node
    (os.path.join(TEST_LOGS_DIR, 'FBC/AP01m/AP01m_192-168-0-11_162.fbc'), {'162','163','164'}),
    (os.path.join(TEST_LOGS_DIR, 'FBC/AP01r/AP01r_192-168-0-27_362.fbc'), {'362','363'}),
    (os.path.join(TEST_LOGS_DIR, 'FBC/AP02m/AP02m_192-168-0-12_182.fbc'), {'182'}),
    
    # Valid RPC logs - expect specific token for each log
    (os.path.join(TEST_LOGS_DIR, 'RPC/AP01m/AP01m_192.168.0.11_163.rpc'), {'163'}),
    (os.path.join(TEST_LOGS_DIR, 'RPC/AP01r/AP01r_192-168-0-27_363.rpc'), {'363'}),
    
    # Edge cases
    (os.path.join(TEST_LOGS_DIR, 'FBC/unknown-node/unknown-node_unknown-ip_unknown-token.fbc'), set()),
    (os.path.join(TEST_LOGS_DIR, 'FBC/NODE/NODE_192.168.0.1_invalid!.fbc'), set()),
    (os.path.join(TEST_LOGS_DIR, 'FBC/NODE1/NODE1_192.168.1.1_123.fbc'), {'123'}),
]

def create_node_manager():
    """Create NodeManager instance for testing"""
    manager = NodeManager()
    # Mock settings
    manager.settings = MagicMock()
    manager.settings.value.return_value = None
    
    # Load test configuration
    manager.load_configuration(TEST_CONFIG_PATH)
    return manager

@pytest.mark.parametrize("log_path, expected_tokens", TEST_CASES)
def test_token_extraction(log_path, expected_tokens):
    """Test token extraction from various log files"""
    manager = create_node_manager()
    
    # Run token extraction
    manager.scan_log_files(os.path.dirname(log_path))
    
    # Find the node from the log path
    node_name = os.path.basename(os.path.dirname(log_path))
    node = manager.get_node(node_name)
    
    # Extract token from log file name
    filename = os.path.basename(log_path)
    token_id = filename.split('_')[-1].split('.')[0]
    
    # For edge cases, we expect no node to be found
    if "unknown" in node_name or "invalid" in filename:
        assert node is None, \
            f"Node {node_name} should not exist for file {filename}"
    else:
        # Verify token exists in node
        token_exists = token_id in {t.token_id for t in node.tokens.values()}
        assert token_exists, \
            f"Token {token_id} not found in node {node_name} for file {filename}"

def test_all_token_scenarios():
    """End-to-end test of all token detection scenarios"""
    manager = create_node_manager()
    
    for log_path, expected_tokens in TEST_CASES:
        # Run token extraction for each log file
        manager.scan_log_files(os.path.dirname(log_path))
        
        # Find the node from the log path
        node_name = os.path.basename(os.path.dirname(log_path))
        node = manager.get_node(node_name)
        
        # Extract token from log file name
        filename = os.path.basename(log_path)
        token_id = filename.split('_')[-1].split('.')[0]
        
        # For edge cases, we expect no node to be found
        if "unknown" in node_name or "invalid" in filename:
            assert node is None, \
                f"Node {node_name} should not exist for file {filename}"
        else:
            # Verify token exists in node
            token_exists = token_id in {t.token_id for t in node.tokens.values()}
            assert token_exists, \
                f"Token {token_id} not found in node {node_name} for file {filename}"