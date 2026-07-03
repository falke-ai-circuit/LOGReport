# LOGReport Commander

Go + React rewrite of the LOGReport tool. Single executable, no installation required.

## Download & Run

1. Download `LOGReporter.exe`
2. Place `nodes.json` in the same folder (or copy from the repo)
3. Place `BsTool.exe` in the same folder (if you have it)
4. Double-click `LOGReporter.exe`
5. Browser opens automatically at `http://localhost:8080`

## Features

| Tab | What it does |
|-----|-------------|
| **Log Processor** | Scan `_DIA/` folder → file groups → generate PDF report → download |
| **Commander** | All nodes in table, Scan All/Selected → reachable/port status + latency |
| **Telnet** | Connect to DNA node → terminal → `ps` / `fis` / `rc` command aliases |
| **Scan** | Parse `.fbc` IO table + `.rpc` error counter table per node/token |
| **BsTool** | Select node + token → run BsTool.exe → output terminal |
| **Sessions** | History of Telnet + BsTool sessions |

## BsTool Setup

BsTool.exe is **not included** in the binary. Place it next to `LOGReporter.exe`:

```
LOGReporter.exe
BsTool.exe          ← place here
nodes.json
```

Or embed it before building:
```bash
make embed-bstool BSTOOL_PATH=/path/to/BsTool.exe
make windows
```

## Command Line Options

```
LOGReporter.exe [options]
  --port N        HTTP port (default: auto-select from 8080)
  --nodes PATH    Path to nodes.json (default: next to executable)
  --no-browser    Don't auto-open browser
```

## Build from Source

```bash
# Prerequisites: Go 1.19+, Node 18+

cd go-backend

# Full release (React + all binaries)
make dist

# Windows .exe only
make windows

# Current OS
make all
```

## Compatibility

- **Windows 7 x64 and later** (primary target)
- Linux x64
- macOS (Intel + Apple Silicon)

## Architecture

```
LOGReporter.exe
├── Go HTTP server (Chi router, port 8080)
├── React frontend (embedded, served from /)
├── BsTool.exe (embedded when present, extracted to %TEMP%/logreport/)
└── nodes.json (read from same directory as .exe)
```

## nodes.json Format

```json
[
  {
    "name": "AP01m",
    "ip_address": "192.168.1.11",
    "status": "offline",
    "tokens": [
      { "token_id": "162", "port": 23 }
    ]
  }
]
```
