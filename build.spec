# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('email_checker', 'email_checker'),
    ],
    hiddenimports=[
        'bs4',
        'urllib3', 
        'concurrent.futures',
        'queue',
        'urllib.parse',
        'threading',
        'email_checker.mass_scanner',
        'email_checker.interface',
        'bs4.builder._htmlparser',
        'urllib3.packages.six.moves'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Убрали tkinter из исключений - он нужен для GUI
        'matplotlib', 
        'pytest', 
        'notebook',
        'scipy', 
        'pandas', 
        'numpy', 
        'test', 
        'unittest',
        'setuptools',
        'pip',
        'wheel'
    ],
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
    name='EmailFinder',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)