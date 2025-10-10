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

def get_file_icon_green():
    """Creates green rectangle icon for successfully executed files"""
    color = QColor("green")
    return create_token_icon(color)

def get_file_icon_yellow():
    """Creates yellow rectangle icon for partially executed files"""
    color = QColor("yellow")
    return create_token_icon(color)

def get_file_icon_red():
    """Creates red rectangle icon for failed/unexecuted files"""
    color = QColor("red")
    return create_token_icon(color)

def get_section_icon_green():
    """Creates green rectangle icon for sections with all files executed"""
    color = QColor("green")
    return create_token_icon(color)

def get_section_icon_yellow():
    """Creates yellow rectangle icon for sections with mixed execution"""
    color = QColor("yellow")
    return create_token_icon(color)

def get_section_icon_red():
    """Creates red rectangle icon for sections with failed/unexecuted files"""
    color = QColor("red")
    return create_token_icon(color)

def get_node_icon_green():
    """Creates green circle icon for nodes with all sections executed"""
    color = QColor("green")
    return create_node_icon(color)

def get_node_icon_yellow():
    """Creates yellow circle icon for nodes with mixed execution"""
    color = QColor("yellow")
    return create_node_icon(color)

def get_node_icon_red():
    """Creates red circle icon for nodes with failed/unexecuted sections"""
    color = QColor("red")
    return create_node_icon(color)