# VNC Tab Visual Mockup

## Overview
This mockup provides a visual representation of the VNC tab layout as implemented in the Command Center UI. The design follows the blueprint specifications with clear visual hierarchy and consistent styling.

## ASCII Diagram

```
+-----------------------------------------------------+
| Log Context Bar (10% height)                        |
|-----------------------------------------------------|
| Log: [AP01m_192-168-0-11_162.fbc]                   |
+-----------------------------------------------------+
| VNC Viewer Area (70% height)                        |
|-----------------------------------------------------|
|  ________________________________________________   |
| |                                                |  |
| |           Remote Desktop Display               |  |
| |                                                |  |
| |________________________________________________|  |
|  [Scrollbars]                                     |
+-----------------------------------------------------+
| Connection Controls (10% height)                    |
|-----------------------------------------------------|
| IP: [192.168.0.11]  Port: [5900]  [Connect]         |
| Status: [Disconnected]                              |
+-----------------------------------------------------+
| Action Controls (10% height)                        |
|-----------------------------------------------------|
| [Copy to Log]  [Record]  Log Type: [FBC▼]  Status: Ready |
+-----------------------------------------------------+
```

## Component Details
- **Log Context Bar**:
  - Shows currently selected log filename
  - Auto-updates when node selection changes
- **VNC Viewer**:
  - Default resolution: 1024x768
  - Scalable with window resizing; main Commander window adjusts size accordingly
  - Scrollable viewport for remote desktop
  - Fixed aspect ratio matching target display
  - Zoom controls for high-resolution displays
  - Status indicators for connection quality
- **Action Controls**:
  - Primary 'Copy to Log' action button (highlighted)
  - 'Record Session' button for VNC session recording
  - Log type dropdown (FBC/LIS/LOG/RPC with FBC default)
  - Status message area with auto-clear (2 seconds)

## Styling Specifications
- **Color Scheme**: 
  - Background: #2D2D2D (dark theme)
  - Text: #D4D4D4 (light gray)
  - Accent: #007ACC (blue for interactive elements)
- **Typography**: 
  - Font: Consolas (10pt)
  - Monospace for all technical content
- **Spacing**:
  - 8px padding between sections
  - 4px internal padding for controls
  - Consistent with existing Telnet tab layout

## Responsive Behavior
- **Window Resize**:
  - Default resolution: 1024x768
  - VNC viewer maintains aspect ratio and scales within window
  - Scrollbars appear when content exceeds viewport
  - Main Commander window dynamically adjusts size to maintain optimal viewing area
  - ConnectionBar and Clipboard Controls maintain fixed height
- **Node Selection Change**:
  - IP address updates immediately
  - Connection state resets to "disconnected"
  - Viewer area clears until new connection established