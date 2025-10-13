"""
BsTool Path Resolver Utility

Centralized utility for detecting BsTool.exe path across different execution environments.
Handles both PyInstaller bundled mode and development mode.
"""

import os
import sys
import logging

logger = logging.getLogger(__name__)


def get_bstool_path() -> str:
    """
    Get the path to bstool.exe, handling both development and bundled environments.
    
    Uses hybrid approach for maximum compatibility:
    1. PyInstaller frozen: Check sys._MEIPASS (temp extraction) then sys.executable directory
    2. Development: Project root directory (3 levels up from this file)
    
    Returns:
        str: Absolute path to bstool.exe, or empty string if not found
        
    Examples:
        >>> # In bundled mode (onefile with temp extraction)
        >>> path = get_bstool_path()
        >>> # Returns: C:\\Users\\User\\AppData\\Local\\Temp\\_MEI123456\\BsTool.exe
        
        >>> # In bundled mode (onedir)
        >>> path = get_bstool_path()
        >>> # Returns: C:\\Program Files\\LOGReporter\\BsTool.exe
        
        >>> # In development mode
        >>> path = get_bstool_path()
        >>> # Returns: D:\\_APP\\LOGReport\\BsTool.exe
    """
    # Check if running in a bundled environment (PyInstaller)
    if getattr(sys, 'frozen', False):
        # Try sys._MEIPASS first (for onefile mode with temp extraction)
        if hasattr(sys, '_MEIPASS'):
            bstool_path = os.path.join(sys._MEIPASS, "BsTool.exe")
            if os.path.exists(bstool_path):
                logger.debug(f"Found bstool.exe in _MEIPASS: {bstool_path}")
                return bstool_path
        
        # Fallback to executable directory (for onedir mode)
        bstool_path = os.path.join(os.path.dirname(sys.executable), "BsTool.exe")
        logger.debug(f"Looking for bstool.exe in executable directory: {bstool_path}")
    else:
        # In development, bstool.exe should be in the project root
        # This file is at: src/commander/utils/bstool_path_resolver.py
        # Project root is 3 levels up
        bstool_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
            "BsTool.exe"
        )
        logger.debug(f"Looking for bstool.exe in project root: {bstool_path}")
    
    # Verify the path exists before returning
    if os.path.exists(bstool_path):
        logger.info(f"BsTool.exe found at: {bstool_path}")
        return bstool_path
    else:
        logger.warning(f"BsTool.exe not found at: {bstool_path}")
        return ""


def validate_bstool_path(path: str) -> bool:
    """
    Validate that the given path points to an existing BsTool.exe file.
    
    Args:
        path: Path to validate
        
    Returns:
        bool: True if path exists and points to BsTool.exe, False otherwise
        
    Examples:
        >>> validate_bstool_path("C:\\Tools\\BsTool.exe")
        True
        >>> validate_bstool_path("C:\\Invalid\\Path.exe")
        False
    """
    if not path:
        return False
    
    if not os.path.exists(path):
        logger.warning(f"Path does not exist: {path}")
        return False
    
    if not os.path.isfile(path):
        logger.warning(f"Path is not a file: {path}")
        return False
    
    if not path.lower().endswith("bstool.exe"):
        logger.warning(f"Path does not point to BsTool.exe: {path}")
        return False
    
    logger.debug(f"Path validated: {path}")
    return True
