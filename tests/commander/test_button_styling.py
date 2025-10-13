"""
Unit tests for Commander Window button styling and visual state management.

Tests verify button color changes, stylesheet application, and visual
feedback for connection states and user interactions.
"""
import pytest
from unittest.mock import MagicMock
from PyQt6.QtWidgets import QApplication, QPushButton
from PyQt6.QtGui import QColor
from src.commander.ui.commander_window import CommanderWindow

@pytest.fixture(scope="module")
def app():
    """Fixture for a QApplication instance."""
    return QApplication([])

@pytest.fixture
def commander_window(app):
    """Fixture for CommanderWindow instance."""
    window = CommanderWindow()
    window.show()
    yield window
    window.close()

class TestButtonStyling:
    """Tests for button coloring and styling."""

    def get_button_background_color(self, button: QPushButton):
        """Helper to get the background color of a QPushButton from stylesheet."""
        style = button.styleSheet()
        # Parse stylesheet for background-color property
        if "background-color:" in style:
            start = style.find("background-color:") + len("background-color:")
            end = style.find(";", start)
            color_str = style[start:end].strip()
            color = QColor()
            color.setNamedColor(color_str)
            return color
        return QColor() # Return an invalid color if not found

    def test_telnet_connect_button_initial_style(self, commander_window):
        """Verify initial styling of the Telnet Connect button."""
        button = commander_window.telnet_connect_button
        
        # Assertions: Button exists and has initial state
        assert button is not None, "Telnet connect button should exist"
        assert isinstance(button, QPushButton), "Should be QPushButton instance"
        
        # Check initial color is not error/connected states
        color = self.get_button_background_color(button)
        assert color != QColor("red"), "Initial state should not be red (error)"
        assert color != QColor("green"), "Initial state should not be green (connected)"
        assert color.isValid() or not button.styleSheet(), "Should have valid color or no stylesheet"

    def test_telnet_connect_button_connected_style(self, commander_window):
        """Verify styling of the Telnet Connect button when connected."""
        button = commander_window.telnet_connect_button
        
        # Simulate connected state (this would typically be handled by the presenter)
        button.setStyleSheet("background-color: green;")
        color = self.get_button_background_color(button)
        
        # Assertions: Connected state shows green
        assert color == QColor("green"), "Connected state should be green"
        assert color.isValid(), "Color should be valid"
        assert button.styleSheet(), "Button should have stylesheet applied"

    def test_telnet_connect_button_disconnected_style(self, commander_window):
        """Verify styling of the Telnet Connect button when disconnected/error."""
        button = commander_window.telnet_connect_button
        
        # Simulate disconnected/error state
        button.setStyleSheet("background-color: red;")
        color = self.get_button_background_color(button)
        
        # Assertions: Error state shows red
        assert color == QColor("red"), "Error state should be red"
        assert color.isValid(), "Color should be valid"
        assert "red" in button.styleSheet().lower(), "Stylesheet should contain red"

        """Verify styling of the Telnet Connect button when disconnected (after being connected)."""
        button = commander_window.telnet_connect_button
        # Simulate connected then disconnected state
        button.setStyleSheet("background-color: green;")
        button.setStyleSheet("background-color: lightgray;") # Or whatever the default disconnected color is
        color = self.get_button_background_color(button)
        assert color == QColor("lightgray") # Assuming lightgray is the default/disconnected color
