# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for anki-mini

block_cipher = None

a = Analysis(
    ['anki_mini/__main__.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'anki_mini.cli',
        'anki_mini.shell',
        'anki_mini.deck',
        'anki_mini.cards',
        'anki_mini.scheduler',
        'anki_mini.review',
        'anki_mini.stats',
        'anki_mini.config',
        'anki_mini.init',
        'anki_mini.utils',
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
    name='anki-mini',
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
    icon=None,
)
