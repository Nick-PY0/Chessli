# -*- mode: python ; coding: utf-8 -*-

import os

block_cipher = None

manifest_path = os.path.join(os.getcwd(), 'manifest.xml')  
icon_path = os.path.join(os.getcwd(), 'Chessli.ico')       

a = Analysis(
    ['Chessli.py'],
    pathex=['.'],
    binaries=[
        ('engines/lc0-v0.30.0-windows-cpu-openblas/lc0.exe', 'engines/lc0-v0.30.0-windows-cpu-openblas'),
        ('engines/lc0-v0.30.0-windows-cpu-openblas/mimalloc-override.dll', 'engines/lc0-v0.30.0-windows-cpu-openblas'),
        ('engines/lc0-v0.30.0-windows-cpu-openblas/mimalloc-redirect.dll', 'engines/lc0-v0.30.0-windows-cpu-openblas'),
        ('engines/lc0-v0.30.0-windows-cpu-openblas/t1-256x10-distilled-swa-2432500.pb.gz', 'engines/lc0-v0.30.0-windows-cpu-openblas'),
        ('engines/stockfish/stockfish-windows-x86-64-avx2.exe', 'engines/stockfish'),
        ('engines/komodo-14/Windows/komodo-14.1-64bit.exe', 'engines/komodo-14/Windows')
    ],
    datas=[
        ('images', 'images'),
        ('pgn', 'pgn')
    ],
    hiddenimports=[],
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
    [],
    exclude_binaries=True,
    name='Chessli',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    manifest=manifest_path,  
    icon=icon_path           
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Chessli'
)
