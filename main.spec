# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('assets/images', 'assets/images')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['pyinstaller', 'pyinstaller-hooks-contrib', 'setuptools', 'packaging'],
    noarchive=False,
    optimize=2,  # Optimierung aktiviert
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='tc_guidl',  # Name der Anwendung geändert
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # --windowed aktiviert
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    onefile=True,
    icon='assets/images/icon.ico',  # Icon hinzugefügt
    distpath='dist'  # Ausgabeordner explizit auf ./dist gesetzt
)
