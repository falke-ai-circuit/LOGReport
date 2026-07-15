# 🔧 BsTool Integration Blueprint

<!-- RECONCILIATION NOTE (2026-07-15 — Coder)
     This blueprint describes the ORIGINAL Python-era BsTool integration design.
     The Go implementation has evolved significantly beyond this design:
     - BsTool is now a native Go TCP client (internal/bstool/) using reverse-engineered protocol
     - BsTool.exe subprocess support added (v3.9.56, local_exe scan method)
     - Subprocess-first, TCP-fallback via executeBsToolErrLog() in handlers_bstool_exec.go
     - TCP timeout minimum raised to 5s (v3.9.57, was 1516ms serial-era default)
     - COMMUNICATION_LINE env var passed to subprocess
     This document is preserved as historical design reference only.
-->

<!-- METADATA -->
metadata: {
  created_date: "2025-10-08_172000",
  last_modified: "2025-10-08_172000",
  last_accessed: "2025-10-08_172000",
  word_count: 1524,
  reference_count: 3,
  document_hash: "bstool_integration_blueprint",
  obsolete_check_date: "2025-10-08",
  section_count: 6,
  internal_link_count: 12
}
<!-- /METADATA -->

## 📑 Table of Contents

- [Overview](#overview)
- [BsTool Architecture](#bstool-architecture)
- [Integration Design](#integration-design)
- [Command Processing](#command-processing)
- [Error Handling](#error-handling)
- [Implementation Plan](#implementation-plan)

---

## 🎯 Overview

Blueprint for integrating BsTool.exe (Binary Scanner Tool) with the LOGReport application for automated log analysis and processing.

### Key Features

| Feature | Description | Benefit |
|---------|-------------|---------|
| **Process Wrapper** | Python subprocess wrapper for BsTool.exe | Programmatic control |
| **Batch Processing** | Process multiple log files sequentially | Automation |
| **Error Detection** | Parse BsTool output for errors | Reliability |
| **Result Integration** | Store BsTool results in application | Unified workflow |

---

## 🏗️ BsTool Architecture

BsTool is an external Windows executable for binary log analysis.

**BsTool Capabilities**:
- Parse binary log files (.fbc, .rpc)
- Extract structured data from logs
- Generate analysis reports
- Detect anomalies and errors

**Integration Approach**: Subprocess wrapper with output parsing

---

## 🔄 Integration Design

**Integration Architecture**:
```
LOGReport Application
    ├── BsToolCommandService
    │   ├── Execute BsTool.exe
    │   ├── Parse Output
    │   └── Handle Errors
    ├── BsToolResultParser
    │   ├── Parse Text Output
    │   └── Extract Structured Data
    └── Sequential Processor
        └── Batch BsTool Execution
```

**Execution Flow**:
1. User requests BsTool processing (context menu or batch)
2. BsToolCommandService prepares command
3. Subprocess executes BsTool.exe with log file path
4. Output captured and parsed
5. Results stored and displayed
6. Status updated in UI

See: [Command System](../architecture/ARCH_command_system.md#protocol-services)

---

## ⚙️ Command Processing

**BsTool Command Service**:
```python
class BsToolCommandService:
    """Service for BsTool.exe integration."""
    
    def execute_bstool(self, log_path: str, args: List[str] = None) -> dict:
        """
        Execute BsTool on log file.
        
        Args:
            log_path: Path to log file
            args: Additional BsTool arguments
        
        Returns:
            Dict with execution results
        """
        # Prepare command
        cmd = [self.bstool_path, log_path]
        if args:
            cmd.extend(args)
        
        # Execute subprocess
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # Parse output
        parsed = self._parse_output(result.stdout)
        
        return {
            'success': result.returncode == 0,
            'output': result.stdout,
            'error': result.stderr,
            'parsed_data': parsed
        }
```

---

## ⚠️ Error Handling

**Error Scenarios**:
- BsTool.exe not found
- Invalid log file path
- BsTool execution timeout
- Parse errors in output

**Error Handling Strategy**:
```python
try:
    result = execute_bstool(log_path)
except FileNotFoundError:
    # BsTool.exe not found
    logging.error("BsTool.exe not found at: %s", bstool_path)
    show_error("BsTool.exe not found")
except subprocess.TimeoutExpired:
    # Execution timeout
    logging.error("BsTool execution timeout")
    show_error("BsTool execution timed out")
except Exception as e:
    # Unexpected error
    logging.error("BsTool execution failed: %s", str(e))
    show_error(f"BsTool failed: {str(e)}")
```

---

## 📋 Implementation Plan

**Phase 1: Basic Integration**
- Create BsToolCommandService
- Implement subprocess wrapper
- Add basic error handling

**Phase 2: Output Parsing**
- Develop BsToolResultParser
- Parse structured data from output
- Store results in application

**Phase 3: UI Integration**
- Add BsTool commands to context menu
- Display BsTool results in UI
- Add progress feedback

**Phase 4: Batch Processing**
- Integrate with Sequential Processor
- Support batch BsTool execution
- Add circuit breaker protection

---

## 📚 References

### Related Documentation

- **[Command System](../architecture/ARCH_command_system.md)** - Command service architecture
- **[Integration Points](BLUEPRINT_integration_points.md)** - System integration details
- **[Implementation Phases](BLUEPRINT_implementation_phases.md)** - Implementation roadmap

### Source Code

- **BsTool Service**: `src/commander/services/bstool_command_service.py`
- **Result Parser**: `src/utils/bstool_parser.py`

---

**Document Status**: ✅ **COMPLETE** - Consolidated from 6 source documents
**Last Updated**: 2025-10-08
**Next Review**: 2026-01-08 (90 days)
