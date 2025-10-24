#!/bin/bash
# Build script for FileSync Linux packages (RPM and DEB)

set -e

echo "========================================"
echo "FileSync Linux Build Script"
echo "========================================"
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check for required tools
check_tool() {
    if ! command -v $1 &> /dev/null; then
        echo -e "${RED}ERROR: $1 not found${NC}"
        echo "Install with: sudo $2"
        return 1
    fi
    return 0
}

# Detect distribution
if [ -f /etc/redhat-release ]; then
    DISTRO="redhat"
    PKG_MANAGER="dnf"
elif [ -f /etc/debian_version ]; then
    DISTRO="debian"
    PKG_MANAGER="apt"
else
    echo -e "${YELLOW}Warning: Unknown distribution, defaulting to generic build${NC}"
    DISTRO="generic"
fi

echo "Detected distribution: $DISTRO"
echo

# Get version from setup.py
VERSION=$(python3 -c "import re; content=open('setup.py').read(); print(re.search(r'version=['\"]([^'\"]+)', content).group(1))")
echo "Building FileSync version: $VERSION"
echo

# Build Python wheel
echo "Building Python wheel..."
python3 -m pip install --upgrade build
python3 -m build

if [ $? -ne 0 ]; then
    echo -e "${RED}ERROR: Wheel build failed${NC}"
    exit 1
fi

echo -e "${GREEN}Wheel built successfully${NC}"
echo

# Build RPM (for Red Hat-based distros)
if [ "$DISTRO" = "redhat" ] || [ "$1" = "rpm" ]; then
    echo "Building RPM package..."

    # Check for rpmbuild
    if ! check_tool rpmbuild "dnf install rpm-build"; then
        echo -e "${YELLOW}Skipping RPM build${NC}"
    else
        # Create RPM build environment
        mkdir -p ~/rpmbuild/{BUILD,RPMS,SOURCES,SPECS,SRPMS}

        # Create source tarball
        git archive --format=tar.gz --prefix=filesync-$VERSION/ HEAD > ~/rpmbuild/SOURCES/filesync-$VERSION.tar.gz

        # Copy spec file
        cp filesync.rpm.spec ~/rpmbuild/SPECS/

        # Build RPM
        rpmbuild -ba ~/rpmbuild/SPECS/filesync.rpm.spec

        if [ $? -eq 0 ]; then
            echo -e "${GREEN}RPM package built successfully${NC}"
            echo "RPM location: ~/rpmbuild/RPMS/noarch/filesync-$VERSION-1.*.noarch.rpm"

            # Copy to dist directory
            mkdir -p dist
            cp ~/rpmbuild/RPMS/noarch/filesync-$VERSION-*.noarch.rpm dist/
        else
            echo -e "${RED}ERROR: RPM build failed${NC}"
        fi
    fi
    echo
fi

# Build DEB (for Debian-based distros)
if [ "$DISTRO" = "debian" ] || [ "$1" = "deb" ]; then
    echo "Building DEB package..."

    # Check for dpkg-deb
    if ! check_tool dpkg-deb "apt install dpkg-dev"; then
        echo -e "${YELLOW}Skipping DEB build${NC}"
    else
        # Install python-stdeb if not present
        pip3 install --user stdeb

        # Build DEB
        python3 setup.py --command-packages=stdeb.command bdist_deb

        if [ $? -eq 0 ]; then
            echo -e "${GREEN}DEB package built successfully${NC}"
            echo "DEB location: deb_dist/python3-filesync_${VERSION}-1_all.deb"

            # Copy to dist directory
            mkdir -p dist
            cp deb_dist/python3-filesync_${VERSION}-1_all.deb dist/filesync_${VERSION}_all.deb
        else
            echo -e "${RED}ERROR: DEB build failed${NC}"
        fi
    fi
    echo
fi

# Build AppImage (universal Linux)
if [ "$1" = "appimage" ]; then
    echo "Building AppImage..."

    if ! check_tool appimagetool "# Download from https://appimage.github.io/"; then
        echo -e "${YELLOW}Skipping AppImage build${NC}"
    else
        # Create AppDir structure
        APPDIR="FileSync.AppDir"
        rm -rf $APPDIR
        mkdir -p $APPDIR/usr/{bin,lib,share/applications}

        # Install FileSync into AppDir
        pip3 install --target=$APPDIR/usr/lib .

        # Create wrapper script
        cat > $APPDIR/usr/bin/filesync-gui << 'EOF'
#!/bin/bash
APPDIR=$(dirname $(dirname $(readlink -f $0)))
export PYTHONPATH="$APPDIR/usr/lib:$PYTHONPATH"
python3 -m filesync.gui.main "$@"
EOF
        chmod +x $APPDIR/usr/bin/filesync-gui

        # Create desktop file
        cp filesync.desktop $APPDIR/filesync.desktop

        # Create AppRun
        ln -s usr/bin/filesync-gui $APPDIR/AppRun

        # Build AppImage
        appimagetool $APPDIR filesync-$VERSION-x86_64.AppImage

        if [ $? -eq 0 ]; then
            echo -e "${GREEN}AppImage built successfully${NC}"
            echo "AppImage location: filesync-$VERSION-x86_64.AppImage"
            mv filesync-$VERSION-x86_64.AppImage dist/
        else
            echo -e "${RED}ERROR: AppImage build failed${NC}"
        fi
    fi
    echo
fi

echo "========================================"
echo "Build Summary"
echo "========================================"
echo
ls -lh dist/ 2>/dev/null || echo "No packages built"
echo
echo -e "${GREEN}Build complete!${NC}"
echo
echo "Install instructions:"
echo "  RPM: sudo dnf install dist/filesync-*.rpm"
echo "  DEB: sudo dpkg -i dist/filesync_*.deb"
echo "  AppImage: chmod +x dist/filesync-*.AppImage && ./dist/filesync-*.AppImage"
echo
