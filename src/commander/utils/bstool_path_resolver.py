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
    1. Nuitka/PyInstaller frozen: Check sys._MEIPASS (temp extraction) then sys.executable directory
    2. Development: Project root directory (3 levels up from this file)
    
    Nuitka onefile mode extracts to {TEMP}\LOGReporter\ with BsTool.exe at root level.
    
    NOTE: Nuitka doesn't set sys.frozen=True or sys._MEIPASS in all cases.
    We detect Nuitka bundles by checking if sys.executable is in a temp directory.
    
    Returns:
        str: Absolute path to bstool.exe, or empty string if not found
        
    Examples:
        >>> # In Nuitka bundled mode (onefile with temp extraction to {TEMP}\LOGReporter)
        >>> path = get_bstool_path()
        >>> # Returns: C:\\Users\\User\\AppData\\Local\\Temp\\LOGReporter\\BsTool.exe
        
        >>> # In PyInstaller bundled mode (onefile with temp extraction)
        >>> path = get_bstool_path()
        >>> # Returns: C:\\Users\\User\\AppData\\Local\\Temp\\_MEI123456\\BsTool.exe
        
        >>> # In bundled mode (onedir)
        >>> path = get_bstool_path()
        >>> # Returns: C:\\Program Files\\LOGReporter\\BsTool.exe
        
        >>> # In development mode
        >>> path = get_bstool_path()
        >>> # Returns: D:\\_APP\\LOGReport\\BsTool.exe
    """
    import tempfile
    
    # CRITICAL: Detect if we're running from a bundled executable
    # Check multiple indicators since Nuitka/PyInstaller behave differently
    
    # Get the directory containing sys.executable
    exe_dir = os.path.dirname(sys.executable)
    temp_dir = tempfile.gettempdir()
    
    # Indicator 1: sys._MEIPASS exists (PyInstaller, some Nuitka configs)
    has_meipass = hasattr(sys, '_MEIPASS')
    
    # Indicator 2: sys.frozen is True (PyInstaller, some Nuitka configs)
    is_frozen = getattr(sys, 'frozen', False)
    
    # Indicator 3: sys.executable is inside temp directory (Nuitka onefile)
    # Normalize paths for comparison
    exe_dir_normalized = os.path.normpath(exe_dir).lower()
    temp_dir_normalized = os.path.normpath(temp_dir).lower()
    in_temp = exe_dir_normalized.startswith(temp_dir_normalized)
    
    # Indicator 4: sys.executable filename is not python.exe (bundled)
    exe_name = os.path.basename(sys.executable).lower()
    is_python_exe = exe_name in ('python.exe', 'pythonw.exe', 'python')
    
    logger.debug(f"Detection indicators:")
    logger.debug(f"  sys._MEIPASS exists: {has_meipass}")
    logger.debug(f"  sys.frozen: {is_frozen}")
    logger.debug(f"  sys.executable in temp: {in_temp} (exe_dir={exe_dir}, temp={temp_dir})")
    logger.debug(f"  sys.executable name: {exe_name} (is python: {is_python_exe})")
    
    # Determine if we're in a bundled environment
    is_bundled = has_meipass or is_frozen or (in_temp and not is_python_exe)
    
    if is_bundled:
        logger.debug(f"Detected bundled environment")
        
        # Try sys._MEIPASS first if it exists
        if has_meipass:
            logger.debug(f"sys._MEIPASS exists: {sys._MEIPASS}")
            
            # Try direct path in _MEIPASS first
            bstool_path = os.path.join(sys._MEIPASS, "BsTool.exe")
            logger.debug(f"Checking for bstool.exe in _MEIPASS: {bstool_path}")
            if os.path.exists(bstool_path):
                logger.info(f"Found bstool.exe in _MEIPASS: {bstool_path}")
                return bstool_path
            
            # Check if _MEIPASS\LOGReporter\BsTool.exe exists
            bstool_path_subfolder = os.path.join(sys._MEIPASS, "LOGReporter", "BsTool.exe")
            logger.debug(f"Checking for bstool.exe in _MEIPASS\\LOGReporter: {bstool_path_subfolder}")
            if os.path.exists(bstool_path_subfolder):
                logger.info(f"Found bstool.exe in _MEIPASS\\LOGReporter subfolder: {bstool_path_subfolder}")
                return bstool_path_subfolder
        
        # For Nuitka onefile: executable is in temp, BsTool.exe is in same directory
        bstool_path = os.path.join(exe_dir, "BsTool.exe")
        logger.debug(f"Checking for bstool.exe in executable directory: {bstool_path}")
        if os.path.exists(bstool_path):
            logger.info(f"Found bstool.exe in executable directory: {bstool_path}")
            return bstool_path
        
        # Log directory contents for diagnostics
        logger.warning(f"BsTool.exe not found in bundled environment")
        try:
            logger.debug(f"Contents of executable directory ({exe_dir}):")
            contents = os.listdir(exe_dir)
            exe_files = [f for f in contents if f.lower().endswith('.exe')]
            dirs = [d for d in contents if os.path.isdir(os.path.join(exe_dir, d))]
            logger.debug(f"  Directories: {dirs}")
            logger.debug(f"  Executables: {exe_files}")
        except Exception as e:
            logger.error(f"  Error listing executable directory: {e}")
        
        logger.warning(f"BsTool.exe not found at: {bstool_path}")
        return ""
    
    else:
        # In development, bstool.exe should be in the project root
        # This file is at: src/commander/utils/bstool_path_resolver.py
        # Project root is 3 levels up
        bstool_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
            "BsTool.exe"
        )
        logger.debug(f"Development mode - looking for bstool.exe in project root: {bstool_path}")
    
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
