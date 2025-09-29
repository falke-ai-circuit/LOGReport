# BsTool Tab Visual Mockup

## Overview
This mockup describes the visual layout and key interactive elements of the new BsTool tab, designed to be consistent with the existing Telnet tab's aesthetic and functionality.

## Layout Structure

The tab will be organized into several vertical sections, similar to the Telnet tab:

1.  **Connection/Execution Bar (Top Section)**
2.  **Output Display (Middle Section)**
3.  **Command Input (Lower-Middle Section)**
4.  **Action Buttons (Bottom Section)**

---

## 🎯 UI Elements Summary

| Element | Type | Description | State/Content |
|---|---|---|---|
| **BsTool Path Label** | `QLabel` | Identifies path input | `BsTool Path:` |
| **BsTool Path Input** | `QLineEdit` | User-editable path | `e.g., C:\\Program Files\\BsTool\\bstool.exe` |
| **Env Var Label** | `QLabel` | Identifies environment variable | `Env Var:` |
| **Env Var Display** | `QLabel` | Fixed environment variable | `COMMUNICATION_LINE=AB01` |
| **Status Indicator** | `QLabel` | Process status | `●` (running) `○` (stopped) `◔` (starting) `✖` (error) |
| **Output Display** | `QTextEdit` | `stdout`/`stderr` from `bstool.exe` | Read-only, monospaced font, scrollable |
| **Command Input** | `QLineEdit` | User command entry | `Enter command...` |
| **Execute Button** | `QPushButton` | Sends command to `bstool.exe` | Enabled (if `bstool.exe` running) |
| **Copy to Log Button** | `QPushButton` | Copies output to log | `Copy to Log` |
| **Clear Terminal Button** | `QPushButton` | Clears output display | `Clear Terminal` |
| **Clear Log Button** | `QPushButton` | Clears associated log file | `Clear Log` |

---

## Visual Representation (Text-based ASCII Art)

```
+---------------------------------------------------------------------+
| BsTool Path: [ C:\Program Files\BsTool\bstool.exe         ] COMMUNICATION_LINE=AB01 ● |
+---------------------------------------------------------------------+
|                                                                     |
|                                                                     |
|  BsTool Output:                                                     |
|  > Initializing bstool...                                           |
|  > BsTool ready.                                                    |
|  >                                                                  |
|  >                                                                  |
|  >                                                                  |
|  >                                                                  |
|                                                                     |
+---------------------------------------------------------------------+
| Command: [                                                ] [Execute] |
+---------------------------------------------------------------------+
| [Copy to Log] [Clear Terminal] [Clear Log]                          |
+---------------------------------------------------------------------+