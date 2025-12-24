# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['src\\app.py'],
    pathex=[],
    binaries=[],
    datas=[('D:/work/Self_Made_Program/jisuanqi/.venv/Lib/site-packages/PySide6/translations', 'translations'), ('src\\resources', 'resources')],
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
    icon=['d:\\work\\Self_Made_Program\\jisuanqi\\计算器.ico'],
)
