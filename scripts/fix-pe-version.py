#!/usr/bin/env python3
"""
Fix PE header version fields for Windows Server 2003 compatibility.

Go 1.22 sets PE OS/Image/Subsystem version to 6.1 (Windows 7) by default.
Server 2003 only supports up to 5.2 (x64) / 5.1 (x86/XP).

This script patches the PE header to set:
  - x86 (PE32):  OS=5.1, Image=5.1, Subsystem=5.1
  - x64 (PE32+): OS=5.2, Image=5.2, Subsystem=5.2

Usage: python3 scripts/fix-pe-version.py <exe1> [exe2 ...]
"""
import struct
import sys

def fix_pe_versions(filename):
    with open(filename, 'r+b') as f:
        # Read e_lfanew (offset to PE header)
        f.seek(0x3C)
        e_lfanew = struct.unpack('<I', f.read(4))[0]

        # Optional header starts at: e_lfanew + 4 (PE sig) + 20 (COFF header)
        opt_start = e_lfanew + 4 + 20

        # Read magic to determine PE32 vs PE32+
        f.seek(opt_start)
        magic = struct.unpack('<H', f.read(2))[0]

        if magic == 0x10b:  # PE32 (32-bit)
            major, minor = 5, 1
        elif magic == 0x20b:  # PE32+ (64-bit)
            major, minor = 5, 2
        else:
            print(f'{filename}: unknown PE magic 0x{magic:x}, skipping')
            return False

        # OS version at offset 40 from optional header start
        f.seek(opt_start + 40)
        f.write(struct.pack('<HH', major, minor))

        # Image version at offset 44
        f.seek(opt_start + 44)
        f.write(struct.pack('<HH', major, minor))

        # Subsystem version at offset 48
        f.seek(opt_start + 48)
        f.write(struct.pack('<HH', major, minor))

        # Verify
        f.seek(opt_start + 40)
        os_maj, os_min = struct.unpack('<HH', f.read(4))
        f.seek(opt_start + 44)
        img_maj, img_min = struct.unpack('<HH', f.read(4))
        f.seek(opt_start + 48)
        sub_maj, sub_min = struct.unpack('<HH', f.read(4))

        bits = 'x86' if magic == 0x10b else 'x64'
        print(f'{filename} ({bits}): OS={os_maj}.{os_min} Image={img_maj}.{img_min} Subsystem={sub_maj}.{sub_min}')
        return True

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: fix-pe-version.py <exe1> [exe2 ...]')
        sys.exit(1)
    for fn in sys.argv[1:]:
        fix_pe_versions(fn)