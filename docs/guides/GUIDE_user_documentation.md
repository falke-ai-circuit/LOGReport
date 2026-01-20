# 📖 User Documentation Guide

<!-- METADATA -->
metadata: {
  created_date: "2025-10-08_174000",
  last_modified: "2025-10-08_174000",
  last_accessed: "2025-10-08_174000",
  word_count: 2134,
  reference_count: 3,
  document_hash: "user_documentation_guide",
  obsolete_check_date: "2025-10-08",
  section_count: 8,
  internal_link_count: 15
}
<!-- /METADATA -->

## 📑 Table of Contents

- [Overview](#overview)
- [Getting Started](#getting-started)
- [Basic Operations](#basic-operations)
- [Advanced Features](#advanced-features)
- [Troubleshooting](#troubleshooting)
- [Configuration](#configuration)
- [Best Practices](#best-practices)
- [FAQ](#faq)

---

## 🎯 Overview

Complete user guide for the LOGReport application - a command management and logging system for fieldbus and RPC protocols.

### What is LOGReport?

LOGReport is a PyQt6-based application that provides:
- **Node Management**: Organize and manage network nodes
- **Command Execution**: Execute FBC and RPC commands
- **Log Management**: Automatic token-based log organization
- **BsTool Integration**: Process logs with BsTool.exe
- **Batch Operations**: Execute commands on multiple tokens

### System Requirements

- **OS**: Windows 10/11 (64-bit)
- **Python**: 3.10+ (included in distribution)
- **RAM**: 2GB minimum, 4GB recommended
- **Disk**: 100MB for application, additional space for logs

---

## 🚀 Getting Started

### Installation

1. **Extract Archive**: Unzip LOGReport distribution to desired location
2. **Verify BsTool**: Ensure BsTool.exe is in the `bin/` directory
3. **Check Configuration**: Review `config/nodes.json`
4. **Run Application**: Execute `run_dev.ps1` (development) or `LOGReporter.exe` (production)

### First Launch

On first launch, LOGReport will:
1. Load node configuration from `config/nodes.json`
2. Scan log directories for existing logs
3. Build node tree in Commander Window
4. Display status in status bar

**Initial Setup Checklist**:
- [ ] Nodes loaded successfully
- [ ] Log directories accessible
- [ ] Node tree populated
- [ ] Status bar shows "Ready"

---

## 🔧 Basic Operations

### Viewing Nodes

**Node Tree Structure**:
```
📦 Nodes
├── 🟢 AP01m (Online, Successful)
│   ├── 🔵 162 (FBC Token)
│   ├── 🔵 163 (FBC Token)
│   └── 🔵 67890 (RPC Token)
└── 🔴 AP02m (Offline or Error)
    └── 🔵 164 (FBC Token)
```

**Node Colors**:
- 🟢 **Green**: Online, commands succeeded, logs have content (>5 lines)
- 🟡 **Yellow**: Online, commands succeeded, minimal log content (≤5 lines)
- 🔴 **Red**: Offline, command failed, or log error

### Executing Commands

**Single Token Execution**:
1. Right-click on token in node tree
2. Select command from context menu:
   - **Execute FBC Token**: Run FBC command
   - **Print RPC Counters**: Print RPC counters
   - **Clear RPC Counters**: Clear RPC counters
3. Monitor progress in status bar
4. Check results in log file

**Batch Execution**:
1. Select multiple tokens (Ctrl+Click or Shift+Click)
2. Right-click on selection
3. Choose batch command
4. Monitor progress bar for completion

### Viewing Logs

**Open Log File**:
1. Right-click on token
2. Select "Open Log Directory"
3. Navigate to token's log file

**Log File Naming**:
- FBC: `<node>_<ip>_<token>_FBC.log`
- RPC: `<node>_<ip>_<token>_RPC.log`

Example: `AP01m_192.168.0.11_162_FBC.log`

---

## 🚀 Advanced Features

### BsTool Integration

**Process Logs with BsTool**:
1. Execute FBC/RPC commands to generate logs
2. Right-click on token
3. Select "Process with BsTool"
4. BsTool analyzes log and generates report
5. View results in BsTool output

**BsTool Requirements**:
- BsTool.exe must be in `bin/` directory
- Log file must exist
- BsTool configured for log format

### Hierarchical Commands

Hierarchical commands execute multiple sub-commands in sequence:
1. FBC commands for all tokens
2. RPC commands for all tokens  
3. BsTool processing on all logs

**Execute Hierarchical Command**:
1. Right-click on node
2. Select "Execute Hierarchical Commands"
3. Monitor multi-stage progress
4. Review combined results

### Hybrid Token Resolution

LOGReport supports hybrid token resolution where FBC tokens can be used for RPC commands if dedicated RPC tokens are unavailable.

**How It Works**:
1. User requests RPC command on token
2. System looks for RPC token
3. If not found, system uses FBC token with same ID
4. Command executes successfully with FBC token metadata

**Benefits**:
- Reduces need for duplicate token definitions
- Simplifies configuration
- Maintains compatibility

See: [Token Management](../technical/TECH_token_management.md#hybrid-token-resolution)

---

## ⚠️ Troubleshooting

### Common Issues

#### Node Not Showing

**Symptom**: Node missing from tree

**Causes**:
- Node not in `config/nodes.json`
- Invalid JSON syntax
- Node marked as hidden

**Solutions**:
1. Check `config/nodes.json` for node entry
2. Validate JSON syntax
3. Restart application after config changes

#### Command Fails

**Symptom**: Red node color, error in logs

**Causes**:
- Network connectivity issue
- Invalid token ID
- Telnet timeout
- Node offline

**Solutions**:
1. Verify network connectivity to node
2. Check token ID is correct
3. Increase timeout in configuration
4. Verify node is powered on

#### Log File Not Created

**Symptom**: No log file after command execution

**Causes**:
- Log directory doesn't exist
- Insufficient permissions
- Disk full
- Path too long

**Solutions**:
1. Check log directory exists
2. Verify write permissions
3. Check available disk space
4. Shorten log path if needed

#### BsTool Fails

**Symptom**: BsTool error message

**Causes**:
- BsTool.exe not found
- Invalid log file format
- BsTool timeout

**Solutions**:
1. Verify BsTool.exe in `bin/` directory
2. Check log file format compatibility
3. Increase BsTool timeout setting

---

## ⚙️ Configuration

### Node Configuration

**File**: `config/nodes.json`

**Structure**:
```json
{
  "nodes": [
    {
      "name": "AP01m",
      "ip_address": "192.168.0.11",
      "status": "online",
      "tokens": {
        "FBC": ["162", "163"],
        "RPC": ["67890"]
      }
    }
  ]
}
```

**Fields**:
- `name`: Node identifier (required)
- `ip_address`: Node IP address (required)
- `status`: Initial status (`online` or `offline`)
- `tokens`: Token lists by protocol

### Application Settings

**File**: `config/settings.json`

**Common Settings**:
```json
{
  "telnet_timeout": 30,
  "log_directory": "logs/",
  "bstool_path": "bin/BsTool.exe",
  "auto_refresh": true,
  "max_log_size_mb": 100
}
```

### Context Menu Configuration

**File**: `config/context_menu.json`

Control which commands appear in context menus:
```json
{
  "filters": {
    "fbc_commands": {
      "visible_for": ["fbc_token", "node_with_fbc"],
      "conditions": {
        "node_online": true
      }
    }
  }
}
```

See: [Context Menu Blueprint](../blueprints/BLUEPRINT_context_menu.md#configuration)

---

## ✅ Best Practices

### Command Execution

1. **Test Single Before Batch**: Test commands on single token before batch execution
2. **Monitor Progress**: Watch progress bar and status messages during execution
3. **Check Logs**: Review logs after execution to verify success
4. **Handle Errors**: Address errors promptly before continuing

### Log Management

1. **Regular Cleanup**: Archive or delete old logs periodically
2. **Monitor Disk Space**: Ensure adequate disk space for logs
3. **Organize by Date**: Use date-based subdirectories for logs
4. **Backup Important Logs**: Save critical logs to separate location

### Configuration

1. **Backup Configs**: Backup configuration files before changes
2. **Validate JSON**: Use JSON validator before saving changes
3. **Test After Changes**: Test configuration changes with single node
4. **Document Changes**: Keep notes on configuration modifications

### Performance

1. **Limit Batch Size**: Don't execute too many tokens at once (recommended: 50-100)
2. **Use Sequential Mode**: Use sequential processor for large batches
3. **Monitor Memory**: Watch application memory usage
4. **Restart Periodically**: Restart application after processing large batches

---

## ❓ FAQ

### Q: How do I add a new node?

**A**: Edit `config/nodes.json`, add node entry with name, IP, and tokens, then restart application.

### Q: Can I execute commands on offline nodes?

**A**: No, nodes must be online and reachable for command execution.

### Q: What's the difference between FBC and RPC?

**A**: FBC (Fieldbus Command) and RPC (Remote Procedure Call) are different protocols for communication with nodes. FBC typically accesses IO structures, while RPC accesses RUPI counters.

### Q: How do I view command history?

**A**: Command history is stored in log files. Open the log directory to view previous command outputs.

### Q: Can I customize the context menu?

**A**: Yes, edit `config/context_menu.json` to control which commands appear for different node/token types.

### Q: How do I backup my configuration?

**A**: Copy the entire `config/` directory to a backup location. This includes all configuration files.

### Q: What if BsTool fails?

**A**: Ensure BsTool.exe is in the `bin/` directory, the log file format is correct, and you have sufficient permissions.

### Q: How do I report a bug?

**A**: Create an issue on the GitHub repository with:
- Steps to reproduce
- Expected vs actual behavior
- Log files (if applicable)
- Configuration files (redact sensitive info)

---

## 📚 References

### Related Documentation

- **[Node System](../architecture/ARCH_node_system.md)** - Node management details
- **[Command System](../architecture/ARCH_command_system.md)** - Command execution
- **[Commander Window](../technical/TECH_commander_window.md)** - UI guide

### Support

- **GitHub**: github.com/goranjovic55/LOGReport
- **Documentation**: See docs/ directory
- **Build Instructions**: BUILD-INSTRUCTIONS.md

---

**Document Status**: ✅ **COMPLETE** - Consolidated from 12 source documents
**Last Updated**: 2025-10-08
**Next Review**: 2026-01-08 (90 days)
