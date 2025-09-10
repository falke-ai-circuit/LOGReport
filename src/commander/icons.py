"""
Icon Generator
Creates placeholder icons for Commander UI
"""
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QSize
from .ui.theme import COLORS

def create_node_icon(color: QColor) -> QIcon:
    """Creates a circular icon for nodes"""
    # Ensure we have an application instance
    if not QApplication.instance():
        QApplication([])  # Create minimal application if none exists

    pixmap = QPixmap(16, 16)
    pixmap.fill(Qt.GlobalColor.transparent)
    
    painter = QPainter(pixmap)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(color)
    painter.drawEllipse(0, 0, 15, 15)
    painter.end()
    
    return QIcon(pixmap)

def create_token_icon(color: QColor) -> QIcon:
    """Creates a square icon for tokens"""
    # Ensure we have an application instance
    if not QApplication.instance():
        QApplication([])  # Create minimal application if none exists

    pixmap = QPixmap(12, 12)
    pixmap.fill(Qt.GlobalColor.transparent)
    
    painter = QPainter(pixmap)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(color)
    painter.drawRect(0, 0, 11, 11)
    painter.end()
    
    return QIcon(pixmap)

# Create icon instances as functions to defer creation
def get_node_online_icon():
    # Use the centralized color palette
    from .ui.theme import COLORS
    color = QColor()
    color.setNamedColor(COLORS.ICON_NODE_ONLINE)
    return create_node_icon(color)

def get_node_offline_icon():
    # Use the centralized color palette
    from .ui.theme import COLORS
    color = QColor()
    color.setNamedColor(COLORS.ICON_NODE_OFFLINE)
    return create_node_icon(color)

def get_token_icon():
    # Use the centralized color palette
    from .ui.theme import COLORS
    color = QColor()
    color.setNamedColor(COLORS.ICON_TOKEN)
    return create_token_icon(color)