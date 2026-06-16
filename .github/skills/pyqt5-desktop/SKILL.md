# PyQt5 Desktop Skill

> `@pyqt5-desktop` | PyQt5 GUI development patterns

## Triggers

| Pattern | Type |
|---------|------|
| .py src/ gui.py | Files |
| src/commander/ | Directories |
| PyQt5 QWidget QMainWindow | Keywords |

## Methodology
1. **Understand** - Review widget hierarchy and signals
2. **Plan** - Design UI flow and state management
3. **Implement** - Follow Qt patterns
4. **Verify** - Test in noVNC or local display

## Patterns

### Widget Structure
```python
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout
from PyQt5.QtCore import Qt, pyqtSignal

class MyWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Title")
        self.setup_ui()
    
    def setup_ui(self):
        central = QWidget()
        layout = QVBoxLayout(central)
        self.setCentralWidget(central)
```

### Signals & Slots
```python
# Connect signal to slot
button.clicked.connect(self.on_click)

# Custom signal
class MyWidget(QWidget):
    data_changed = pyqtSignal(str)
    
    def emit_change(self, value):
        self.data_changed.emit(value)
```

### Threading (Worker Pattern)
```python
from PyQt5.QtCore import QThread, pyqtSignal

class Worker(QThread):
    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    
    def run(self):
        try:
            result = self.do_work()
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))
```

## ⚠️ Gotchas

| Issue | Solution |
|-------|----------|
| QAction import | `from PyQt5.QtWidgets import QAction` (not QtGui) |
| Enum format | `Qt.white` not `Qt.GlobalColor.white` |
| exec() method | Use `app.exec()` (PyQt5) not `app.exec_()` |
| Thread UI updates | Use signals, never update UI from worker thread |
| Modal dialogs | Use `dialog.exec()` for blocking, `dialog.show()` for non-blocking |

## File Locations

| Component | Path |
|-----------|------|
| Main GUI | `src/gui.py` |
| Node Dialog | `src/node_config_dialog.py` |
| Workers | `src/gui_workers.py` |
| Commander GUI | `src/commander/` |

## Docker noVNC Testing
```bash
# Start container
docker compose up -d

# Access GUI
# Browser: http://localhost:6080/vnc.html
# Codespaces: https://<name>-6080.app.github.dev/vnc.html

# Change resolution
RESOLUTION=1920x1080x24 docker compose up -d
```
