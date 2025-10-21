# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('email_checker', 'email_checker'),
        ('requirements.txt', '.')
    ],
    hiddenimports=[
        'bs4',
        'urllib3',
        'concurrent.futures',
        'queue',
        'urllib.parse',
        'threading',
        'email_checker.mass_scanner',
        'email_checker.interface'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter', 
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
    [],
    exclude_binaries=True,
    name='EmailFinder',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # Важно: отключаем UPX из-за проблем с памятью
    console=False,  # False для GUI приложения
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)