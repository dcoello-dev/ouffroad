# -*- mode: python ; coding: utf-8 -*-

import sys
from PyInstaller.utils.hooks import copy_metadata

block_cipher = None

# Include metadata for packages that use it (like uvicorn, fastapi)
datas = []
datas += copy_metadata('uvicorn')
datas += copy_metadata('fastapi')
datas += copy_metadata('requests')

# Add frontend build
# Source: ../front/app/dist
# Destination: ouffroad/front (relative to the executable's internal root)
datas += [('../front/app/dist', 'ouffroad/front')]

a = Analysis(
    ['run.py'],
    pathex=['../src'],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.lifespan.on',
        'ouffroad.api',
        'ouffroad.config',
        'ouffroad.core',
        'ouffroad.media',
        'ouffroad.repository',
        'ouffroad.services',
        'ouffroad.storage',
        'ouffroad.track',
        'PIL',
        'PIL.ExifTags',
        'PIL.Image',
        'multipart',
        'python_multipart',
        'fitparse',
        'gpxpy',
        'toml',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
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
    [],
    name='ouffroad',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
