# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for FileSync Windows executable.

To build:
    pip install pyinstaller
    pyinstaller filesync.spec
"""

import os

block_cipher = None

# Collect all GUI resources
gui_datas = []

# Hidden imports needed by the application
hidden_imports = [
    'PIL._tkinter_finder',
    'customtkinter',
    'tkinter',
    'cryptography.hazmat.backends.openssl',
    'cryptography.hazmat.bindings._rust',
    'sqlite3',
    'click',
    'pathlib',
    'json',
    'hashlib',
    'threading',
    'queue',
    'datetime',
    # Optional cloud provider imports
    'google.oauth2.credentials',
    'googleapiclient.discovery',
    'msal',
    'boxsdk',
    'requests',
    # Optional feature imports
    'watchdog',
    'watchdog.observers',
    'watchdog.events',
    'plyer',
    'plyer.platforms.win.notification',
    'pystray',
    'pystray._win32',
    'PIL.Image',
    'PIL.ImageTk',
]

# Analysis for GUI application
gui_analysis = Analysis(
    ['src/filesync/gui/main.py'],
    pathex=[],
    binaries=[],
    datas=gui_datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'numpy', 'scipy', 'pandas'],  # Exclude heavy unused libs
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Analysis for CLI application
cli_analysis = Analysis(
    ['src/filesync/cli/main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'click',
        'cryptography.hazmat.backends.openssl',
        'sqlite3',
        'pathlib',
        'json',
        'hashlib',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'numpy', 'scipy', 'pandas', 'tkinter', 'customtkinter'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# PYZ archives
gui_pyz = PYZ(gui_analysis.pure, gui_analysis.zipped_data, cipher=block_cipher)
cli_pyz = PYZ(cli_analysis.pure, cli_analysis.zipped_data, cipher=block_cipher)

# GUI Executable
gui_exe = EXE(
    gui_pyz,
    gui_analysis.scripts,
    [],
    exclude_binaries=True,
    name='FileSync',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # GUI app - no console window
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/filesync.ico' if os.path.exists('assets/filesync.ico') else None,
)

# CLI Executable
cli_exe = EXE(
    cli_pyz,
    cli_analysis.scripts,
    [],
    exclude_binaries=True,
    name='filesync',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # CLI app - show console
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# Collect all binaries and dependencies
gui_coll = COLLECT(
    gui_exe,
    gui_analysis.binaries,
    gui_analysis.zipfiles,
    gui_analysis.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='FileSync-GUI',
)

cli_coll = COLLECT(
    cli_exe,
    cli_analysis.binaries,
    cli_analysis.zipfiles,
    cli_analysis.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='filesync-cli',
)

# Create installer-friendly single directory
# This can be packaged with Inno Setup or NSIS
