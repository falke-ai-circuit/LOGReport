---
metadata:
  created_date: "2025-10-02_184500"
  last_modified: "2025-10-02T18:45:00Z"
  last_accessed: "2025-10-02T18:45:00Z"
  word_count: 450
  reference_count: 8
  document_hash: "sha256:tech_session_manager_v1_hash"
  similarity_index: 0.08
  obsolete_check_date: "2025-10-02"
---

# ⚙️ TECH Session Manager v1

> **Purpose:** Centralized management of Telnet, VNC, FTP, and debugger sessions for LOGReport Commander, handling creation, connection, and lifecycle.

## 📋 Overview
**What:** Session abstraction layer | **Audience:** Developers | **Solves:** Unified session handling across protocols, caching, and error recovery.

## 🎯 Scope & Requirements
| Type | Requirement | Target | Constraint |
|------|-------------|--------|------------|
| Functional | Create/connect/disconnect sessions | All session types (TELNET/VNC/FTP/DEBUGGER) | Auto-connect optional, cache by (host,port,type) |
| Performance | Connection <5s, retry max 3 | 95% success rate | Timeout 15s default |
| Security | Auth handling (username/password) | Secure storage | No plain-text persistence |

## 🔧 Architecture & Stack
```
SessionManager (QObject)
├── BaseSession (QObject): connect/disconnect/send_command
│   ├── TelnetSession: telnetlib, prompt detection (regex patterns)
│   ├── VNCSession: vncdotool, recording (SessionRecorder)
│   └── FTPSession: Placeholder (Phase 2)
└── SessionConfig (dataclass): host/port/type/auth/timeout
```
| Component | Role | Technology | Version | Purpose |
|-----------|------|------------|---------|---------|
| SessionManager | Orchestration | PyQt6.QtCore (QObject, pyqtSignal) | 6.5+ | Cache active_sessions dict, create_session |
| TelnetSession | Protocol impl | telnetlib, socket | Python 3.12 | Buffered read, prompt regex (\n\d+[a-z]%\s*$) |
| VNCSession | VNC handling | vncdotool.api | Latest | Retry logic (max 3), recording integration |
| SessionConfig | Config model | dataclasses | Stdlib | Type-safe params (SessionType Enum) |

**Patterns:** Factory (create_session by type) → Rationale: Extensible | Observer (connection_state_changed signal) → UI updates | Caching (session_cache) → Reuse connected sessions.

## 🌐 API & Interfaces
```python
# Create session
config = SessionConfig(host="192.168.0.11", port=23, session_type=SessionType.TELNET)
session = manager.create_session(config, auto_connect=True)

# Send command
response = session.send_command("show version")

# Disconnect
session.disconnect()

# Get active
active = manager.get_active_sessions()
```
**Data Models:**
```json
{
  "config": {
    "host": "string",
    "port": "int",
    "session_type": "TELNET|VNC|FTP|DEBUGGER",
    "username": "string (opt)",
    "password": "string (opt)",
    "timeout": "int (default 15)"
  },
  "state": {
    "is_connected": "bool",
    "connection": "object (protocol-specific)"
  }
}
```

**Errors:** ConnectionError→Timeout/refused • ValueError→Invalid type • EOFError→Remote close.

## ⚙️ Configuration & Security
| Variable | Purpose | Default | Required | Example |
|----------|---------|---------|----------|---------|
| SESSION_TIMEOUT | Connection timeout | 15 | ❌ | 30 |
| MAX_RETRIES | VNC retry count | 3 | ❌ | 5 |
| VNC_PASSWORD | Auth for VNC | "" | ✅ for auth | "secret" |

**Security:** Password→Not logged • Sessions→Isolated per node • Validation→Token validate (3-digit ID).

## ⚡ Performance & Testing
**Targets:** Connect <5s • Command response <10s • Memory <50MB/session  
**Optimization:** Cache reuse • Non-blocking read (0.05s timeout) • Prompt detection early exit.

**Testing:** Unit (connect/disconnect [tests/commander/test_session_manager.py]) • Integration (telnet send [tests/commander/test_telnet_connect.py]) • E2E (VNC recording).  
**Critical Tests:** ✅ Cache hit (reuse session) ✅ Retry on fail ✅ Signal emit on state change.

## 🚀 Deployment & Operations
```bash
# Install deps
pip install telnetlib3 vncdotool  # telnetlib std, vncdotool for VNC

# Run with sessions
python src/main.py --telnet-host 192.168.0.11 --port 23

# Test session
pytest tests/commander/test_session_manager.py
```
**Environments:** Dev (local telnet mock) • Prod (remote VNC/Telnet).  
**Process:** Init in CommanderWindow • Cleanup on app close.

## 📊 Monitoring & Maintenance
**Logging:** DEBUG connect attempts → application.log [src/commander/log_writer.py:39]  
**Metrics:** Sessions active • Connect success rate • Retry count.  
**Alerts:** Connection fail >3 → Notify • Cache miss >50% → Warn.

## 🛠️ Troubleshooting
| Issue | Symptoms | Solution | Tools |
|-------|----------|----------|-------|
| Connect timeout | "socket.timeout" | Increase timeout, check network | telnet 192.168.0.11 23 |
| Prompt not detected | Partial response | Add regex pattern, log raw bytes | logging.debug(response.hex()) |
| VNC retry fail | "Max retries" | Verify VNC server, password | vncdotool connect vnc://host:port |

**Debug:** Logs→application.log • Socket→get_socket().recv(1) • Health→is_connected.

---
**📚 Refs:** src/commander/session_manager.py, tests/commander/test_session_manager.py, ROADMAP_commander_module_v1.md.