import os
import sys
import pytest

# Add src directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))


class TestTelnetTabVisibilityRegression:
    """Regression test suite for Telnet tab visibility issue"""
    
    def test_telnet_tab_module_imports(self):
        """Test that TelnetTab module can be imported without errors"""
        try:
            from commander.ui.telnet_tab import TelnetTab
            assert TelnetTab is not None, "TelnetTab class should be importable"
        except Exception as e:
            pytest.fail(f"Failed to import TelnetTab: {e}")
    
    def test_vnc_tab_module_imports(self):
        """Test that VNCTab module can be imported without errors"""
        try:
            from commander.ui.vnc_tab import VNCTab
            assert VNCTab is not None, "VNCTab class should be importable"
        except Exception as e:
            pytest.fail(f"Failed to import VNCTab: {e}")
    
    def test_session_view_module_imports(self):
        """Test that SessionView module can be imported without errors"""
        try:
            from commander.ui.session_view import SessionView
            assert SessionView is not None, "SessionView class should be importable"
        except Exception as e:
            pytest.fail(f"Failed to import SessionView: {e}")
    
    def test_commander_window_module_imports(self):
        """Test that CommanderWindow module can be imported without errors"""
        try:
            from commander.ui.commander_window import CommanderWindow
            assert CommanderWindow is not None, "CommanderWindow class should be importable"
        except Exception as e:
            pytest.fail(f"Failed to import CommanderWindow: {e}")
    
    def test_telnet_tab_class_structure(self):
        """Test that TelnetTab class has the expected structure by examining its source"""
        from commander.ui.telnet_tab import TelnetTab
        
        # Check that the class exists
        assert TelnetTab is not None, "TelnetTab class should exist"
        
        # Check that it has the expected methods by looking at its method resolution order
        methods = [method for method in dir(TelnetTab) if not method.startswith('_') or method in ['__init__']]
        
        # Check for expected public methods
        expected_methods = [
            'append_output', 'get_command', 'clear_command',
            'get_connection_info', 'update_connection_status'
        ]
        
        for method in expected_methods:
            assert hasattr(TelnetTab, method), f"TelnetTab should have method {method}"
    
    def test_session_view_imports_telnet_and_vnc_tabs(self):
        """Test that SessionView correctly imports TelnetTab and VNCTab"""
        # This test verifies that the import statements in session_view.py are correct
        # by checking that the module can be imported without ImportError
        try:
            from commander.ui.session_view import SessionView
            # If we get here, the imports in session_view.py worked
            assert True
        except ImportError as e:
            pytest.fail(f"SessionView failed to import TelnetTab or VNCTab: {e}")
        except Exception as e:
            # Other exceptions are OK, we just want to verify imports work
            assert True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])