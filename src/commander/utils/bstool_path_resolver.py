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
    r"""
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
    
    logger.info(f"🔍 get_bstool_path() called")
    logger.info(f"📍 sys.executable: {sys.executable}")
    
    # CRITICAL: Detect if we're running from a bundled executable
    # Check multiple indicators since Nuitka/PyInstaller behave differently
    
    # Get the directory containing sys.executable
    exe_dir = os.path.dirname(sys.executable)
    temp_dir = tempfile.gettempdir()
    
    logger.info(f"📂 exe_dir: {exe_dir}")
    logger.info(f"📂 temp_dir: {temp_dir}")
    
    # Indicator 1: sys._MEIPASS exists (PyInstaller, some Nuitka configs)
    has_meipass = hasattr(sys, '_MEIPASS')
    
    # Indicator 2: sys.frozen is True (PyInstaller, some Nuitka configs)
    is_frozen = getattr(sys, 'frozen', False)
    
    # Indicator 3: sys.__compiled__ exists (Nuitka-specific)
    is_compiled = hasattr(sys, '__compiled__')
    
    # Indicator 4: sys.executable is inside temp directory (Nuitka onefile)
    # Normalize paths for comparison (case-insensitive on Windows)
    exe_dir_normalized = os.path.normpath(exe_dir).lower()
    temp_dir_normalized = os.path.normpath(temp_dir).lower()
    in_temp = exe_dir_normalized.startswith(temp_dir_normalized)
    
    # Indicator 5: Check for LOGReporter subdirectory in temp (Nuitka onefile-tempdir-spec)
    # Nuitka extracts to {TEMP}\LOGReporter\ by default with our build config
    # CRITICAL: Windows may use 8.3 short paths like LOGREP~1, expand them
    try:
        import ctypes
        # Get long path name (converts LOGREP~1 -> LOGReporter)
        buffer = ctypes.create_unicode_buffer(512)
        ctypes.windll.kernel32.GetLongPathNameW(exe_dir, buffer, 512)
        exe_dir_long = buffer.value.lower() if buffer.value else exe_dir_normalized
    except:
        exe_dir_long = exe_dir_normalized
    
    in_logreporter_temp = 'logreporter' in exe_dir_long
    
    # Indicator 6: sys.executable filename is not python.exe (bundled)
    exe_name = os.path.basename(sys.executable).lower()
    is_python_exe = exe_name in ('python.exe', 'pythonw.exe', 'python')
    
    logger.debug(f"Detection indicators:")
    logger.debug(f"  sys._MEIPASS exists: {has_meipass}")
    logger.debug(f"  sys.frozen: {is_frozen}")
    logger.debug(f"  sys.__compiled__ exists (Nuitka): {is_compiled}")
    logger.debug(f"  sys.executable in temp: {in_temp} (exe_dir={exe_dir}, temp={temp_dir})")
    logger.debug(f"  exe_dir_long (expanded): {exe_dir_long}")
    logger.debug(f"  LOGReporter in path: {in_logreporter_temp}")
    logger.debug(f"  sys.executable name: {exe_name} (is python: {is_python_exe})")
    
    # Determine if we're in a bundled environment
    # CRITICAL: If we're in a temp/LOGReporter folder, it's ALWAYS bundled (Nuitka onefile)
    # Even if Nuitka names the exe python.exe, the temp/LOGReporter location is definitive
    is_bundled = (has_meipass or is_frozen or is_compiled or 
                  (in_temp and not is_python_exe) or 
                  in_logreporter_temp)  # If in LOGReporter temp, always bundled
    
    logger.info(f"🔍 DETECTION SUMMARY: bundled={is_bundled} | meipass={has_meipass} | frozen={is_frozen} | compiled={is_compiled} | temp={in_temp} | logreporter_temp={in_logreporter_temp}")
    
    if is_bundled:
        logger.info(f"✅ Bundled mode detected - searching for BsTool.exe...")
        
        # List of candidate paths to check (in priority order)
        candidate_paths = []
        
        # 1. Try sys._MEIPASS first if it exists (PyInstaller)
        if has_meipass:
            logger.debug(f"sys._MEIPASS exists: {sys._MEIPASS}")
            candidate_paths.append(os.path.join(sys._MEIPASS, "BsTool.exe"))
            candidate_paths.append(os.path.join(sys._MEIPASS, "LOGReporter", "BsTool.exe"))
        
        # 2. Try executable directory (Nuitka onefile standard location)
        candidate_paths.append(os.path.join(exe_dir, "BsTool.exe"))
        
        # 3. Try one level up from executable (some Nuitka configs)
        parent_dir = os.path.dirname(exe_dir)
        candidate_paths.append(os.path.join(parent_dir, "BsTool.exe"))
        
        # 4. Try common Nuitka extraction subdirectories
        candidate_paths.append(os.path.join(exe_dir, "bin", "BsTool.exe"))
        candidate_paths.append(os.path.join(exe_dir, "_internal", "BsTool.exe"))
        
        # 5. If we're in a LOGReporter temp folder, try direct path
        if in_logreporter_temp:
            # Extract the LOGReporter folder path (use long path to avoid LOGREP~1)
            parts = exe_dir_long.split(os.sep)
            try:
                idx = [p.lower() for p in parts].index('logreporter')
                logreporter_root = os.sep.join(parts[:idx+1])
                candidate_paths.append(os.path.join(logreporter_root, "BsTool.exe"))
                logger.debug(f"Added LOGReporter root path: {logreporter_root}")
            except ValueError:
                pass  # logreporter not in path somehow
        
        logger.info(f"📋 Checking {len(candidate_paths)} candidate paths...")
        # Try all candidate paths
        for i, bstool_path in enumerate(candidate_paths, 1):
            logger.debug(f"  [{i}/{len(candidate_paths)}] Checking: {bstool_path}")
            if os.path.exists(bstool_path):
                logger.info(f"✅ FOUND BsTool.exe at: {bstool_path}")
                return bstool_path
        
        # Log directory contents for diagnostics
        logger.warning(f"❌ BsTool.exe NOT FOUND in any candidate location")
        try:
            logger.debug(f"📂 Contents of executable directory ({exe_dir}):")
            contents = os.listdir(exe_dir)
            exe_files = [f for f in contents if f.lower().endswith('.exe')]
            dirs = [d for d in contents if os.path.isdir(os.path.join(exe_dir, d))]
            logger.debug(f"  Directories: {dirs}")
            logger.debug(f"  Executables: {exe_files}")
            
            # Also check parent directory
            if os.path.exists(parent_dir):
                logger.debug(f"Contents of parent directory ({parent_dir}):")
                parent_contents = os.listdir(parent_dir)
                parent_exe_files = [f for f in parent_contents if f.lower().endswith('.exe')]
                parent_dirs = [d for d in parent_contents if os.path.isdir(os.path.join(parent_dir, d))]
                logger.debug(f"  Directories: {parent_dirs}")
                logger.debug(f"  Executables: {parent_exe_files}")
        except Exception as e:
            logger.error(f"  Error listing directories: {e}")
        
        logger.warning(f"Checked {len(candidate_paths)} candidate paths, none found")
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
