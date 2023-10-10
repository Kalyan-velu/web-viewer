# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['task_manager.py'],
    pathex=[],
    binaries=[],
    datas=[('E:\\AtoZDebug\\visitor\\env\\Lib\\site-packages\\fake_useragent\\data\\browsers.json',
            'fake_useragent\\data'),
            ('E:\\AtoZDebug\\visitor\\env\\Lib\\site-packages\\playwright\\driver\\package\\.local-browsers\\chromium-1080',
            '.playwright\\.local-browsers\\chromium-1080'),
            ('E:\\AtoZDebug\\visitor\\env\\Lib\\site-packages\\playwright\\driver\\package\\.local-browsers\\firefox-1424',
            '.playwright\\.local-browsers\\firefox-1424')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='visitor',
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