---
reason: 'duplicate of mockup'
archived_date: '2025-10-02'
original_path: 'docs/blueprints/vnc_tab_blueprint.md'
---

# VNC Tab Architecture Blueprint

## Layout Structure
The VNC tab implements a **QVBoxLayout** as its root container to ensure proper vertical arrangement of components. This follows the established pattern seen in `SessionView` implementation across the application.

### Component Hierarchy
```
VNC Tab (QWidget)
│
├── Top Section (QHBoxLayout)
│   ├── IP Address Input (QLineEdit)
│   │   └── Placeholder: "192.168.x.x:5900"
│   └── Log Filename Indicator (QLabel)
│       └── Dynamic: Shows selected log filename
│
├── Middle Section (QFrame)
│   ├── VNC Viewer Container
│   │   └── Placeholder for actual VNC rendering widget
│   └── Connection Status Overlay (QLabel)
│       └── Visible during connection states
│
└── Bottom Section (QVBoxLayout)
    ├── Connection Controls (QHBoxLayout)
    │   ├── IP Address Input (QLineEdit)
    │   │   └── Auto-populated from log filename
    │   ├── Connect Button (QPushButton)
    │   │   └── Text: "Connect"
    │   └── Status Indicator (QLabel)
    │       └── Dynamic: "Disconnected" / "Connected" / "Connecting..."
    │
    ├── Log Output Area (QTextEdit)
    │   ├── Read-only mode
    │   └── Auto-scroll enabled
    └── Action Controls (QHBoxLayout)
        ├── Copy to Log Button (QPushButton)
        │   └── Text: "Copy to Logfile"
        ├── Session Record Button (QPushButton)
        │   └── Text: "Record Session"
        └── Clear Log Button (QPushButton)
            └── Text: "Clear Log"
```

## Key Implementation Specifications

### 1. Dynamic IP Management
- **IP Extraction Logic**:
  - Parse IP from log filename pattern (e.g., `AP01m-192_168_0_11` → `192.168.0.11`)
  - Implemented via log filename parsing
  - Triggered when log file is selected in node tree
- **IP Input Field** must support:
  - Real-time validation of IP/port format
  - Integration with `SessionManager.ip_changed` signal
  - Automatic population from log filename parsing
- **Connection Workflow**:
  ```mermaid
  graph LR
    A[User enters IP] --> B{Valid format?}
    B -->|Yes| C[Connect Button enabled]
    B -->|No| D[Show validation error]
    C --> E[User clicks Connect]
    E --> F[Call VNCSession.connect()]
    F --> G{Connection successful?}
    G -->|Yes| H[Update status indicator]
    G -->|No| I[Show error dialog]
  ```

### 2. Clipboard Integration
- **Automatic Clipboard-to-Logfile**:
  - System monitors clipboard for changes
  - When log file is selected, clipboard content automatically written to file
  - Implemented via [`ClipboardMonitor`](src/commander/services/clipboard_monitor.py:1)
  - Triggered by `NodeManager.active_log_file` changes
- **Manual Copy Functionality**:
  - `copy_to_log_clicked` signal emitted when button pressed
  - Handled by `CommanderPresenter` clipboard service
  - Content written to both:
    - Application log file (`logs/application.log`)
    - Current session's log file (via `LogWriter`)
  - **Ctrl+C Implementation**:
    - Text selection in VNC viewer copies to system clipboard
    - Implemented via `VNCSession.text_selected` signal
    - Notification shown via `StatusService.show_message("Copied to clipboard")`
  - **Security Consideration**:
    - Sanitize clipboard content before logging
    - Implement rate limiting (max 5 operations/minute)

### 3. Dependency Mapping
| Component | Dependency | Purpose |
|-----------|------------|---------|
| VNCSession | `src/commander/session_manager.py` | Connection management |
| SessionManager | `src/commander/session_manager.py` | IP address coordination |
| LogWriter | `src/commander/log_writer.py` | Log file operations |
| ClipboardService | `src/commander/services/clipboard_service.py` | Clipboard access |

## Design Constraints
- **Theming**: Must inherit styling from `CommanderWindow` theme system
- **Responsive Behavior**:
  - Default resolution: 1024x768
  - VNC viewer container must resize with window while maintaining aspect ratio
  - Scalable within window constraints
  - Main Commander window should dynamically adjust its size to accommodate VNC viewer dimensions
  - Log area should maintain minimum height of 150px
- **Error Handling**:
  - Connection failures must show detailed error in log area
  - Automatic reconnection attempts limited to 3

## Implementation Roadmap
1. Create `VNCTab` class extending `QWidget`
2. Implement layout structure with QVBoxLayout
3. Integrate log filename parsing for IP extraction
4. Implement bottom-section connection controls matching Telnet tab pattern
5. Integrate clipboard monitoring service for automatic log writing
6. Add Ctrl+C text selection handling with clipboard notification
7. Implement session recording mechanism:
   - Capture mouse movements and clicks
   - Store as timestamped event sequence
   - Save to `recordings/vnc/[node_token]_[timestamp].vncr`
8. Integrate with `VNCSession` connection workflow
9. Connect clipboard functionality to existing signal system
10. Implement theme inheritance mechanism