---
metadata:
  created_date: "2025-10-01_080200"
  last_modified: "2025-10-01T08:02:00Z"
  last_accessed: "2025-10-01T08:02:00Z"
  word_count: 260
  reference_count: 6
  document_hash: "sha256:tech_pyqt_migration_hash"
  similarity_index: 0.12
  obsolete_check_date: "2025-10-01"
---

# ⚙️ TECH PyQt Migration v1

> **Purpose:** Guide PyQt5 → PyQt6 migration for LOGReport commander components.

## 📋 Overview
**What:** Update Qt bindings, signals, imports | **Audience:** Developers | **Solves:** Compatibility with PyQt6 (v6.5+), deprecate PyQt5 remnants.

## 🎯 Scope & Requirements
| Type | Requirement | Target | Constraint |
|------|-------------|--------|------------|
| Functional | Update signals/imports | All commander .py files | No API breaks, test coverage 90% |
| Performance | Binding efficiency | <5% overhead | Qt6 optimized threading |
| Security | Secure imports | No deprecated funcs | Validate post-migration tests |

## 🔧 Architecture & Stack
```
PyQt5 (legacy) → PyQt6 (current)
├── Imports: from PyQt5 → PyQt6
├── Signals: pyqtSignal → pyqtSignal (unchanged)
└── Components: CommanderWindow, LogWriter, CommandQueue
```
| Component | Role | Change | Version | Purpose |
|-----------|------|--------|---------|---------|
| PyQt6.QtCore | Signals/Threads | pyqtSignal, QRunnable | 6.5+ | Cross-platform signals |
| PyQt6.QtWidgets | UI Factory | QMainWindow, QTreeView | 6.5+ | Modern widget rendering |
| commander.ui | Window/UI | Update imports [src/commander/ui/commander_window.py:41](src/commander/ui/commander_window.py:41) | - | Backward compat |

**Patterns:** Direct replace → Minimal disruption | Test-driven → Verify signals.

## 🌐 API & Interfaces
```python
# Before (PyQt5)
from PyQt5.QtCore import pyqtSignal, QObject

# After (PyQt6)
from PyQt6.QtCore import pyqtSignal, QObject  # No change in usage
signal = pyqtSignal(str, bool, int, int)  # e.g., log_write_completed
```

**Data Models:** Unchanged (dataclasses for QueuedCommand).

**Errors:** ImportError → Version mismatch • SignalMismatch → Qt version.

## ⚙️ Configuration & Security
| Variable | Purpose | Default | Required | Example |
|----------|---------|---------|----------|---------|
| QT_VERSION | Binding check | 6 | ✅ | PyQt6==6.5.0 |
| SIGNAL_COMPAT | Legacy mode | False | ❌ | False (full migration) |

**Security:** Sanitize Qt inputs • No eval in signals.

## ⚡ Performance & Testing
**Targets:** Signal emit <1ms • UI render 60fps • Memory same as PyQt5.
**Optimization:** Qt6 native threading [src/commander/command_queue.py:166](src/commander/command_queue.py:166).

**Testing:** Unit (signals [tests/commander/test_log_writer.py:21](tests/commander/test_log_writer.py:21)) • Integration (UI factory) • E2E (queue processing).

## 🚀 Deployment & Operations
```bash
# Install PyQt6
pip install PyQt6==6.5.0
# Update requirements.txt
# Run tests
pytest tests/commander/
```

**Environments:** Dev (virtualenv PyQt6) • Prod (docker with Qt6).

## 📊 Monitoring & Maintenance
**Logging:** Import warnings → app.log [src/commander/log_writer.py:39](src/commander/log_writer.py:39).
**Metrics:** Signal emissions count • Qt version check.
**Alerts:** PyQt5 remnants → Deprecation warning.

## 🛠️ Troubleshooting
| Issue | Symptoms | Solution | Tools |
|-------|----------|----------|-------|
| Import fail | ModuleNotFoundError | pip install PyQt6 | requirements.txt diff |
| Signal error | Type mismatch | Update pyqtSignal args [src/commander/log_writer.py:20](src/commander/log_writer.py:20) | pytest signals |

**Debug:** Logs → application.log • Qt debug → QT_DEBUG_PLUGINS=1.

---
**📚 Refs:** ROADMAP_recent_changes_v1.md, ARCH_cmd_queue_impl_v1.md, BLUEPRINT_bstool_integration_v1.md (PyQt refs).