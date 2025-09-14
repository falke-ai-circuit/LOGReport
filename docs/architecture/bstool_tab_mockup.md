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

## Detailed UI Elements

### 1. Connection/Execution Bar

This horizontal bar will be at the top of the tab.

-   **Label:** `BsTool Path:`
-   **Input Field (BsTool Path):**
    -   Type: `QLineEdit`
    -   Placeholder: `e.g., C:\Program Files\BsTool\bstool.exe`
    -   Width: Occupies significant horizontal space.
-   **Label:** `Env Var:`
-   **Input Field (Environment Variable):**
    -   Type: `QLineEdit`
    -   Placeholder: `e.g., BSL_CONFIG=C:\config.json`
    -   Width: Shorter than the BsTool Path input, but sufficient for typical environment variable key-value pairs.
-   **Connect Button:**
    -   Type: `QPushButton`
    -   Text: `Connect`
    -   Initial State: Enabled
-   **Disconnect Button:**
    -   Type: `QPushButton`
    -   Text: `Disconnect`
    -   Initial State: Disabled
-   **Status Indicator:**
    -   Type: `QLabel`
    -   Content: A circular Unicode character (e.g., `●` for connected, `○` for disconnected, `◔` for connecting, `✖` for error).
    -   Color: Dynamically changes based on process state (e.g., green for running, gray for stopped, orange for starting, red for error).
    -   Font Size: Larger than surrounding text for visibility.

### 2. Output Display

This section will occupy the majority of the tab's vertical space.

-   **Display Area:**
    -   Type: `QTextEdit`
    -   Read-only: `True`
    -   Content: Displays all `stdout` and `stderr` output from the `bstool.exe` process.
    -   Scrollbar: Vertical scrollbar will appear as content exceeds visible area.
    -   Font: Monospaced font for clear console output readability.

### 3. Command Input

This horizontal bar will be located below the Output Display.

-   **Input Field (Command):**
    -   Type: `QLineEdit`
    -   Placeholder: `Enter command...`
    -   Width: Occupies significant horizontal space.
-   **Execute Button:**
    -   Type: `QPushButton`
    -   Text: `Execute`
    -   Initial State: Enabled (but commands will only be sent if `bstool.exe` is running).

### 4. Action Buttons

This horizontal bar will be at the bottom of the tab.

-   **Copy to Log Button:**
    -   Type: `QPushButton`
    -   Text: `Copy to Log`
-   **Clear Terminal Button:**
    -   Type: `QPushButton`
    -   Text: `Clear Terminal`
-   **Clear Log Button:**
    -   Type: `QPushButton`
    -   Text: `Clear Log`

---

## Visual Representation (Text-based ASCII Art)

```
+---------------------------------------------------------------------+
| BsTool Path: [ C:\Program Files\BsTool\bstool.exe         ] Env Var: [ BSL_CONFIG=C:\config.json ] [Connect] [Disconnect] ● |
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