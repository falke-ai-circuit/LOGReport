"""
Test file for validating FBC token detection for node AP01m
"""
import os
import sys
import pytest
from unittest.mock import MagicMock, patch

# Add src directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

from commander.node_manager import NodeManager
from commander.models import Node
from commander.services.fbc_command_service import FbcCommandService
from commander.command_queue import CommandQueue
from commander.log_writer import LogWriter


class TestFbcTokenDetection:
    """Test suite for FBC token detection functionality"""
    
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
        test_logs_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'test_logs', 'FBC')
        manager.set_log_root(test_logs_dir)
        return manager
    
    @pytest.fixture
    def fbc_service(self, node_manager):
        """Create an FBC command service"""
        command_queue = CommandQueue()
        log_writer = LogWriter(node_manager)
        service = FbcCommandService(node_manager, command_queue, log_writer)
        return service
    
    def test_ap01m_fbc_tokens_detection(self, node_manager):
        """Test that all FBC tokens (162, 163, 164) are detected for node AP01m"""
        # Scan log files
        node_manager.scan_log_files()
        
        # Get AP01m node
        node = node_manager.get_node("AP01m")
        assert node is not None, "AP01m node should exist"
        
        # Check that all FBC tokens are detected
        # Flatten the token lists and filter for FBC tokens
        fbc_tokens = []
        for token_list in node.tokens.values():
            for token in token_list:
                if token.token_type == "FBC":
                    fbc_tokens.append(token)
        token_ids = [t.token_id for t in fbc_tokens]
        
        # Verify all three FBC tokens are present
        expected_tokens = {"162", "163", "164"}
        detected_tokens = set(token_ids)
        
        assert expected_tokens.issubset(detected_tokens), \
            f"Expected FBC tokens {expected_tokens}, but got {detected_tokens}"
        
        # Verify each token has the correct properties
        for token_id in expected_tokens:
            token = next((t for t in fbc_tokens if t.token_id == token_id), None)
            assert token is not None, f"Token {token_id} should exist"
            assert token.token_type == "FBC", f"Token {token_id} should be FBC type"
            assert token.ip_address == "192.168.0.11", f"Token {token_id} should have correct IP"
    
    def test_print_all_fbc_tokens_command(self, node_manager, fbc_service):
        """Test the 'Print all FBC tokens' command functionality"""
        # Scan log files
        node_manager.scan_log_files()
        
        # Get AP01m node
        node = node_manager.get_node("AP01m")
        assert node is not None, "AP01m node should exist"
        
        # Get FBC tokens
        # Flatten the token lists and filter for FBC tokens
        fbc_tokens = []
        for token_list in node.tokens.values():
            for token in token_list:
                if token.token_type == "FBC":
                    fbc_tokens.append(token)
        assert len(fbc_tokens) >= 3, "Should have at least 3 FBC tokens"
        
        # Mock command queue to capture commands
        with patch.object(fbc_service.command_queue, 'add_command') as mock_add_command:
            # Process all FBC tokens (simulating "Print all FBC tokens" command)
            for token in fbc_tokens:
                fbc_service.queue_fieldbus_command("AP01m", token.token_id)
            
            # Verify that commands were queued for all tokens
            assert mock_add_command.call_count == len(fbc_tokens), \
                f"Expected {len(fbc_tokens)} commands to be queued"
            
            # Verify each command
            expected_tokens = {"162", "163", "164"}
            queued_tokens = set()
            
            for call_args in mock_add_command.call_args_list:
                command, token, _ = call_args[0]
                queued_tokens.add(token.token_id)
                # Verify command format
                # For FBC tokens, they should be normalized to 3-digit format
                normalized_token = token.token_id.zfill(3) if token.token_id.isdigit() else token.token_id
                expected_command = f"print from fbc io structure {normalized_token}0000"
                assert command == expected_command, \
                    f"Command format incorrect for token {token.token_id}"
            
            # Verify all expected tokens were queued
            assert expected_tokens.issubset(queued_tokens), \
                f"Expected tokens {expected_tokens} to be queued, but got {queued_tokens}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])