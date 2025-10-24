# FileSync Build Instructions

This document provides comprehensive instructions for building FileSync executables and installers for different platforms.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Windows Build](#windows-build)
  - [Standalone Executable](#windows-standalone-executable)
  - [Installer](#windows-installer)
- [Linux Build](#linux-build)
  - [RPM Package](#rpm-package-red-hat-fedora-centos)
  - [DEB Package](#deb-package-debian-ubuntu)
  - [AppImage](#appimage-universal-linux)
- [macOS Build](#macos-build)
- [Cross-Platform Python Wheel](#cross-platform-python-wheel)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### All Platforms

- Python 3.11 or higher
- Git
- pip (Python package installer)

### Platform-Specific

**Windows:**
- [Python for Windows](https://www.python.org/downloads/windows/)
- [Inno Setup](https://jrsoftware.org/isinfo.php) (for creating installer)

**Linux (RPM):**
```bash
# Fedora/RHEL/CentOS
sudo dnf install python3-devel rpm-build git

# Install Python build dependencies
pip3 install build
```

**Linux (DEB):**
```bash
# Ubuntu/Debian
sudo apt install python3-dev python3-pip python3-venv dpkg-dev git

# Install Python build dependencies
pip3 install build stdeb
```

**macOS:**
```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python
brew install python@3.11
```

## Windows Build

### Windows Standalone Executable

Build standalone .exe files that don't require Python to be installed.

#### Automatic Build (Recommended)

1. **Run the build script:**
   ```cmd
   build_windows.bat
   ```

2. **Find your executables:**
   - GUI: `dist\FileSync-GUI\FileSync.exe`
   - CLI: `dist\filesync-cli\filesync.exe`

#### Manual Build

1. **Install PyInstaller:**
   ```cmd
   pip install pyinstaller
   ```

2. **Install dependencies:**
   ```cmd
   pip install customtkinter pillow cryptography click pystray watchdog plyer
   ```

3. **Build executables:**
   ```cmd
   pyinstaller filesync.spec
   ```

4. **Test the executables:**
   ```cmd
   dist\FileSync-GUI\FileSync.exe
   dist\filesync-cli\filesync.exe --help
   ```

### Windows Installer

Create a professional installer using Inno Setup.

#### Prerequisites

Download and install [Inno Setup](https://jrsoftware.org/isdl.php) (6.0 or later).

#### Build Steps

1. **Build executables first** (see above)

2. **Compile the installer:**
   - Open Inno Setup Compiler
   - File → Open → Select `build_installer.iss`
   - Build → Compile

   Or via command line:
   ```cmd
   "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" build_installer.iss
   ```

3. **Find your installer:**
   - Location: `installer\FileSync-0.1.0-Windows-Setup.exe`
   - Size: ~50-80 MB

4. **Test the installer:**
   - Run the installer
   - Install FileSync
   - Launch from Start Menu

#### Installer Features

- Installs both GUI and CLI applications
- Adds CLI to system PATH
- Creates Start Menu shortcuts
- Creates desktop shortcut (optional)
- Includes documentation
- Uninstaller included

## Linux Build

### RPM Package (Red Hat, Fedora, CentOS)

#### Automatic Build

```bash
./build_linux.sh rpm
```

#### Manual Build

1. **Install build tools:**
   ```bash
   sudo dnf install rpm-build python3-devel
   ```

2. **Create RPM build environment:**
   ```bash
   mkdir -p ~/rpmbuild/{BUILD,RPMS,SOURCES,SPECS,SRPMS}
   ```

3. **Create source tarball:**
   ```bash
   VERSION=$(python3 -c "import re; print(re.search(r'version=['\"]([^'\"]+)', open('setup.py').read()).group(1))")
   git archive --format=tar.gz --prefix=filesync-$VERSION/ HEAD > ~/rpmbuild/SOURCES/filesync-$VERSION.tar.gz
   ```

4. **Copy spec file:**
   ```bash
   cp filesync.rpm.spec ~/rpmbuild/SPECS/
   ```

5. **Build RPM:**
   ```bash
   rpmbuild -ba ~/rpmbuild/SPECS/filesync.rpm.spec
   ```

6. **Find your RPM:**
   ```bash
   ls ~/rpmbuild/RPMS/noarch/filesync-*.rpm
   ```

#### Install RPM

```bash
sudo dnf install ~/rpmbuild/RPMS/noarch/filesync-0.1.0-1.*.noarch.rpm
```

Or:

```bash
sudo rpm -ivh filesync-0.1.0-1.*.noarch.rpm
```

### DEB Package (Debian, Ubuntu)

#### Automatic Build

```bash
./build_linux.sh deb
```

#### Manual Build

1. **Install build tools:**
   ```bash
   sudo apt install python3-dev python3-pip dpkg-dev
   ```

2. **Install stdeb:**
   ```bash
   pip3 install --user stdeb
   ```

3. **Build DEB:**
   ```bash
   python3 setup.py --command-packages=stdeb.command bdist_deb
   ```

4. **Find your DEB:**
   ```bash
   ls deb_dist/python3-filesync_*.deb
   ```

#### Install DEB

```bash
sudo dpkg -i deb_dist/python3-filesync_0.1.0-1_all.deb
```

Or:

```bash
sudo apt install ./deb_dist/python3-filesync_0.1.0-1_all.deb
```

### AppImage (Universal Linux)

AppImages work on all Linux distributions without installation.

#### Build AppImage

```bash
./build_linux.sh appimage
```

#### Run AppImage

```bash
chmod +x dist/filesync-0.1.0-x86_64.AppImage
./dist/filesync-0.1.0-x86_64.AppImage
```

AppImages can be moved anywhere and run directly without installation.

## macOS Build

### App Bundle (Recommended)

1. **Install dependencies:**
   ```bash
   pip3 install py2app
   ```

2. **Create setup-mac.py:**
   ```python
   from setuptools import setup

   APP = ['src/filesync/gui/main.py']
   DATA_FILES = []
   OPTIONS = {
       'argv_emulation': True,
       'packages': ['filesync'],
       'iconfile': 'assets/filesync.icns',
   }

   setup(
       app=APP,
       data_files=DATA_FILES,
       options={'py2app': OPTIONS},
       setup_requires=['py2app'],
   )
   ```

3. **Build:**
   ```bash
   python3 setup-mac.py py2app
   ```

4. **Find your app:**
   - Location: `dist/FileSync.app`

5. **Create DMG (optional):**
   ```bash
   hdiutil create -volname "FileSync" -srcfolder dist/FileSync.app -ov -format UDZO FileSync-0.1.0.dmg
   ```

### Universal Binary (Intel + Apple Silicon)

```bash
python3 setup-mac.py py2app --arch=universal2
```

## Cross-Platform Python Wheel

Build a Python wheel that can be installed on any platform with pip.

### Build Wheel

```bash
# Install build tools
pip install build

# Build wheel
python -m build
```

### Find Your Wheel

```bash
ls dist/filesync-0.1.0-py3-none-any.whl
```

### Install Wheel

```bash
pip install dist/filesync-0.1.0-py3-none-any.whl
```

## Build Output Summary

After building, you should have:

### Windows
- `dist/FileSync-GUI/FileSync.exe` - Standalone GUI executable
- `dist/filesync-cli/filesync.exe` - Standalone CLI executable
- `installer/FileSync-0.1.0-Windows-Setup.exe` - Full installer

### Linux (RPM)
- `~/rpmbuild/RPMS/noarch/filesync-0.1.0-1.*.noarch.rpm` - RPM package

### Linux (DEB)
- `deb_dist/python3-filesync_0.1.0-1_all.deb` - DEB package

### Linux (AppImage)
- `dist/filesync-0.1.0-x86_64.AppImage` - Universal Linux executable

### macOS
- `dist/FileSync.app` - macOS application bundle
- `FileSync-0.1.0.dmg` - macOS disk image (optional)

### Python Wheel
- `dist/filesync-0.1.0-py3-none-any.whl` - Python wheel

## Troubleshooting

### Windows

**Issue: "Python not found in PATH"**
```cmd
# Add Python to PATH or use full path
C:\Python311\python.exe --version
```

**Issue: "ModuleNotFoundError"**
```cmd
# Install missing dependencies
pip install -r requirements.txt
```

**Issue: Antivirus blocking PyInstaller**
- Add exclusion for Python and dist/ directory
- Or temporarily disable antivirus during build

### Linux

**Issue: "rpmbuild: command not found"**
```bash
sudo dnf install rpm-build  # Fedora/RHEL
```

**Issue: "dpkg-deb: command not found"**
```bash
sudo apt install dpkg-dev  # Ubuntu/Debian
```

**Issue: Permission denied on build_linux.sh**
```bash
chmod +x build_linux.sh
```

### macOS

**Issue: "py2app not found"**
```bash
pip3 install py2app
```

**Issue: Code signing required**
```bash
# For distribution, you need an Apple Developer account
# For personal use, right-click app → Open
```

### General

**Issue: Build fails with import errors**
```bash
# Ensure all dependencies are installed
pip install -e ".[full]"
```

**Issue: Large executable size**
- This is normal for PyInstaller (bundles Python + libraries)
- GUI exe: ~60-80 MB
- CLI exe: ~40-50 MB
- Use UPX compression (enabled in spec file)

**Issue: Slow startup time**
- First run extracts files (one-time delay)
- Subsequent runs are faster
- Consider using Python wheel for better startup

## Distribution

### Windows
- Upload installer to GitHub Releases
- Users run `FileSync-0.1.0-Windows-Setup.exe`

### Linux (RPM)
- Add to repository or GitHub Releases
- Users: `sudo dnf install filesync-0.1.0-1.*.rpm`

### Linux (DEB)
- Add to repository or GitHub Releases
- Users: `sudo apt install ./filesync_0.1.0_all.deb`

### Linux (AppImage)
- Upload to GitHub Releases
- Users: `chmod +x` and run directly

### macOS
- Upload DMG to GitHub Releases
- Users: Mount DMG and drag to Applications

### Python Wheel
- Upload to PyPI: `twine upload dist/*.whl`
- Users: `pip install filesync`

## Continuous Integration

### GitHub Actions Example

```yaml
name: Build

on: [push, pull_request]

jobs:
  build-windows:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: build_windows.bat
      - uses: actions/upload-artifact@v3
        with:
          name: windows-exe
          path: dist/

  build-linux:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: ./build_linux.sh deb
      - uses: actions/upload-artifact@v3
        with:
          name: linux-deb
          path: deb_dist/
```

## Support

For build issues:
- Check [GitHub Issues](https://github.com/IamSteveV/file-sync/issues)
- Review [Troubleshooting](#troubleshooting) section
- Ensure all prerequisites are installed

---

**Happy Building!** 🚀
