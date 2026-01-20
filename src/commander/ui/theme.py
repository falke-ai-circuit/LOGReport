"""
Theme Module - Centralized color palette and styling for the Commander UI
"""

from typing import Dict, Final


class ColorPalette:
    """Centralized color palette for the Commander application UI."""
    
    # Primary dark theme colors
    BACKGROUND_DARK: Final[str] = "#2D2D30"
    BACKGROUND_MEDIUM: Final[str] = "#3D3D3D"
    BACKGROUND_LIGHT: Final[str] = "#4D4D4D"
    BACKGROUND_HIGHLIGHT: Final[str] = "#5D5D5D"
    
    # Text colors
    TEXT_PRIMARY: Final[str] = "#DCDCDC"
    TEXT_SECONDARY: Final[str] = "#AAAAAA"
    TEXT_DISABLED: Final[str] = "#888888"
    
    # Accent colors
    ACCENT_BLUE: Final[str] = "#007ACC"
    ACCENT_BLUE_HOVER: Final[str] = "#0088E0"
    ACCENT_BLUE_PRESSED: Final[str] = "#0066B3"
    
    # UI element colors
    BORDER_COLOR: Final[str] = "#3E3E42"
    INPUT_BACKGROUND: Final[str] = "#252526"
    # Unified highlight color - grey for subtle highlighting throughout UI
    # Changed from purple (#C969E6) to grey for consistent dark theme
    SELECTION_BACKGROUND: Final[str] = "#5D5D5D"
    
    # Scrollbar colors
    SCROLLBAR_BACKGROUND: Final[str] = "#2D2D30"
    SCROLLBAR_HANDLE: Final[str] = "#5D5D5D"
    SCROLLBAR_HANDLE_HOVER: Final[str] = "#6D6D6D"
    SCROLLBAR_HANDLE_PRESSED: Final[str] = "#4D4D4D"
    
    # Status colors
    STATUS_SUCCESS: Final[str] = "lime"
    STATUS_WARNING: Final[str] = "orange"
    STATUS_ERROR: Final[str] = "red"
    STATUS_DISCONNECTED: Final[str] = "#888"
    
    # Icon colors
    ICON_NODE_ONLINE: Final[str] = "#32A852"  # Green
    ICON_NODE_OFFLINE: Final[str] = "#C8C8C8"  # Gray
    ICON_TOKEN: Final[str] = "#588B8B"  # CadetBlue
    
    # Button specific colors
    BUTTON_BACKGROUND: Final[str] = "#3D3D3D"
    BUTTON_BACKGROUND_HOVER: Final[str] = "#4D4D4D"
    BUTTON_BACKGROUND_PRESSED: Final[str] = "#2D2D2D"
    BUTTON_BACKGROUND_CHECKED: Final[str] = "#5D5D5D"
    BUTTON_BORDER: Final[str] = "#555"
    BUTTON_TEXT: Final[str] = "#DCDCDC"


class StyleSheetManager:
    """Manager for centralized stylesheet definitions."""
    
    @staticmethod
    def get_application_stylesheet() -> str:
        """Get the main application stylesheet."""
        return """
            QMainWindow, QWidget {
                background-color: """ + ColorPalette.BACKGROUND_DARK + """;
                color: """ + ColorPalette.TEXT_PRIMARY + """;
                font-family: Segoe UI;
            }
            QPushButton {
                background-color: """ + ColorPalette.BUTTON_BACKGROUND + """;
                border: 1px solid """ + ColorPalette.BUTTON_BORDER + """;
                padding: 5px 15px;
                min-width: 80px;
                color: """ + ColorPalette.BUTTON_TEXT + """;
            }
            QPushButton:hover {
                background-color: """ + ColorPalette.BUTTON_BACKGROUND_HOVER + """;
            }
            QPushButton:pressed {
                background-color: """ + ColorPalette.BUTTON_BACKGROUND_PRESSED + """;
            }
            QPushButton:checked {
                background-color: """ + ColorPalette.BUTTON_BACKGROUND_CHECKED + """;
                font-weight: bold;
            }
            QLineEdit, QComboBox {
                background-color: """ + ColorPalette.INPUT_BACKGROUND + """;
                color: """ + ColorPalette.TEXT_PRIMARY + """;
                border: 1px solid """ + ColorPalette.BORDER_COLOR + """;
                padding: 4px;
            }
            QTextEdit {
                background-color: #1E1E1E;
                color: """ + ColorPalette.TEXT_PRIMARY + """;
                border: 1px solid """ + ColorPalette.BORDER_COLOR + """;
                selection-background-color: """ + ColorPalette.SELECTION_BACKGROUND + """;
            }
            QTreeWidget {
                selection-background-color: """ + ColorPalette.SELECTION_BACKGROUND + """;
            }
            QTreeWidget::item:selected {
                background-color: """ + ColorPalette.SELECTION_BACKGROUND + """;
                color: #000000;
            }
            QTreeWidget::item:hover {
                background-color: """ + ColorPalette.BACKGROUND_HIGHLIGHT + """;
            }
            QHeaderView::section {
                background-color: """ + ColorPalette.BACKGROUND_MEDIUM + """;
                color: """ + ColorPalette.TEXT_PRIMARY + """;
                padding: 4px;
                border: 1px solid """ + ColorPalette.BORDER_COLOR + """;
                font-weight: bold;
            }
            QScrollBar:vertical {
                border: none;
                background: """ + ColorPalette.SCROLLBAR_BACKGROUND + """;
                width: 12px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: """ + ColorPalette.SCROLLBAR_HANDLE + """;
                min-height: 20px;
                border-radius: 6px;
                margin: 2px;
            }
            QScrollBar::handle:vertical:hover {
                background: """ + ColorPalette.SCROLLBAR_HANDLE_HOVER + """;
            }
            QScrollBar::handle:vertical:pressed {
                background: """ + ColorPalette.SCROLLBAR_HANDLE_PRESSED + """;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
            QScrollBar:horizontal {
                border: none;
                background: """ + ColorPalette.SCROLLBAR_BACKGROUND + """;
                height: 12px;
                margin: 0px;
            }
            QScrollBar::handle:horizontal {
                background: """ + ColorPalette.SCROLLBAR_HANDLE + """;
                min-width: 20px;
                border-radius: 6px;
                margin: 2px;
            }
            QScrollBar::handle:horizontal:hover {
                background: """ + ColorPalette.SCROLLBAR_HANDLE_HOVER + """;
            }
            QScrollBar::handle:horizontal:pressed {
                background: """ + ColorPalette.SCROLLBAR_HANDLE_PRESSED + """;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                border: none;
                background: none;
                width: 0px;
            }
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                background: none;
            }
            QFrame {
                border: 1px solid """ + ColorPalette.BORDER_COLOR + """;
            }
            QTabWidget::pane {
                border: 1px solid """ + ColorPalette.BORDER_COLOR + """;
            }
            QTabBar::tab {
                background-color: """ + ColorPalette.BACKGROUND_MEDIUM + """;
                color: """ + ColorPalette.TEXT_PRIMARY + """;
                padding: 8px 16px;
                border: 1px solid """ + ColorPalette.BORDER_COLOR + """;
                border-bottom: none;
            }
            QTabBar::tab:selected {
                background-color: """ + ColorPalette.BACKGROUND_DARK + """;
                border-bottom: 2px solid """ + ColorPalette.BACKGROUND_HIGHLIGHT + """;
            }
            QTabBar::tab:hover:!selected {
                background-color: """ + ColorPalette.BUTTON_BACKGROUND_HOVER + """;
            }
            QToolBar {
                background-color: """ + ColorPalette.BACKGROUND_DARK + """;
                border: none;
                spacing: 10px;
            }
        """
    
    @staticmethod
    def get_telnet_tab_stylesheet() -> str:
        """Get the Telnet tab specific stylesheet."""
        return """
            QWidget {
                background-color: """ + ColorPalette.BACKGROUND_DARK + """;
                color: """ + ColorPalette.TEXT_PRIMARY + """;
                font-family: Segoe UI;
            }
            QPushButton {
                background-color: """ + ColorPalette.BUTTON_BACKGROUND + """;
                border: 1px solid """ + ColorPalette.BUTTON_BORDER + """;
                padding: 5px 15px;
                min-width: 80px;
                color: """ + ColorPalette.BUTTON_TEXT + """;
            }
            QPushButton:hover {
                background-color: """ + ColorPalette.BUTTON_BACKGROUND_HOVER + """;
            }
            QPushButton:pressed {
                background-color: """ + ColorPalette.BUTTON_BACKGROUND_PRESSED + """;
            }
            QLineEdit, QComboBox {
                background-color: """ + ColorPalette.INPUT_BACKGROUND + """;
                color: """ + ColorPalette.TEXT_PRIMARY + """;
                border: 1px solid """ + ColorPalette.BORDER_COLOR + """;
                padding: 4px;
            }
            QTextEdit {
                background-color: #1E1E1E;
                color: """ + ColorPalette.TEXT_PRIMARY + """;
                border: 1px solid """ + ColorPalette.BORDER_COLOR + """;
                selection-background-color: """ + ColorPalette.SELECTION_BACKGROUND + """;
            }
            QScrollBar:vertical {
                border: none;
                background: """ + ColorPalette.SCROLLBAR_BACKGROUND + """;
                width: 12px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: """ + ColorPalette.SCROLLBAR_HANDLE + """;
                min-height: 20px;
                border-radius: 6px;
                margin: 2px;
            }
            QScrollBar::handle:vertical:hover {
                background: """ + ColorPalette.SCROLLBAR_HANDLE_HOVER + """;
            }
            QScrollBar::handle:vertical:pressed {
                background: """ + ColorPalette.SCROLLBAR_HANDLE_PRESSED + """;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
            QScrollBar:horizontal {
                border: none;
                background: """ + ColorPalette.SCROLLBAR_BACKGROUND + """;
                height: 12px;
                margin: 0px;
            }
            QScrollBar::handle:horizontal {
                background: """ + ColorPalette.SCROLLBAR_HANDLE + """;
                min-width: 20px;
                border-radius: 6px;
                margin: 2px;
            }
            QScrollBar::handle:horizontal:hover {
                background: """ + ColorPalette.SCROLLBAR_HANDLE_HOVER + """;
            }
            QScrollBar::handle:horizontal:pressed {
                background: """ + ColorPalette.SCROLLBAR_HANDLE_PRESSED + """;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                border: none;
                background: none;
                width: 0px;
            }
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                background: none;
            }
        """


# Export instances for easy access
COLORS = ColorPalette()
STYLESHEETS = StyleSheetManager()