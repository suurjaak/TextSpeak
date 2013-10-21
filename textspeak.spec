# -*- mode: python -*-
# Spec file for pyinstaller.
# To get this spec, run python Setup.py <specfile> in pyinstaller\ directory.
# Copy to pyinstaller\gui and in pyinstaller\ run python Build.py
import os
import platform
import sys
sys.path.append("")

import conf

a = Analysis([("textspeak.py")],)
pyz = PYZ(a.pure)

exename = "%s.exe" % conf.Title
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name=os.path.join("dist", exename),
    debug=False,  # Verbose or non-verbose 
    strip=False,  # EXE and all shared libraries run through cygwin's strip, tends to render Win32 DLLs unusable
    upx=True,     # Using Ultimate Packer for eXecutables
    icon="C:\\stuff\\projektid\\textspeak\\icon.ico",
    console=False # Use the Windows subsystem executable instead of the console one
)
