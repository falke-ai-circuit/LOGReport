# ⚙️ BsTool Auto-Detection and Path Resolution

> **Purpose:** *Automatic resolution of bstool.exe in bundled EXE environments, handling subdir placement, caching for performance, and DLL reset for reliability.*

## 📋 Overview
**What:** Path resolution service for external tool integration | **Audience:** Developers, deployers | **Solves:** Manual path config in frozen apps, DLL loading failures post-bundling

## 🎯 Scope & Requirements
| Type | Requirement | Target | Constraint |
|------|-------------|--------|------------|
| Functional | Detect frozen env, resolve relative subdir path, cache result, reset DLL on failure | 100% auto-detection in PyInstaller bundles | Windows-only; assumes _internal/ subdir |
| Performance | Cache path lookups | <10ms resolution; cache TTL 1h | No network deps; local file ops only |
| Security | Validate exe integrity via hash | SHA-256 match on load | No user input; read-only paths |

## 🔧 Architecture & Stack
```
[Text Diagram: Path Resolution Flow]
User Action → _get_bstool_path() Service
├── Check sys._MEIPASS (frozen?) → Yes: base = _MEIPASS + '/_internal/bstool.exe'
│   ├── Cache hit? → Return cached path
│   └── Cache miss: Resolve relative path → Validate exe exists → Cache & return
├── No: base = __file__ dir + '/bstool.exe' (dev mode)
└── DLL Reset: On load fail → Unload DLLs → Retry path → Emit error if persistent
```
| Component | Role | Technology | Version | Purpose |
|-----------|------|------------|---------|---------|
| _get_bstool_path | Core resolver | Python sys/os | 3.10+ | Detects bundle mode, constructs path |
| Cache Manager | Stores resolved paths | dict with TTL | Custom | Avoids repeated file ops; expires stale |
| DLL Reset Handler | Reloads on failure | ctypes/win32api | Windows API | Clears loaded DLLs for fresh load |
| BsToolCommandService | Integrates resolution | PyQt6 signals | 6.5+ | Triggers path resolution on exec |

**Patterns:** Singleton Service → *Centralizes path logic for reuse* | Caching with TTL → *O(1) lookups, prevents stale paths*

## 🌐 API & Interfaces
```python
def _get_bstool_path(reset_dll=False) -> str:
    """Resolve bstool.exe path with optional DLL reset."""
    # Returns: Valid path or raises FileNotFoundError
    pass

class BsToolCommandService(QObject):
    path_resolved = pyqtSignal(str)  # Emits on successful resolution
    path_error = pyqtSignal(str)    # Emits on failure (e.g., "DLL load failed")

    def execute_with_resolution(self, args: str):
        path = _get_bstool_path()
        self.path_resolved.emit(path)
        # Proceed with subprocess.Popen(path, args)
```
**Data Models:**
```json
{
  "path_cache": {
    "bstool_exe": "C:/app/_internal/bstool.exe",
    "ttl": "2025-10-03T20:00:00Z",
    "validated": true
  },
  "dll_state": {
    "loaded": ["kernel32.dll"],
    "reset_needed": false
  }
}
```

**Errors:** FileNotFoundError→{Path validation fail: Check bundle} • DLLLoadError→{Reset attempted: Manual reinstall} • CacheExpired→{Re-resolve silently}

## ⚙️ Configuration & Security
| Variable | Purpose | Default | Required | Example |
|----------|---------|---------|----------|---------|
| `BSTOOL_SUBDIR` | Bundle subdir | '_internal' | ❌ | 'tools' |
| `DLL_RESET_TIMEOUT` | Reset wait (ms) | 5000 | ❌ | 10000 |
| `CACHE_TTL_HOURS` | Cache expiry | 1 | ❌ | 24 |

**Security:** Path→{Canonicalize to prevent traversal} • Exe→{Hash verify on load} • Env→{Fixed COMMUNICATION_LINE=AB01, no injection} • Validation→{File exists + executable bit}

## ⚡ Performance & Testing
**Targets:** Resolution {5ms} • Cache hit {1ms} • DLL reset {2s max} • Scale {1000+ calls/session}  
**Optimization:** Cache→{In-memory dict} • Scale→{Lazy load on first exec} • Monitor→{Log resolution time}

**Testing:** Unit {95%} • Integration {Path in bundle} • E2E {Full exec cycle}  
**Critical Tests:** ✅ Frozen path resolution • ✅ Cache persistence • ✅ DLL reset on fail • ✅ Dev mode fallback

## 🚀 Deployment & Operations
```bash
# Build with bundling
build.bat  # Includes bstool.exe in _internal/

# Post-build verify
python -c "import sys; print(sys._MEIPASS)"  # Confirms bundle path
dist/LOGReporter.exe --test-bstool  # Runs resolution test
```
**Environments:** Dev→{Local bstool.exe} • Staging→{Bundle test} • Prod→{Signed exe}  
**Process:** CI/CD→{Auto-bundle on tag} • Rollback→{Versioned bundles} • Scaling→{N/A, single exe}

## 📊 Monitoring & Maintenance
**Logging:** ERROR→{Path fail/DLL error} → INFO→{Resolution success} → DEBUG→{Cache hits} → {JSON format, 7d retention}  
**Metrics:** ResolutionTime→{Histogram ms} • CacheHitRate→{%} • DLLErrorRate→{Per session}  
**Alerts:** PathFail→{>5/session → Notify dev} • ResetFreq→{>1/hour → Bundle issue}

## 🛠️ Troubleshooting
| Issue | Symptoms | Solution | Tools |
|-------|----------|----------|-------|
| Path not found | FileNotFoundError on exec | Verify bundle: Check _internal/bstool.exe | PyInstaller --onefile --debug=all |
| DLL load fail | ImportError post-resolve | Trigger reset: Set reset_dll=True | Dependency Walker (depends.exe) |
| Cache stale | Old path after move | Clear cache: Restart app or set TTL=0 | Python debugger (pdb) |
| Slow resolution | >100ms on first load | Profile ops: Add timing logs | cProfile, time.perf_counter |

**Debug:** Logs→`logs/application.log` • Profile→`python -m cProfile _get_bstool_path()` • Health→{N/A, service signal}

---
**📚 Refs:** *PyInstaller docs (bundling datas), ctypes DLL unload patterns, Python caching best practices*