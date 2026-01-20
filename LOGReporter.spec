# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for LOGReporter with Windows Server 2012 compatibility

block_cipher = None

# Add path to avoid missing modules
import sys
import os
sys.path.append(os.path.abspath('src'))

# Custom Windows manifest with Windows Server 2012/2012 R2 support
# Includes compatibility declarations for Vista through Windows 11 and all Server versions
manifest_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
  <assemblyIdentity
    version="1.0.0.0"
    processorArchitecture="amd64"
    name="LOGReporter"
    type="win32"/>
  <trustInfo xmlns="urn:schemas-microsoft-com:asm.v3">
    <security>
      <requestedPrivileges>
        <requestedExecutionLevel level="asInvoker" uiAccess="false"/>
      </requestedPrivileges>
    </security>
  </trustInfo>
  <compatibility xmlns="urn:schemas-microsoft-com:compatibility.v1">
    <application>
      <!-- Windows Vista / Server 2008 -->
      <supportedOS Id="{e2011457-1546-43c5-a5fe-008deee3d3f0}"/>
      <!-- Windows 7 / Server 2008 R2 -->
      <supportedOS Id="{35138b9a-5d96-4fbd-8e2d-a2440225f93a}"/>
      <!-- Windows 8 / Server 2012 -->
      <supportedOS Id="{4a2f28e3-53b9-4441-ba9c-d69d4a4a6e38}"/>
      <!-- Windows 8.1 / Server 2012 R2 -->
      <supportedOS Id="{d78f2640-1f3f-11e3-8fae-00144feabdc0}"/>
      <!-- Windows 10 / Server 2016/2019/2022 -->
      <supportedOS Id="{8e0f7a12-bfb3-4fe8-b9a5-48fd50a15a9a}"/>
      <!-- Windows 11 -->
      <supportedOS Id="{1f676c76-80e1-4239-95bb-83d0f6d0da78}"/>
    </application>
  </compatibility>
  <application xmlns="urn:schemas-microsoft-com:asm.v3">
    <windowsSettings>
      <longPathAware xmlns="http://schemas.microsoft.com/SMI/2016/WindowsSettings">true</longPathAware>
    </windowsSettings>
  </application>
</assembly>
'''

a = Analysis(
    ['src/main.py'],
    pathex=[os.getcwd()],
    binaries=[
        # Bundle BsTool.exe in same directory as LOGReporter.exe
        (os.path.abspath('BsTool.exe'), '.')
    ],
    datas=[
        ('src/nodes.json', 'src'),
        ('version_info.txt', '.'),
        (os.path.abspath('assets'), 'assets')
    ],
    hiddenimports=[
        'docx',
        'PyQt5',
        'PyQt5.QtCore',
        'PyQt5.QtWidgets',
        'PyQt5.QtGui',
        'reportlab',
        'PIL'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['src/runtime_hooks/runtime_hook.py'],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='LOGReporter',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    console=True,
    icon=None,
    version='version_info.txt',
    manifest=manifest_xml,
)
