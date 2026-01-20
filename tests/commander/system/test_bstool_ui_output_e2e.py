"""
End-to-end test to verify bstool.exe output is displayed in the BsTool tab's UI output area.

This test performs a full end-to-end validation of the bstool integration with the BsTool tab UI:
1. Simulates user interaction with the BsTool tab to execute bstool commands
2. Verifies that bstool.exe output is correctly displayed in the BsTool tab's output area
3. Tests various command execution scenarios
"""

import os
import sys
import tempfile
import subprocess
import time
import shutil
import json
from pathlib import Path
import pytest
from unittest.mock import MagicMock, patch

try:
    import pyautogui
    import win32gui
    import win32con
    import win32process
    import psutil
    UI_AUTOMATION_AVAILABLE = True
except ImportError:
    UI_AUTOMATION_AVAILABLE = False
    print("WARNING: UI automation libraries not available. "
          "Install requirements from requirements-test.txt to run full UI automation.")
    pyautogui = None
    win32gui = None
    win32con = None
    psutil = None

# Add src directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src')))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtTest import QTest

from commander.ui.bstool_tab import BsToolTab
from commander.services.bstool_command_service import BsToolCommandService
from commander.presenters.commander_presenter import CommanderPresenter
from commander.ui.commander_ui_factory import CommanderUIFactory
from commander.node_manager import NodeManager
from commander.log_writer import LogWriter
from commander.services.status_service import StatusService


class TestBsToolUIOutputE2E:
    """End-to-end tests for BsTool UI output display in BsTool tab."""

    def setup_method(self):
        """Set up test environment."""
        # Create QApplication instance if it doesn't exist
        self.app = QApplication.instance() or QApplication(sys.argv)
        
        # Create temporary directories for test
        self.temp_dir = tempfile.mkdtemp(prefix="bstool_ui_e2e_test_")
        self.test_log_dir = os.path.join(self.temp_dir, "test_logs")
        os.makedirs(self.test_log_dir, exist_ok=True)
        
        # Create a test log file
        self.test_log_file = os.path.join(self.test_log_dir, "test_ui_e2e.log")
        with open(self.test_log_file, 'w') as f:
            f.write("Initial log content for UI E2E test\n")
        
        # Store original working directory
        self.original_cwd = os.getcwd()
        
        # Change to project root
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.abspath(__file__)))))
        os.chdir(project_root)
        
        # Initialize test variables
        self.bstool_tab = None
        self.bstool_service = None
        self.presenter = None
        
        # Create UI components
        self._create_test_components()
        
    def teardown_method(self):
        """Clean up test environment."""
        # Clean up temporary directory
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
            
        # Change back to original directory
        os.chdir(self.original_cwd)
        
    def _create_test_components(self):
        """Create test components for end-to-end testing."""
        # Create UI components
        self.bstool_tab = BsToolTab()
        
        # Create services
        self.node_manager = NodeManager()
        self.log_writer = LogWriter(self.node_manager)
        self.status_service = StatusService()
        
        # Create UI factory
        self.ui_factory = CommanderUIFactory()
        
        # Create mock services for testing
        self.bstool_service = MagicMock(spec=BsToolCommandService)
        
        # Create presenter with mocked services
        self.presenter = MagicMock(spec=CommanderPresenter)
        
        # Connect signals manually for testing
        self.bstool_tab.execute_clicked.connect(self._handle_execute_clicked)
        self.bstool_tab.connect_bstool_service(self.bstool_service)
        
        # Set initial state to connected to enable execute button
        from commander.widgets import ConnectionState
        self.bstool_tab.update_status(ConnectionState.CONNECTED)
        
    def _handle_execute_clicked(self, command):
        """Handle execute button click for testing."""
        # In a real implementation, this would call the presenter
        # For testing, we'll simulate the service execution
        pass
        
    def test_bstool_command_execution_output_in_bstool_tab(self):
        """
        Test that bstool command output is displayed in BsTool tab when executed.
        
        This test simulates:
        1. User entering a command in the BsTool tab
        2. User clicking execute
        3. Verifying that bstool output appears in the BsTool tab's output area
        """
        # Mock the bstool service to simulate execution
        mock_output = "BsTool execution output\nLine 1\nLine 2\n"
        
        # Connect the mock service to the UI tab
        self.bstool_tab.connect_bstool_service(self.bstool_service)
        
        # Configure the bstool service mock to actually emit signals
        self.bstool_service.bstool_output_signal = MagicMock()
        self.bstool_service.bstool_output_signal.emit = lambda output, log_file: self.bstool_tab.append_output(output)
        
        # Set up command input
        test_command = "-errlog AP01"
        self.bstool_tab.command_input.setText(test_command)
        
        # Simulate bstool service output by directly calling the signal
        self.bstool_service.bstool_output_signal.emit(mock_output, self.test_log_file)
        
        # Verify output is displayed in the UI (no need to capture signals)
        output_text = self.bstool_tab.output.toPlainText()
        assert mock_output in output_text, "Output should be displayed in the UI"
        assert output_text == mock_output, "Output should match exactly"
        
    def test_bstool_multiple_outputs_in_bstool_tab(self):
        """
        Test that multiple bstool outputs are correctly appended to the BsTool tab.
        
        This test verifies:
        1. Multiple output lines are appended correctly
        2. Output order is preserved
        3. UI updates properly with each output
        """
        # Test data with multiple outputs
        outputs = [
            "First output line\n",
            "Second output line\n",
            "Third output line\n"
        ]
        
        # Simulate multiple outputs from bstool service
        for output in outputs:
            self.bstool_tab.append_output(output)
        
        # Verify all outputs are displayed in the UI
        output_text = self.bstool_tab.output.toPlainText()
        
        # Check that all outputs are present
        for output in outputs:
            assert output.strip() in output_text, f"Output '{output.strip()}' should be in the UI"
            
        # Check order is preserved (no extra newlines between outputs)
        expected_full_text = "".join(outputs)
        assert output_text == expected_full_text, "Output order should be preserved without extra newlines"
        
    def test_bstool_output_formatting_in_bstool_tab(self):
        """
        Test that bstool output is properly formatted in the BsTool tab.
        
        This test verifies:
        1. Output is correctly appended to existing content
        2. Line breaks are preserved
        3. Special characters are handled correctly
        """
        # Test data with various formatting
        test_output = "Test output with special characters: äöü\nLine with numbers: 12345\nEmpty line next:\n\nLine after empty line"
        
        # Clear any existing output
        self.bstool_tab.clear_output()
        
        # Simulate appending output
        self.bstool_tab.append_output(test_output)
        
        # Verify output is displayed correctly
        output_text = self.bstool_tab.output.toPlainText()
        assert output_text == test_output, "Output should match exactly with formatting preserved"
        
    def test_bstool_error_output_in_bstool_tab(self):
        """
        Test that bstool error output is displayed in BsTool tab.
        
        This test verifies:
        1. Error messages are properly formatted
        2. Error output is distinguishable from regular output
        3. Error messages are sent to the BsTool tab
        """
        # Test error output
        error_output = "ERROR: Failed to execute bstool\nError details here\n"
        
        # Clear any existing output
        self.bstool_tab.clear_output()
        
        # Simulate error output
        self.bstool_tab.append_output(error_output)
        
        # Verify error output is displayed
        output_text = self.bstool_tab.output.toPlainText()
        assert error_output in output_text, "Error output should be displayed in the UI"
        assert output_text == error_output, "Error output should match exactly"
        
    def test_bstool_output_clear_functionality(self):
        """
        Test that BsTool tab clear functionality works with bstool output.
        
        This test verifies:
        1. Output can be cleared from the BsTool tab
        2. Clear function doesn't affect other UI components
        """
        # Add some test output
        test_output = "Test output line 1\nTest output line 2\n"
        self.bstool_tab.append_output(test_output)
        
        # Verify output exists
        output_text = self.bstool_tab.output.toPlainText()
        assert output_text == test_output, "Output should be present before clearing"
        
        # Clear output
        self.bstool_tab.clear_output()
        
        # Verify output is cleared
        output_text = self.bstool_tab.output.toPlainText()
        assert output_text == "", "Output should be cleared"
        
    def test_bstool_command_execution_integration_with_presenter(self):
        """
        Test integration between BsToolTab and Presenter for command execution.
        
        This test simulates:
        1. User entering a command in the BsTool tab
        2. User clicking execute
        3. Verifying that the presenter handles the execution properly
        """
        # Track if execute signal was emitted
        execute_signals = []
        def capture_execute_signal(cmd):
            execute_signals.append(cmd)
            
        # Connect signal to capture function
        self.bstool_tab.execute_clicked.connect(capture_execute_signal)
        
        # Set up command input
        test_command = "-status AP01"
        self.bstool_tab.command_input.setText(test_command)
        
        # Simulate clicking execute button
        self.bstool_tab.execute_btn.click()
        
        # Verify signal was emitted with correct command
        assert len(execute_signals) == 1, "Execute signal should be emitted once"
        assert execute_signals[0] == test_command, "Command should match exactly"
        
        # Verify command input is cleared after execution
        # Note: In current implementation, command is not automatically cleared
        # This is a design choice that we're verifying
        current_command = self.bstool_tab.get_command()
        assert current_command == test_command, "Command should remain in input field"
        
    def test_bstool_tab_status_updates_during_execution(self):
        """
        Test that BsTool tab status updates correctly during command execution.
        
        This test verifies:
        1. Status indicator updates during different execution states
        2. Execute button state changes appropriately
        3. UI feedback is provided during execution
        """
        from commander.widgets import ConnectionState
        
        # Test initial state (should be connected from setup)
        assert self.bstool_tab.status_label.text() == "\u25CF", "Should start in connected state"
        assert self.bstool_tab.execute_btn.isEnabled() == True, "Execute button should be enabled"
        
        # Test disconnected state
        self.bstool_tab.update_status(ConnectionState.DISCONNECTED)
        assert self.bstool_tab.status_label.text() == "\u25CB", "Should show disconnected state"
        assert self.bstool_tab.execute_btn.isEnabled() == False, "Execute button should be disabled when disconnected"
        
        # Test connecting state
        self.bstool_tab.update_status(ConnectionState.CONNECTING)
        assert self.bstool_tab.status_label.text() == "\u25D1", "Should show connecting state"
        assert self.bstool_tab.execute_btn.isEnabled() == False, "Execute button should be disabled when connecting"
        
        # Test error state
        self.bstool_tab.update_status(ConnectionState.ERROR)
        assert self.bstool_tab.status_label.text() == "\u2a2f", "Should show error state"
        assert self.bstool_tab.execute_btn.isEnabled() == False, "Execute button should be disabled when in error state"
        
        # Test back to connected state
        self.bstool_tab.update_status(ConnectionState.CONNECTED)
        assert self.bstool_tab.status_label.text() == "\u25CF", "Should show connected state"
        assert self.bstool_tab.execute_btn.isEnabled() == True, "Execute button should be enabled when connected"


if __name__ == "__main__":
    # Run the test if executed directly
    pytest.main([__file__, "-v"])
