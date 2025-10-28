# Python 3.13 Telnetlib Compatibility Fix

## Issue
Python 3.13 removed the built-in `telnetlib` module, causing `ModuleNotFoundError` when starting LOGReporter.

## Solution
Installed the standalone `telnetlib` package which provides the same API as the built-in module.

## Changes Made

### 1. Updated `requirements.txt`
Added conditional dependency:
```
telnetlib; python_version >= '3.13'
```

### 2. Created `src/commander/telnet_compat.py`
Compatibility layer that:
- Uses built-in `telnetlib` on Python ≤ 3.12
- Falls back to external `telnetlib` package on Python ≥ 3.13
- Provides helpful error messages if neither is available

### 3. Updated `src/commander/session_manager.py`
Added try/except to gracefully handle the import:
```python
try:
    import telnetlib
except ModuleNotFoundError:
    from .telnet_compat import telnetlib
```

### 4. Updated `build_nuitka.bat`
Added `--include-package=telnetlib` to ensure the external package is bundled.

## Installation

For Python 3.13+:
```powershell
pip install telnetlib
```

Or install all dependencies:
```powershell
pip install -r requirements.txt
```

## Build Impact

The Nuitka build script now includes:
- `--include-package=telnetlib` to bundle the external package
- Compatible with both Python 3.12 and 3.13+

## Testing

Run the application to verify:
```powershell
python .\src\main.py
```

The GUI should open without `ModuleNotFoundError`.

## Future Considerations

The `telnetlib` package is a direct port of the removed stdlib module. Alternatives:
- **telnetlib3**: Modern async/await-based library (requires code refactoring)
- **Paramiko**: SSH library with telnet-like capabilities
- **Keep current solution**: Works well, minimal changes required

Current solution is recommended for stability and compatibility.
