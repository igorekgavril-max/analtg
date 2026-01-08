# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main-work.py'],
    pathex=[],
    binaries=[],
    datas=[('idandhash.env', '.')],
    hiddenimports=[
        'telethon',
        'telethon.tl.types',
        'nicegui',
        'pandas',
        'matplotlib',
        'matplotlib.pyplot',
        'dotenv',
        'asyncio',
        'datetime',
        'tempfile',
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
    name='TGBotStat',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

