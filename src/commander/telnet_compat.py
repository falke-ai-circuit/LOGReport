"""
Telnet compatibility layer for Python 3.13+
telnetlib was removed in Python 3.13, this module provides compatibility
"""
import sys

try:
    # Python 3.12 and earlier - use built-in telnetlib
    import telnetlib
except ModuleNotFoundError:
    # Python 3.13+ - use vendored telnetlib from this package
    from . import telnetlib

# Export for use in other modules
__all__ = ['telnetlib']
