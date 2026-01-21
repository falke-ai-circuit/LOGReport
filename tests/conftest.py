"""
Pytest configuration for unit tests.

This conftest.py file ensures the src directory is properly added to the Python path
for test discovery and imports.
"""

import sys
import os
from pathlib import Path

# Add src directory to Python path for proper imports
src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))
