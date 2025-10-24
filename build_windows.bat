@echo off
REM Build script for FileSync Windows executable
REM Requires: Python 3.11+, PyInstaller

echo ========================================
echo FileSync Windows Build Script
echo ========================================
echo.

REM Check Python version
python --version
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python not found in PATH
    exit /b 1
)

REM Install build dependencies
echo Installing build dependencies...
pip install pyinstaller pillow customtkinter cryptography click pystray watchdog plyer

REM Clean previous builds
echo Cleaning previous builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM Build executables
echo Building FileSync executables...
pyinstaller filesync.spec

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Build failed
    exit /b 1
)

echo.
echo ========================================
echo Build Complete!
echo ========================================
echo.
echo Executables created in dist/:
echo   - dist/FileSync-GUI/FileSync.exe  (GUI application)
echo   - dist/filesync-cli/filesync.exe  (CLI application)
echo.
echo To create installer, use Inno Setup with build_installer.iss
echo.

pause
