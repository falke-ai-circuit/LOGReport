# Quick Build Guide - Nuitka

## TL;DR - Fast Start

```powershell
# 1. Install Nuitka
pip install nuitka

# 2. Get UPX (optional, for 50-70% size reduction)
.\download_upx.bat

# 3. Build
.\build_nuitka.bat

# 4. Run
.\dist\LOGReporter.exe
```

## Build Options

| Script | Time | Output | Use Case |
|--------|------|--------|----------|
| `build_nuitka.bat` | 15-25 min | Single .exe (20-40MB with UPX) | Production release |
| `build_nuitka_fast.bat` | 3-5 min | Directory with .exe | Development testing |
| `build.bat` (PyInstaller) | 2-3 min | Single .exe (60MB) | Quick builds |

## Size Comparison

| Build Type | Size | Speed | Compression Time |
|------------|------|-------|------------------|
| PyInstaller | ~60MB | Baseline | N/A |
| Nuitka (no UPX) | ~50-100MB | 2-4x faster | N/A |
| Nuitka + UPX --best | ~30-40MB | 2-4x faster | +1-2 min |
| **Nuitka + UPX --ultra-brute** | **~20-30MB** | **2-4x faster** | **+2-5 min** |

## What's Different?

### Nuitka Advantages
- ✅ Compiles Python to C → Native executable
- ✅ 2-4x faster runtime performance
- ✅ Faster startup (no unpacking)
- ✅ Better memory efficiency
- ✅ LTO (Link-Time Optimization)

### UPX Compression
- ✅ 50-70% size reduction
- ✅ `--best --lzma --ultra-brute` = maximum compression
- ✅ Transparent decompression at runtime
- ✅ No performance penalty after startup
- ⚠️ Adds 2-5 minutes to build time
- ⚠️ Some antivirus may flag (false positive)

## First Time Setup

```powershell
# 1. Verify Python
python --version  # Should be 3.10+

# 2. Install dependencies
pip install -r requirements.txt
pip install nuitka

# 3. Get UPX for compression
.\download_upx.bat
# OR manually: https://github.com/upx/upx/releases

# 4. Verify BsTool.exe exists
dir BsTool.exe

# 5. Build!
.\build_nuitka.bat
```

## Compression Levels Explained

| UPX Level | Size | Time | Command |
|-----------|------|------|---------|
| None | 100% | 0 min | (skip UPX) |
| `--best` | 60-70% | +1 min | `upx --best file.exe` |
| `--best --lzma` | 50-60% | +2 min | `upx --best --lzma file.exe` |
| **`--best --lzma --ultra-brute`** | **40-50%** | **+3-5 min** | **Our default** |

**Our choice:** `--ultra-brute` because:
- Build happens once, run happens many times
- 20-30MB vs 100MB = easier distribution
- Worth the extra 3-5 minutes for release builds

## Troubleshooting Quick Fixes

```powershell
# "Nuitka not found"
pip install nuitka

# "UPX not found" (WARNING, not error)
.\download_upx.bat
# Build still works, just larger file

# "BsTool.exe not found" (ERROR)
# Place BsTool.exe in project root

# "Build failed - out of memory"
# Close other applications, try again

# "Antivirus blocks UPX exe"
# Add exception or build without UPX
```

## When to Use What?

### Use `build_nuitka.bat` (Production)
- ✅ Final release builds
- ✅ Distribution to users
- ✅ Need smallest file size
- ✅ Need best performance
- ❌ Don't use for rapid iteration

### Use `build_nuitka_fast.bat` (Development)
- ✅ Testing during development
- ✅ Quick iterations
- ✅ Don't need single file
- ❌ Don't use for distribution

### Use `build.bat` (PyInstaller)
- ✅ Fastest possible build
- ✅ Emergency builds
- ✅ Testing build system
- ❌ Larger file, slower runtime

## Build Time Breakdown

**Total: ~15-25 minutes (first build)**

| Phase | Time | Can Skip? |
|-------|------|-----------|
| Analysis | 1-2 min | ❌ Required |
| C Compilation | 8-12 min | ❌ Required |
| Linking | 2-3 min | ❌ Required |
| Onefile Packaging | 1-2 min | ❌ Required |
| UPX Compression | 2-5 min | ✅ Optional |

**Subsequent builds: ~5-8 minutes** (Nuitka caches unchanged modules)

## File Locations

```
After build:
├── dist/
│   └── LOGReporter.exe          # YOUR FINAL EXECUTABLE
├── main.build/                  # Temp (can delete)
├── main.onefile-build/          # Temp (can delete)
└── upx/
    └── upx.exe                  # Compression tool
```

## Testing Checklist

After build completes:

```powershell
# 1. Check file size
dir dist\LOGReporter.exe

# 2. Run executable
.\dist\LOGReporter.exe

# 3. Test features
- [ ] GUI opens
- [ ] BsTool path detected
- [ ] Can add nodes
- [ ] Can generate report
- [ ] All tabs work

# 4. Check performance
- [ ] Fast startup (< 2 sec)
- [ ] Responsive UI
- [ ] Report generation works
```

## Distribution

**Ready to ship:**
```
dist/LOGReporter.exe  →  Copy to anywhere, run directly
```

**No installation needed!**
- ✅ Single file
- ✅ All dependencies included
- ✅ BsTool.exe bundled inside
- ✅ Works on any Windows PC
- ✅ Extracts to %TEMP%\LOGReporter at runtime

## Support

Full documentation: [NUITKA_BUILD_INSTRUCTIONS.md](NUITKA_BUILD_INSTRUCTIONS.md)

Issues?
1. Check error message
2. Check troubleshooting section
3. Try fast build to isolate issue
4. Check Nuitka logs in `main.build/`
