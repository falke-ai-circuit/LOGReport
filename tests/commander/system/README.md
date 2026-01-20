# BsTool System Integration Tests

This directory contains system tests for verifying the end-to-end integration of BsTool with the LOGReport application.

## Test Overview

The system test performs the following steps:

1. **Build Process Verification**: Ensures the application builds correctly with `BsTool.exe` bundled
2. **Application Launch**: Launches the bundled `LOGReporter.exe`
3. **UI Interaction Simulation**: Simulates user interaction with the context menu
4. **BsTool Execution Verification**: Verifies `BsTool.exe` executes with the correct environment
5. **Output Validation**: Confirms output is correctly appended to log files

## Test Files

- `test_bstool_system_integration.py` - Main system test implementation
- `test_bstool_path_persistence_e2e.py` - End-to-end test for bstool path persistence across application restarts

## Running the Tests

### Prerequisites

1. Ensure all dependencies are installed:
   ```bash
   pip install -r requirements-test.txt
   ```

2. Make sure `BsTool.exe` is present in the project root directory

### Running Build Verification Test

```bash
# Run only the build verification test
python -m pytest tests/commander/system/test_bstool_system_integration.py::TestBsToolSystemIntegration::test_bstool_build_process -v
```

### Running Direct Execution Test

```bash
# Run the direct execution test (bypasses UI automation)
python -m pytest tests/commander/system/test_bstool_system_integration.py::TestBsToolSystemIntegration::test_bstool_direct_execution -v
```

### Running Full System Test

```bash
# Run the full system test (requires UI automation libraries)
python -m pytest tests/commander/system/test_bstool_system_integration.py::TestBsToolSystemIntegration::test_bstool_full_system_integration -v
```

### Running BsTool Path Persistence Test

```bash
# Run the bstool path persistence end-to-end test
python -m pytest tests/commander/system/test_bstool_path_persistence_e2e.py -v
```

### Running All Tests

```bash
# Run all system tests
python -m pytest tests/commander/system/test_bstool_system_integration.py -v
```

## Test Markers

- `@pytest.mark.slow` - Indicates tests that take longer to execute
- `@pytest.mark.skipif` - Skips tests when dependencies are not available

## Implementation Details

### UI Automation Framework

The test includes a framework for UI automation using:
- `pyautogui` for mouse/keyboard simulation
- `pywin32` for Windows API interactions
- `psutil` for process management

The UI automation portion requires specific coordinates to be determined for the actual application UI. The framework is in place but would need to be customized with the correct coordinates for full automation.

### Direct Execution Test

As an alternative to UI automation, the test includes a direct execution method that verifies the core functionality without simulating the UI. This test:
1. Builds the application
2. Executes `BsTool.exe` directly with the required environment variables
3. Verifies the output is correctly appended to log files

### Path Persistence Test

The bstool path persistence test verifies that:
1. The bstool path is correctly saved to QSettings when changed in the UI
2. The bstool path is correctly loaded from QSettings when the application restarts
3. The loaded path is properly displayed in the UI

## Environment Variables

The test specifically verifies that `BsTool.exe` is executed with:
```
COMMUNICATION_LINE=AB01
```

## Test Artifacts

The test creates temporary directories and files during execution:
- Temporary build directory
- Test log files
- Build artifacts in `dist/` and `build/` directories

All artifacts are cleaned up after test execution.

## Troubleshooting

### Missing Dependencies

If you see import errors, install the test dependencies:
```bash
pip install -r requirements-test.txt
```

### Build Failures

Ensure:
1. `BsTool.exe` is in the project root
2. PyInstaller is properly installed
3. No antivirus software is blocking the build process

### UI Automation Issues

If UI automation tests fail:
1. Ensure the application window can be found
2. Verify screen coordinates for UI elements
3. Check that the application has proper focus during testing