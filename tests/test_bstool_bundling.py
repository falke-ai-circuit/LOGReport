"""
Test BsTool.exe bundling and path detection functionality.

Tests verify:
1. Path detection in development mode
2. Path detection in frozen mode (PyInstaller)
3. sys._MEIPASS handling
4. Fallback behavior
"""

import os
import sys
import unittest
from unittest.mock import Mock, patch, MagicMock
import tempfile

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))


class TestBsToolPathDetection(unittest.TestCase):
    """Test BsTool.exe path detection across different environments"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Import here to avoid issues with mocking
        from commander.services.bstool_command_service import BsToolCommandService
        self.service_class = BsToolCommandService
        
    def test_development_mode_path_detection(self):
        """Test path detection in development (non-frozen) mode"""
        with patch.object(sys, 'frozen', False, create=True):
            service = self.service_class()
            path = service._get_bstool_path()
            
            # Should return path relative to project root
            self.assertIn("BsTool.exe", path)
            self.assertIsInstance(path, str)
            
    def test_frozen_mode_with_meipass(self):
        """Test path detection in frozen mode with sys._MEIPASS"""
        with tempfile.TemporaryDirectory() as temp_dir:
            bstool_path = os.path.join(temp_dir, "BsTool.exe")
            
            # Create dummy BsTool.exe
            with open(bstool_path, 'w') as f:
                f.write("dummy")
            
            with patch.object(sys, 'frozen', True, create=True):
                with patch.object(sys, '_MEIPASS', temp_dir, create=True):
                    service = self.service_class()
                    detected_path = service._get_bstool_path()
                    
                    # Should find BsTool.exe in _MEIPASS
                    self.assertEqual(detected_path, bstool_path)
                    self.assertTrue(os.path.exists(detected_path))
                    
    def test_frozen_mode_fallback_to_executable_dir(self):
        """Test fallback to sys.executable directory when _MEIPASS not found"""
        with tempfile.TemporaryDirectory() as temp_dir:
            fake_executable = os.path.join(temp_dir, "LOGReporter.exe")
            
            with patch.object(sys, 'frozen', True, create=True):
                # Mock sys._MEIPASS to point to non-existent BsTool.exe
                with patch.object(sys, '_MEIPASS', "/non/existent", create=True):
                    with patch.object(sys, 'executable', fake_executable):
                        service = self.service_class()
                        detected_path = service._get_bstool_path()
                        
                        # Should fallback to executable directory
                        expected_path = os.path.join(temp_dir, "BsTool.exe")
                        self.assertEqual(detected_path, expected_path)
                        
    def test_frozen_mode_without_meipass(self):
        """Test frozen mode when sys._MEIPASS doesn't exist"""
        with tempfile.TemporaryDirectory() as temp_dir:
            fake_executable = os.path.join(temp_dir, "LOGReporter.exe")
            
            with patch.object(sys, 'frozen', True, create=True):
                # Ensure _MEIPASS doesn't exist
                if hasattr(sys, '_MEIPASS'):
                    delattr(sys, '_MEIPASS')
                    
                with patch.object(sys, 'executable', fake_executable):
                    service = self.service_class()
                    detected_path = service._get_bstool_path()
                    
                    # Should use executable directory
                    expected_path = os.path.join(temp_dir, "BsTool.exe")
                    self.assertEqual(detected_path, expected_path)
                    
    def test_path_detection_returns_string(self):
        """Ensure path detection always returns a string"""
        service = self.service_class()
        path = service._get_bstool_path()
        
        self.assertIsInstance(path, str)
        self.assertGreater(len(path), 0)
        
    def test_bstool_exe_filename_in_path(self):
        """Verify BsTool.exe is in the detected path"""
        service = self.service_class()
        path = service._get_bstool_path()
        
        self.assertTrue(path.endswith("BsTool.exe"))


class TestBsToolBundlingConfiguration(unittest.TestCase):
    """Test PyInstaller spec configuration for BsTool bundling"""
    
    def test_spec_file_exists(self):
        """Verify LOGReporter.spec exists"""
        spec_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "LOGReporter.spec")
        self.assertTrue(os.path.exists(spec_path), "LOGReporter.spec not found")
        
    def test_spec_contains_bstool_binary(self):
        """Verify spec file includes BsTool.exe as binary"""
        spec_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "LOGReporter.spec")
        
        with open(spec_path, 'r', encoding='utf-8') as f:
            spec_content = f.read()
            
        self.assertIn("BsTool.exe", spec_content, "BsTool.exe not found in spec binaries")
        
    def test_spec_contains_windows_manifest(self):
        """Verify spec includes custom Windows manifest"""
        spec_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "LOGReporter.spec")
        
        with open(spec_path, 'r', encoding='utf-8') as f:
            spec_content = f.read()
            
        self.assertIn("manifest_xml", spec_content, "manifest_xml not defined in spec")
        
    def test_manifest_includes_windows_server_2012(self):
        """Verify manifest includes Windows Server 2012 support"""
        spec_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "LOGReporter.spec")
        
        with open(spec_path, 'r', encoding='utf-8') as f:
            spec_content = f.read()
            
        # Windows 8 / Server 2012
        self.assertIn("{4a2f28e3-53b9-4441-ba9c-d69d4a4a6e38}", spec_content,
                      "Windows Server 2012 supportedOS ID not found")
        
        # Windows 8.1 / Server 2012 R2
        self.assertIn("{d78f2640-1f3f-11e3-8fae-00144feabdc0}", spec_content,
                      "Windows Server 2012 R2 supportedOS ID not found")


if __name__ == '__main__':
    unittest.main()
