Name:           filesync
Version:        0.1.0
Release:        1%{?dist}
Summary:        Cloud Storage Deduplication System with Importance-Based Tiering

License:        MIT
URL:            https://github.com/IamSteveV/file-sync
Source0:        %{name}-%{version}.tar.gz

BuildArch:      noarch
BuildRequires:  python3-devel
BuildRequires:  python3-setuptools
BuildRequires:  python3-pip

Requires:       python3 >= 3.11
Requires:       python3-cryptography >= 41.0.0
Requires:       python3-click >= 8.1.0
Requires:       python3-pillow >= 10.0.0
Requires:       python3-customtkinter >= 5.2.0
Requires:       python3-tkinter

%description
FileSync is a cross-platform file synchronization and deduplication system
that intelligently manages your files across multiple cloud storage providers
with importance-based tiering, client-side encryption, and automated redundancy
management.

Features:
- Content-based deduplication with SHA-256 hashing
- Multi-provider sync (Google Drive, OneDrive, Box, Proton Drive, Local)
- 4-tier importance system (Critical, Important, Standard, Archive)
- Client-side AES-256-GCM encryption
- 3-2-1 backup strategy enforcement
- Modern GUI with CustomTkinter
- Advanced features: file watching, notifications, conflict resolution,
  advanced search, file preview, backup scheduler, quota monitoring

%prep
%setup -q

%build
%py3_build

%install
%py3_install

# Create config directory
mkdir -p %{buildroot}%{_sysconfdir}/%{name}

# Create documentation directory
mkdir -p %{buildroot}%{_docdir}/%{name}
install -m 644 README.md %{buildroot}%{_docdir}/%{name}/
install -m 644 ARCHITECTURE.md %{buildroot}%{_docdir}/%{name}/
install -m 644 ARCHITECTURE_DIAGRAM.md %{buildroot}%{_docdir}/%{name}/
install -m 644 LICENSE %{buildroot}%{_docdir}/%{name}/

# Create desktop entry for GUI
mkdir -p %{buildroot}%{_datadir}/applications
cat > %{buildroot}%{_datadir}/applications/%{name}.desktop << EOF
[Desktop Entry]
Type=Application
Name=FileSync
Comment=Cloud Storage Deduplication System
Exec=filesync-gui
Icon=filesync
Terminal=false
Categories=Utility;FileTools;Archiving;
Keywords=backup;cloud;sync;deduplication;encryption;
EOF

# Create man pages directory
mkdir -p %{buildroot}%{_mandir}/man1

%files
%license LICENSE
%doc README.md ARCHITECTURE.md ARCHITECTURE_DIAGRAM.md

# Python package files
%{python3_sitelib}/%{name}/
%{python3_sitelib}/%{name}-%{version}-py%{python3_version}.egg-info/

# Executables
%{_bindir}/filesync
%{_bindir}/filesync-gui

# Desktop entry
%{_datadir}/applications/%{name}.desktop

# Config directory
%dir %{_sysconfdir}/%{name}

%changelog
* Fri Oct 23 2024 FileSync Team <noreply@filesync.com> - 0.1.0-1
- Initial RPM release
- Core deduplication engine with SHA-256
- 4-tier importance system
- Client-side AES-256-GCM encryption
- Modern GUI with CustomTkinter
- Complete CLI with Click
- Advanced search with multiple filter types
- File preview (text, images, PDFs)
- Conflict resolution UI
- Backup scheduler
- Cloud quota monitoring
- File system watching and auto-import
- Desktop notifications
- OAuth2 authentication framework
- System tray integration
- Keyboard shortcuts
- Drag-and-drop file addition
