# VNC Session Recording Blueprint

## Overview
This blueprint defines the architecture for capturing, storing, and replaying VNC session interactions within the LOGReport application. The implementation enables users to record terminal sessions for audit, training, and debugging purposes.

## Core Components

### 1. Event Capture System
- **Input Event Interception**
  - Captures mouse movements, clicks, keyboard inputs, and clipboard operations
  - Implemented as decorator pattern around existing VNC session handlers
  - Timestamp precision: 10ms resolution using system monotonic clock
  - Event structure:
    ```typescript
    interface SessionEvent {
      timestamp: number; // Unix timestamp in ms
      type: 'mouse' | 'keyboard' | 'clipboard' | 'screen';
      data: {
        x?: number;       // Mouse X coordinate
        y?: number;       // Mouse Y coordinate
        button?: string;  // Mouse button
        key?: string;     // Keyboard key
        clipboard?: string; // Clipboard content
        screen?: string;  // Base64-encoded screen diff
      };
    }
    ```

### 2. Storage Format (.vncr)
- **File Structure**
  ```
  [HEADER]
  MAGIC: "VNCREC"
  VERSION: 1.0
  METADATA: { 
    startTime: ISO8601, 
    endTime: ISO8601,
    node: string,
    sessionType: "VNC"
  }
  
  [EVENT STREAM]
  [TIMESTAMP][EVENT_TYPE][PAYLOAD_LENGTH][PAYLOAD]
  ```
- **Optimization Strategies**
  - Delta encoding for screen updates (only changed regions)
  - GZIP compression applied at 500ms intervals
  - Maximum file size: 500MB (configurable in `config/settings/recording.yaml`)
  - Automatic rotation when threshold reached

### 3. Replay System
- **Playback Engine**
  - Event queue processor with adjustable speed (0.5x-2.0x)
  - Synchronization with original timing or accelerated mode
  - Visual indicators for mouse movements and clicks
  - Integration with existing session view components:
    ```python
    class SessionPlayer:
        def __init__(self, vnc_view: SessionView):
            self.vnc_view = vnc_view
            self.event_queue = PriorityQueue()
        
        def load_recording(self, file_path: str):
            # Parse .vncr file and populate event queue
        
        def play(self, speed: float = 1.0):
            # Process events with timing adjustments
    ```

## Integration Points

### 1. Session Manager Integration
- Extended `VNCSession` class with recording capabilities:
  ```python
  class VNCSession(BaseSession):
      def start_recording(self, output_path: str):
          self.recorder = SessionRecorder(output_path)
          self.recorder.start()
          
      def stop_recording(self):
          self.recorder.stop()
          return self.recorder.finalize()
  ```

### 2. UI Components
- **Recording Controls** (added to VNC tab toolbar):
  - Record button (red circle icon)
  - Pause/resume button
  - Playback speed selector
  - Timeline scrubber
- **Status Indicators**:
  - Recording duration counter
  - Storage usage meter
  - Visual recording indicator (pulsing red dot)

### 3. Configuration
- `config/settings/recording.yaml`:
  ```yaml
  session_recording:
    enabled: true
    max_file_size: 500 # MB
    compression_level: 6
    storage_path: "test_logs/recordings"
    screen_capture_interval: 100 # ms
    clipboard_capture: true
  ```

## Security Considerations
- **Data Protection**
  - Automatic redaction of sensitive patterns (passwords, tokens)
  - Configurable encryption for stored recordings
  - Access control via existing session permissions
- **Compliance**
  - GDPR-compliant data handling
  - Audit trail for recording access
  - Automatic deletion after retention period

## Implementation Roadmap

| Phase | Components | Timeline |
|-------|------------|----------|
| 1 | Event capture infrastructure, basic storage format | Week 1 |
| 2 | UI integration, playback engine | Week 2 |
| 3 | Security features, configuration system | Week 3 |
| 4 | Performance optimization, testing | Week 4 |

## Dependencies
- `src/commander/session_manager.py` (VNC session handling)
- `src/commander/ui/session_view.py` (display components)
- `src/commander/utils/token_utils.py` (sensitive data detection)
- `config/settings/recording.yaml` (configuration)

## Validation Criteria
- [ ] Recordings maintain 95%+ visual fidelity to original sessions
- [ ] Playback accurately reproduces timing at 1.0x speed
- [ ] Recording overhead < 15% CPU usage during normal operation
- [ ] .vncr files 60-70% smaller than raw event streams
- [ ] All sensitive data patterns properly redacted in recordings