# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

ROOT = Path(globals().get("SPECPATH", Path.cwd())).resolve()
PYSIDE_TRANSLATIONS = ROOT / ".venv" / "Lib" / "site-packages" / "PySide6" / "translations"
datas = []
if PYSIDE_TRANSLATIONS.exists():
    datas.append((str(PYSIDE_TRANSLATIONS), "translations"))
datas.extend([
    (str(ROOT / "src" / "resources"), "resources"),
    (str(ROOT / "img"), "img"),
])

a = Analysis(
    ['src\\app.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='thief_counter',
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
    icon=[str(ROOT / "计算器.ico")],
)
