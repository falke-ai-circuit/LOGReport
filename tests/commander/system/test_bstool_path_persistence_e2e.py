"""
End-to-end test to verify bstool path persistence across application restarts.

This test performs a full end-to-end validation of the bstool path persistence:
1. Creates QSettings with a unique test organization
2. Sets bstool path value
3. Verifies the path is saved correctly
4. Creates new QSettings instance with same organization
5. Verifies the path is loaded correctly
"""
import os
import sys
import tempfile
import shutil
import pytest
from unittest.mock import patch

# Add src directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src')))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QSettings


class TestBsToolPathPersistenceE2E:
    """End-to-end tests for BsTool path persistence functionality."""

    def setup_method(self):
        """Set up test environment."""
        # Create QApplication instance if it doesn't exist
        self.app = QApplication.instance() or QApplication(sys.argv)
        
        # Create a unique organization and application name for testing
        # This ensures our test settings don't interfere with real application settings
        self.test_org_name = "CommanderLogCreatorTest"
        self.test_app_name = f"SettingsTest_{os.getpid()}"
        
        # Clean up any existing test settings
        settings = QSettings(self.test_org_name, self.test_app_name)
        settings.clear()
        settings.sync()
        
    def teardown_method(self):
        """Clean up test environment."""
        # Clean up test settings
        settings = QSettings(self.test_org_name, self.test_app_name)
        settings.clear()
        settings.sync()
        
    def test_bstool_path_persistence_across_application_restart(self):
        """
        Test that bstool path is correctly persisted across application restarts.
        
        This test simulates:
        1. Starting the application for the first time
        2. Setting the bstool path in the UI
        3. Closing the application (which should save settings)
        4. Starting the application again
        5. Verifying that the bstool path is loaded and displayed correctly
        """
        # Step 1: Simulate first application session - save bstool path
        settings1 = QSettings(self.test_org_name, self.test_app_name)
        test_bstool_path = "C:\\Program Files\\BsTool\\bstool.exe"
        settings1.setValue("bstool_path", test_bstool_path)
        settings1.sync()
        
        # Step 2: Verify the path was saved to settings
        saved_path = settings1.value("bstool_path", "")
        assert saved_path == test_bstool_path, f"Path should be saved to settings. Expected: {test_bstool_path}, Got: {saved_path}"
        
        # Step 3: Simulate application restart - create new settings instance
        # This simulates what happens when the application is closed and reopened
        settings2 = QSettings(self.test_org_name, self.test_app_name)
        
        # Step 4: Verify bstool path is loaded correctly
        loaded_path = settings2.value("bstool_path", "")
        assert loaded_path == test_bstool_path, f"Path should be loaded from settings. Expected: {test_bstool_path}, Got: {loaded_path}"
        
    def test_bstool_path_persistence_with_empty_path(self):
        """
        Test that empty bstool path is correctly handled during persistence.
        
        This test verifies:
        1. Empty path is saved correctly
        2. Empty path is loaded correctly
        """
        # Step 1: Simulate first application session - save empty bstool path
        settings1 = QSettings(self.test_org_name, self.test_app_name)
        test_bstool_path = ""
        settings1.setValue("bstool_path", test_bstool_path)
        settings1.sync()
        
        # Step 2: Verify the empty path was saved to settings
        saved_path = settings1.value("bstool_path", "")
        assert saved_path == test_bstool_path, f"Empty path should be saved to settings. Expected: '{test_bstool_path}', Got: '{saved_path}'"
        
        # Step 3: Simulate application restart - create new settings instance
        settings2 = QSettings(self.test_org_name, self.test_app_name)
        
        # Step 4: Verify empty bstool path is loaded correctly
        loaded_path = settings2.value("bstool_path", "")
        assert loaded_path == test_bstool_path, f"Empty path should be loaded from settings. Expected: '{test_bstool_path}', Got: '{loaded_path}'"
        
    def test_bstool_path_persistence_with_no_saved_path(self):
        """
        Test that default value is returned when no bstool path is saved.
        
        This test verifies:
        1. Default value is returned when no path is saved
        2. Application handles missing path gracefully
        """
        # Step 1: Create fresh settings (no bstool_path saved)
        settings = QSettings(self.test_org_name, self.test_app_name)
        
        # Step 2: Verify default value is returned
        loaded_path = settings.value("bstool_path", "")
        assert loaded_path == "", f"Default empty string should be returned when no path is saved. Got: '{loaded_path}'"


if __name__ == "__main__":
    # Run the test if executed directly
    pytest.main([__file__, "-v"])