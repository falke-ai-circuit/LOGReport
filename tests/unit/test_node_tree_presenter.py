import unittest
import os
from unittest.mock import Mock, patch
from src.commander.presenters.node_tree_presenter import NodeTreePresenter
from src.commander.node_manager import NodeManager

class TestNodeTreePresenter(unittest.TestCase):

    def setUp(self):
        self.mock_view = Mock()
        self.mock_node_manager = Mock(spec=NodeManager)
        self.mock_session_manager = Mock()
        self.mock_log_writer = Mock()
        self.mock_command_queue = Mock()
        self.mock_fbc_service = Mock()
        self.mock_rpc_service = Mock()
        self.mock_context_menu_service = Mock()
        self.mock_bstool_service = Mock()

        self.presenter = NodeTreePresenter(
            self.mock_view,
            self.mock_node_manager,
            self.mock_session_manager,
            self.mock_log_writer,
            self.mock_command_queue,
            self.mock_fbc_service,
            self.mock_rpc_service,
            self.mock_context_menu_service,
            self.mock_bstool_service
        )

    def test_extract_node_id_from_log_path_truncation(self):
        # Test case 1: Node name ends with 'm' and is longer than 2 characters
        log_path_m = "/path/to/logs/LOG/AP01m_192-168-0-11.log"
        expected_node_id_m = "AP01"
        actual_node_id_m = self.presenter._extract_node_id_from_log_path(log_path_m)
        self.assertEqual(actual_node_id_m, expected_node_id_m, f"Failed for {log_path_m}")

        # Test case 2: Node name ends with 'r' and is longer than 2 characters
        log_path_r = "/path/to/logs/LOG/AP02r_192-168-0-12.log"
        expected_node_id_r = "AP02"
        actual_node_id_r = self.presenter._extract_node_id_from_log_path(log_path_r)
        self.assertEqual(actual_node_id_r, expected_node_id_r, f"Failed for {log_path_r}")

        # Test case 3: Node name does not end with 'm' or 'r'
        log_path_no_trunc = "/path/to/logs/LOG/AP03_192-168-0-13.log"
        expected_node_id_no_trunc = "AP03"
        actual_node_id_no_trunc = self.presenter._extract_node_id_from_log_path(log_path_no_trunc)
        self.assertEqual(actual_node_id_no_trunc, expected_node_id_no_trunc, f"Failed for {log_path_no_trunc}")

        # Test case 4: Node name is 2 characters long (should not truncate)
        log_path_short = "/path/to/logs/LOG/AAm_192-168-0-14.log"
        expected_node_id_short = "AAm"
        actual_node_id_short = self.presenter._extract_node_id_from_log_path(log_path_short)
        self.assertEqual(actual_node_id_short, expected_node_id_short, f"Failed for {log_path_short}")

        # Test case 5: Non-LOG file type (should not truncate)
        log_path_fbc = "/path/to/logs/FBC/AP01m_192-168-0-11.fbc"
        expected_node_id_fbc = "AP01m"
        actual_node_id_fbc = self.presenter._extract_node_id_from_log_path(log_path_fbc)
        self.assertEqual(actual_node_id_fbc, expected_node_id_fbc, f"Failed for {log_path_fbc}")

        # Test case 6: Log file with multiple extensions
        log_path_multi_ext = "/path/to/logs/LOG/AP01m_192-168-0-11.rpc.log"
        expected_node_id_multi_ext = "AP01"
        actual_node_id_multi_ext = self.presenter._extract_node_id_from_log_path(log_path_multi_ext)
        self.assertEqual(actual_node_id_multi_ext, expected_node_id_multi_ext, f"Failed for {log_path_multi_ext}")

        # Test case 7: Log file with no underscore
        log_path_no_underscore = "/path/to/logs/LOG/AP01m.log"
        expected_node_id_no_underscore = "AP01"
        actual_node_id_no_underscore = self.presenter._extract_node_id_from_log_path(log_path_no_underscore)
        self.assertEqual(actual_node_id_no_underscore, expected_node_id_no_underscore, f"Failed for {log_path_no_underscore}")

        # Test case 8: Log file with no underscore and no truncation needed
        log_path_no_underscore_no_trunc = "/path/to/logs/LOG/AP01.log"
        expected_node_id_no_underscore_no_trunc = "AP01"
        actual_node_id_no_underscore_no_trunc = self.presenter._extract_node_id_from_log_path(log_path_no_underscore_no_trunc)
        self.assertEqual(actual_node_id_no_underscore_no_trunc, expected_node_id_no_underscore_no_trunc, f"Failed for {log_path_no_underscore_no_trunc}")

if __name__ == '__main__':
    unittest.main()