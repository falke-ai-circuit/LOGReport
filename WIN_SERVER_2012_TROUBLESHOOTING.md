# Windows Server 2012 Troubleshooting Guide

## Qt Platform Plugin Error

### Symptom
Application fails to start with error:
```
This application failed to start because no Qt platform plugin could be initialized.
Available platform plugins are: minimal, offscreen, windows.
```

### Root Cause
The Qt6 libraries bundled with LOGReport require **Visual C++ Redistributable 2015-2022** which may not be installed on Windows Server 2012 by default.

---

## Solution 1: Install Visual C++ Redistributable (RECOMMENDED)

### Steps:
1. **Download the installer:**
   - Visit: https://aka.ms/vs/17/release/vc_redist.x64.exe
   - Or search for "Visual C++ Redistributable 2015-2022 x64"

2. **Install with administrator privileges:**
   - Right-click the downloaded `vc_redist.x64.exe`
   - Select "Run as administrator"
   - Follow the installation wizard
   - Restart the computer if prompted

3. **Verify installation:**
   - Check `C:\Windows\System32\` for these files:
     - `vcruntime140.dll`
     - `vcruntime140_1.dll`
     - `msvcp140.dll`
     - `msvcp140_1.dll`
     - `msvcp140_2.dll`

4. **Run LOGReporter.exe again**

---

## Solution 2: Check Dependencies (DIAGNOSTIC)

Run the provided PowerShell script to identify missing DLLs:

```powershell
cd "path\to\LOGReporter"
powershell -ExecutionPolicy Bypass -File .\misc\scripts\check_dependencies.ps1
```

The script will:
- Check for required runtime DLLs
- Identify the Windows version
- Provide specific installation instructions
- Test the executable

---

## Solution 3: Enable Debug Output

If the error persists, enable detailed Qt debug output:

1. **Open Command Prompt** as administrator in the LOGReporter directory
2. **Run with debug environment variable:**
   ```cmd
   set QT_DEBUG_PLUGINS=1
   LOGReporter.exe
   ```

3. **Review the output** to identify which specific platform plugin or DLL is failing

The output will show:
- Plugin search paths
- Platform plugins found
- DLL loading attempts
- Specific failure reasons

---

## Technical Details

### What's Bundled
LOGReport now includes:
- ✅ BsTool.exe (automatic path detection)
- ✅ Visual C++ Runtime DLLs (vcruntime140*, msvcp140*)
- ✅ Qt6 platform plugins (qwindows.dll, qminimal.dll, qoffscreen.dll)
- ✅ Windows Server 2012 compatibility manifest

### Platform Fallback Logic
The application attempts to initialize Qt in this order:
1. **Auto-detect** (default)
2. **Windows** (native Windows GUI)
3. **Offscreen** (headless rendering)
4. **Minimal** (basic rendering)

If all platforms fail, the application displays:
```
ERROR: All platform options exhausted. Cannot start GUI.
Please install Visual C++ Redistributable 2015-2022 (x64)
Download: https://aka.ms/vs/17/release/vc_redist.x64.exe
```

---

## Verification Steps

After installing Visual C++ Redistributable:

1. **Check DLL files exist:**
   ```cmd
   dir C:\Windows\System32\vcruntime140*.dll
   dir C:\Windows\System32\msvcp140*.dll
   ```

2. **Run LOGReporter:**
   ```cmd
   cd "path\to\LOGReporter"
   LOGReporter.exe
   ```

3. **Verify functionality:**
   - Application window opens successfully
   - BsTool tab shows execution path (automatically detected)
   - Can connect to nodes
   - Can retrieve and process logs
   - Can generate PDF reports

---

## Still Not Working?

### Additional Checks:

1. **Windows Updates:**
   - Ensure Windows Server 2012 is fully updated
   - Install KB2999226 (Universal C Runtime update)
   - Download: https://support.microsoft.com/help/2999226

2. **NET Framework:**
   - Ensure .NET Framework 4.6.2 or later is installed
   - Some Qt components may require .NET framework

3. **System Architecture:**
   - Verify you're running 64-bit Windows Server 2012
   - LOGReporter.exe is compiled for x64 only

4. **Antivirus/Security:**
   - Temporarily disable antivirus
   - Check Windows Firewall isn't blocking the executable
   - Verify execution policy allows running the application

### Contact Information:
If none of these solutions work, provide the following information for support:
- Windows Server 2012 version (R2 or Standard)
- Output from `check_dependencies.ps1` script
- Qt debug output (`set QT_DEBUG_PLUGINS=1` output)
- Screenshot of the error message
- Event Viewer logs (Application section)

---

## Quick Reference

| Issue | Solution |
|-------|----------|
| Missing VC++ Runtime | Install from https://aka.ms/vs/17/release/vc_redist.x64.exe |
| BsTool not found | Check execution path in BsTool tab (auto-detected) |
| Qt plugin error | Install VC++ Redistributable + restart |
| Slow startup | Normal for first run (DLL loading), subsequent starts faster |
| Missing DLLs | Run `check_dependencies.ps1` script |

---

## Notes
- **Executable size:** 103 MB (includes all dependencies)
- **First run:** May take 10-15 seconds as DLLs are extracted
- **Subsequent runs:** 2-3 seconds startup time
- **Windows Server 2012 compatibility:** Explicitly declared in manifest
- **BsTool integration:** Automatic path detection (no configuration needed)
