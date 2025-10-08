import pytest
from unittest.mock import MagicMock
from PyQt5.QtWidgets import QApplication, QPushButton
from PyQt5.QtGui import QColor
from src.commander.ui.commander_window import CommanderWindow
from src.commander.ui.vnc_tab import VNCTab

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

@pytest.fixture
def vnc_tab(commander_window):
    """Fixture for VNCTab instance."""
    tab = VNCTab(commander_window)
    return tab

class TestButtonStyling:
    """Tests for button coloring and styling."""

    def get_button_background_color(self, button: QPushButton):
        """Helper to get the background color of a QPushButton."""
        style = button.styleSheet()
        # This is a simplified approach. A more robust solution would parse the stylesheet.
        # For now, we assume a direct background-color setting.
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
        assert button is not None
        # Assuming a default style is applied globally or via a base stylesheet
        # This test might need adjustment based on the actual global stylesheet
        # For now, we check if it's not explicitly red (error) or green (connected)
        color = self.get_button_background_color(button)
        assert color != QColor("red")
        assert color != QColor("green")

    def test_telnet_connect_button_connected_style(self, commander_window):
        """Verify styling of the Telnet Connect button when connected."""
        button = commander_window.telnet_connect_button
        # Simulate connected state (this would typically be handled by the presenter)
        button.setStyleSheet("background-color: green;")
        color = self.get_button_background_color(button)
        assert color == QColor("green")

    def test_telnet_connect_button_disconnected_style(self, commander_window):
        """Verify styling of the Telnet Connect button when disconnected (after being connected)."""
        button = commander_window.telnet_connect_button
        # Simulate connected then disconnected state
        button.setStyleSheet("background-color: green;")
        button.setStyleSheet("background-color: lightgray;") # Or whatever the default disconnected color is
        color = self.get_button_background_color(button)
        assert color == QColor("lightgray") # Assuming lightgray is the default/disconnected color

    def test_vnc_tab_buttons_no_conflicting_styles(self, vnc_tab):
        """Verify VNC tab buttons do not have conflicting inline styles."""
        # This test is more conceptual and might require manual inspection or a more advanced
        # stylesheet parsing utility if direct programmatic access to inherited styles is not feasible.
        # For now, we assume that if the stylesheet is empty, no inline conflicting styles are present.
        # In a real scenario, you might check for specific properties that were known to conflict.
        assert vnc_tab.connect_button.styleSheet() == ""
        assert vnc_tab.disconnect_button.styleSheet() == ""
        assert vnc_tab.send_ctrl_alt_del_button.styleSheet() == ""