# LOGReport Build Instructions

## Requirements
- Python 3.10+
- Windows OS (for .exe build)
- BsTool.exe in project root directory

## Step-by-Step Build Process
1. **Install dependencies**:
   ```cmd
   pip install -r requirements-narrow.txt
   ```

2. **Set up environment**:
   ```cmd
   mkdir assets
   ```
   Place your application icon at `assets\logo.ico`

3. **Ensure BsTool.exe is present**:
   Verify `BsTool.exe` exists in the project root directory. It will be automatically bundled with the application.

4. **Run build script**:
   ```cmd
   build.bat
   ```
   Or manually using PyInstaller:
   ```cmd
   python -m PyInstaller LOGReporter.spec
   ```

5. **Locate executable**:  
   The built executable will be at:  
   `dist\LOGReporter.exe`
   
   BsTool.exe will be bundled inside the executable and automatically extracted at runtime.

## BsTool Integration
- **Bundling**: BsTool.exe is packaged as a binary resource in LOGReporter.spec
- **Path Detection**: Application automatically detects BsTool.exe location:
  - **Frozen (packaged)**: Uses `sys._MEIPASS` or `sys.executable` directory
  - **Development**: Uses project root directory
- **No Manual Configuration**: Path is automatically determined at runtime

## Windows Server 2012 Compatibility
The application includes a custom Windows manifest with explicit support for:
- Windows Vista / Server 2008
- Windows 7 / Server 2008 R2
- **Windows 8 / Server 2012** ✓
- **Windows 8.1 / Server 2012 R2** ✓
- Windows 10 / Server 2016/2019/2022
- Windows 11

This ensures compatibility with older Windows Server versions commonly used in enterprise environments.

## Customization Options
- **Icon**: Replace `assets\logo.ico`
- **Metadata**: Edit `version_info.txt`
- **App name**: Modify `name` in LOGReporter.spec
- **Manifest**: Edit `manifest_xml` in LOGReporter.spec for OS compatibility

## Post-Build Testing
Verify functionality by:
1. Running the executable
2. Testing BsTool tab functionality (automatic path detection)
3. Testing node connections
4. Retrieving sample logs
5. Generating PDF reports

## Troubleshooting
- **Missing dependencies**: Run `pip install -r requirements-narrow.txt`
- **Missing BsTool.exe**: Ensure BsTool.exe is in project root before building
- **BsTool not found at runtime**: Check application logs for path detection details
- **Missing icon**: Place a valid .ico file in assets or remove `icon` from spec
- **PyInstaller errors**: Try `--clean` switch: `pyinstaller --clean LOGReporter.spec`
- **Windows Server 2012 issues**: Verify manifest includes Server 2012 supportedOS entries

## Notes
- Linux/macOS builds require platform-specific modifications
- Executable size can be reduced with UPX compression (enabled by default)
- One-file mode creates a single executable with all dependencies bundled
- BsTool.exe path is resolved automatically - no configuration needed
