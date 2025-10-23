# FileSync

> **Cloud Storage Deduplication System with Importance-Based Tiering**

FileSync is a cross-platform file synchronization and deduplication system that intelligently manages your files across multiple cloud storage providers with importance-based tiering, client-side encryption, and automated redundancy management.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🌟 Features

### Core Functionality
- **Content-Based Deduplication**: SHA-256 hashing ensures you never store the same file twice
- **Multi-Provider Sync**: Seamlessly sync across Google Drive, OneDrive, Box, Proton Drive, and local storage
- **Importance-Based Tiering**: 4-tier system (Critical, Important, Standard, Archive) with automatic redundancy
- **Client-Side Encryption**: AES-256-GCM encryption for sensitive files with zero-trust architecture
- **3-2-1 Backup Strategy**: Automated enforcement of backup best practices
- **Single Source of Truth**: SQLite-based manifest tracks all file metadata and locations

### Advanced GUI Features
- **Modern Interface**: Dark-themed GUI built with CustomTkinter
- **File System Watching**: Automatically import files from monitored folders
- **Desktop Notifications**: Real-time cross-platform notifications for important events
- **Conflict Resolution**: Visual interface for handling file version conflicts
- **Advanced Search**: Complex queries with filters for date, size, tags, providers, encryption status
- **File Preview**: Built-in preview for text files, images, and PDFs
- **Backup Scheduler**: Automated validation, verification, and lifecycle management tasks
- **Cloud Quota Monitoring**: Real-time tracking of storage usage across all providers with alerts
- **OAuth2 Integration**: Secure browser-based authentication for cloud providers
- **Drag & Drop**: Intuitive file addition with drag-and-drop support
- **System Tray Integration**: Background operation with quick access menu
- **Keyboard Shortcuts**: Efficient navigation (Ctrl+1-5, Ctrl+N, Ctrl+F, F1, etc.)

### Security & Reliability
- **Zero-Trust Encryption**: Files encrypted before upload, providers never see unencrypted data
- **Automated Validation**: Continuous monitoring of redundancy requirements
- **Integrity Verification**: Hash-based file integrity checks across all copies
- **Lifecycle Policies**: Automatic tier promotion/demotion based on customizable rules
- **Multi-Copy Redundancy**: Configurable redundancy per importance tier

## 📋 Table of Contents

- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [Usage](#-usage)
  - [GUI Application](#gui-application)
  - [Command Line Interface](#command-line-interface)
- [Tier System](#-tier-system)
- [Advanced Features](#-advanced-features)
- [Configuration](#-configuration)
- [Architecture](#-architecture)
- [Requirements](#-requirements)
- [Development](#-development)
- [Contributing](#-contributing)
- [License](#-license)

## 🚀 Installation

### Prerequisites

- Python 3.11 or higher
- pip package manager

### Install from Source

```bash
# Clone the repository
git clone https://github.com/IamSteveV/file-sync.git
cd file-sync

# Install dependencies
pip install -r requirements.txt

# Install the package
pip install -e .
```

### Install with Optional Features

```bash
# Full installation with all features
pip install -e ".[full]"

# GUI only
pip install -e ".[gui]"

# Specific cloud providers
pip install -e ".[gdrive,onedrive,box]"

# Development tools
pip install -e ".[dev]"
```

## ⚡ Quick Start

### Initialize FileSync

```bash
# Using CLI
filesync init

# Using GUI
filesync-gui
```

This creates:
- Manifest database at `~/.filesync/filesync.db`
- Configuration files in `~/.filesync/`
- Local offline storage at `~/filesync-offline/`

### Add Your First File

```bash
# CLI: Add a file with Critical tier
filesync add myfile.txt --tier 0 --encrypt --tags important,work

# GUI: Use the drag-and-drop interface or "Add File" button
```

### View Your Files

```bash
# CLI: List all files
filesync list

# List files by tier
filesync list --tier 0

# GUI: Navigate to the Files view for visual browsing
```

## 📖 Usage

### GUI Application

Launch the graphical interface:

```bash
filesync-gui
```

#### Main Views

**Dashboard**
- Statistics overview: total files, storage used, encrypted files
- Tier distribution pie chart
- Provider distribution visualization
- Storage quota monitoring widget
- Quick access to common actions

**Files Management**
- Browse all managed files in sortable table view
- Search with simple text or advanced filters
- Drag and drop files to add them instantly
- Preview files (text, images, PDFs) without downloading
- View detailed file information and locations
- Delete or download files with context menu

**Provider Configuration**
- Configure cloud storage providers
- OAuth2 authentication wizard for Google Drive, OneDrive, Box
- View connection status and credentials
- Test provider connections

**Validation**
- Run redundancy checks across all files
- View compliance status with color-coded indicators
- See non-compliant files with specific issues
- Quick-fix buttons for common problems
- Generate validation reports

**Settings**
- Initialize or re-initialize FileSync
- Export/import manifest database
- Configure auto-import from folders
  - Add watched folders with tier assignment
  - Enable recursive watching
  - View and manage active watches
- Desktop notifications
  - Enable/disable notifications
  - Test notification delivery
- View system paths and configuration
- Manage encryption settings

#### Advanced Features in GUI

**Advanced Search** (🔍 Advanced button)
- Text search with filename patterns and wildcard support
- Tag filtering with AND/OR logic
- Date range filters (created/modified) with quick presets
- File size ranges with unit conversion (B/KB/MB/GB)
- Multi-select tier filtering
- Provider location filtering
- Encryption status filtering
- Save and apply complex search criteria

**File Preview**
- Automatic preview for supported file types
- Text files: syntax highlighting, line numbers
- Images: auto-scaling, original size display
- PDFs: page count, metadata (requires PyPDF2)
- Open in system default application
- Quick preview panel for side-by-side viewing

**Conflict Resolution**
- Visual comparison of conflicting versions
- See metadata: size, modified date, hash, provider
- Multiple resolution strategies:
  - Keep selected version (delete others)
  - Keep all versions (rename files)
  - Manual merge (download both for comparison)
- Preview different versions before choosing
- Batch conflict resolution

**Backup Scheduler**
- Create scheduled tasks for:
  - Validation (check redundancy)
  - Verification (hash integrity checks)
  - Lifecycle (apply promotion/demotion policies)
  - Sync (synchronize files)
  - Backup (full backup operations)
- Schedule frequencies:
  - Hourly (specify minute)
  - Daily (specify time)
  - Weekly (specify day and time)
  - Monthly (specify day of month and time)
  - Custom (specify interval in hours)
- Enable/disable tasks without deleting
- View next run times and last execution
- Edit existing schedules

**Cloud Quota Monitoring**
- Real-time quota display for all providers
- Visual progress bars with usage percentage
- Warning alerts (>80% used) in orange
- Critical alerts (>95% used) in red
- Total storage summary across all providers
- Last updated timestamp
- Refresh on demand
- Compact widget for dashboard integration

**File System Watching**
- Monitor folders for new files
- Automatically import when files are created
- Assign tier to auto-imported files
- Recursive folder watching
- Filter out temporary files automatically
- Pause/resume watching per folder
- Configuration persistence

**Desktop Notifications**
- Success notifications (file added, sync complete)
- Warning notifications (approaching quota, redundancy issues)
- Error notifications (sync failures, validation errors)
- Info notifications (task scheduled, backup complete)
- Cross-platform support (Windows, macOS, Linux)
- Customizable (enable/disable per type)

**Keyboard Shortcuts**
- `Ctrl+1` - Dashboard view
- `Ctrl+2` - Files view
- `Ctrl+3` - Providers view
- `Ctrl+4` - Validation view
- `Ctrl+5` - Settings view
- `Ctrl+N` - Add new file
- `Ctrl+R` - Refresh current view
- `Ctrl+F` - Focus search
- `Ctrl+S` - Sync all files
- `F1` - Show help
- `F5` - Refresh
- `Esc` - Close dialogs

**System Tray**
- Minimize to tray for background operation
- Quick access menu:
  - Show/Hide main window
  - Quick sync
  - Run validation
  - View notifications
  - Exit application
- Visual notifications in tray
- Background auto-sync daemon

### Command Line Interface

#### Initialize

```bash
filesync init
```

#### Add Files

```bash
# Add a single file
filesync add /path/to/file.txt --tier 1 --tags work,project

# Add with encryption (required for tier 0)
filesync add /path/to/sensitive.doc --tier 0 --encrypt --tags confidential

# Add with custom reason
filesync add contract.pdf --tier 0 --encrypt --reason "Employment contract"
```

#### List Files

```bash
# List all files
filesync list

# List files by tier
filesync list --tier 0

# List files with specific tag
filesync list --tag important

# List encrypted files only
filesync list --encrypted
```

#### Check Status

```bash
# View system status
filesync status

# Detailed status with file counts
filesync status --verbose
```

#### Validate Redundancy

```bash
# Run validation
filesync validate

# Validate and show detailed report
filesync validate --verbose

# Validate specific tier only
filesync validate --tier 0
```

#### Manage Tiers

```bash
# List tier configurations
filesync tiers

# Show details for a specific tier
filesync tiers --tier 0
```

#### Lifecycle Management

```bash
# Apply lifecycle policies
filesync apply-policies

# Dry run (see what would change without applying)
filesync apply-policies --dry-run

# Apply to specific tier only
filesync apply-policies --tier 2
```

## 🎯 Tier System

FileSync uses a 4-tier importance system to automatically manage redundancy:

### Tier 0: Critical
**Use case**: Irreplaceable files, legal documents, critical data, passports, contracts

**Requirements**:
- Minimum 3 copies
- Minimum 2 cloud providers
- Offline backup REQUIRED
- Encryption REQUIRED
- Proton Drive REQUIRED (zero-trust)
- Verified weekly

**Example**: `[Local] + [Proton] + [Google Drive]` (all encrypted)

```bash
filesync add passport.pdf --tier 0 --encrypt --tags "legal,personal"
```

### Tier 1: Important
**Use case**: Important work files, projects, valuable data, edited photos

**Requirements**:
- Minimum 2 copies
- Minimum 2 providers
- Encryption optional (recommended for sensitive data)
- Verified bi-weekly

**Example**: `[Google Drive] + [OneDrive]`

```bash
filesync add project.zip --tier 1 --tags "work,project"
```

### Tier 2: Standard
**Use case**: Regular files, everyday documents, reference materials

**Requirements**:
- Minimum 2 copies
- Minimum 1 provider
- Verified monthly

**Example**: `[Google Drive] + [Local]`

```bash
filesync add document.pdf --tier 2 --tags "reference"
```

### Tier 3: Archive
**Use case**: Low-priority files, rarely accessed data, large media files

**Requirements**:
- Minimum 1 copy
- Minimum 1 provider
- Verified on-demand

**Example**: `[Box]` (single copy, cost-optimized)

```bash
filesync add old-backup.zip --tier 3 --tags "archive"
```

## 🎨 Advanced Features

### Auto-Import from Folders

Configure folders to automatically import new files:

1. Open Settings → Auto-Import
2. Click "Add Folder"
3. Select folder to watch
4. Choose default tier for imported files
5. Enable recursive watching if needed
6. Files added to folder are automatically imported

### Scheduled Backups

Automate maintenance tasks:

1. Open Backup Scheduler dialog
2. Click "Add Task"
3. Select task type (Validation, Verification, Lifecycle, etc.)
4. Choose frequency (Hourly, Daily, Weekly, Monthly, Custom)
5. Set time and enable the task
6. View next run times in the scheduler

### Quota Alerts

Monitor storage usage:

1. Quotas update automatically when providers are accessed
2. Click "Refresh" to update immediately
3. Warning shown when >80% used (orange)
4. Critical alert when >95% used (red)
5. View detailed quota breakdown per provider

### Conflict Resolution

When file conflicts are detected:

1. Open conflict resolution dialog
2. Compare versions side-by-side
3. View metadata (size, date, hash, provider)
4. Preview each version if supported
5. Choose resolution strategy
6. Apply resolution to resolve conflict

## ⚙️ Configuration

### Provider Setup

FileSync supports multiple cloud storage providers:

#### Local Storage (Offline Backup)
Automatically configured during initialization at `~/filesync-offline/`

#### Google Drive
1. Create OAuth2 credentials in [Google Cloud Console](https://console.cloud.google.com)
2. Enable Google Drive API
3. Create OAuth 2.0 client ID (Desktop application)
4. Download credentials JSON
5. In GUI: Providers → Google Drive → Configure
6. Upload credentials and complete OAuth2 flow in browser

#### Microsoft OneDrive
1. Register app in [Azure Portal](https://portal.azure.com)
2. Get Application (client) ID and client secret
3. Add redirect URI: `http://localhost:8080/callback`
4. Grant Files.ReadWrite permission
5. In GUI: Providers → OneDrive → Configure
6. Enter credentials and authenticate

#### Box
1. Create Box app at [developer.box.com](https://developer.box.com)
2. Configure OAuth2 credentials
3. Set redirect URI: `http://localhost:8080/callback`
4. In GUI: Providers → Box → Configure
5. Complete OAuth2 authorization

#### Proton Drive
1. Get Proton Drive API credentials (when available)
2. Configure in GUI or config file
3. Required for Tier 0 (Critical) files

### Configuration Files

FileSync stores configuration in `~/.filesync/`:

```
~/.filesync/
├── filesync.db                 # Manifest database (SQLite)
├── config.json                 # General configuration
├── providers.json              # Provider credentials (encrypted)
├── auto_import_config.json     # Folder watch settings
├── scheduler_config.json       # Backup scheduler settings
├── quota_cache.json           # Cached quota information
└── cache/                     # Temporary cache files
```

### Environment Variables

```bash
# Set custom manifest location
export FILESYNC_MANIFEST=/path/to/manifest.db

# Set custom offline storage
export FILESYNC_OFFLINE=/path/to/offline/storage

# Set custom config directory
export FILESYNC_CONFIG=/path/to/config
```

## 🏗️ Architecture

FileSync uses a modular, layered architecture. For complete details, see:
- [ARCHITECTURE.md](ARCHITECTURE.md) - Design philosophy and concepts
- [ARCHITECTURE_DIAGRAM.md](ARCHITECTURE_DIAGRAM.md) - Visual diagrams and data flows

### High-Level Overview

```
┌─────────────────────────────────────────┐
│      User Interfaces (GUI/CLI)          │
└────────────┬────────────────────────────┘
             │
┌────────────▼────────────────────────────┐
│       Core Business Logic               │
│  • Sync Engine (orchestration)          │
│  • Deduplication (SHA-256)              │
│  • Encryption (AES-256-GCM)             │
│  • Redundancy Validator                 │
│  • Lifecycle Manager                    │
└────────────┬────────────────────────────┘
             │
┌────────────▼────────────────────────────┐
│      Data & Storage Layer               │
│  • Manifest Manager (SQLite)            │
│  • Provider Abstraction Layer           │
└────────────┬────────────────────────────┘
             │
┌────────────▼────────────────────────────┐
│    Cloud Storage Providers              │
│  Local • GDrive • OneDrive • Box        │
│  Proton                                 │
└─────────────────────────────────────────┘
```

### Supporting Subsystems

- **Authentication**: OAuth2Manager for cloud provider authentication
- **Encryption**: AES-256-GCM with PBKDF2 key derivation (100,000 iterations)
- **File Watcher**: watchdog-based folder monitoring
- **Notifications**: plyer for cross-platform desktop notifications
- **Scheduler**: Background task scheduler with cron-like capabilities
- **Quota Monitor**: Real-time storage usage tracking

## 📦 Requirements

### Core Dependencies

```
cryptography>=41.0.0      # AES-256-GCM encryption
click>=8.1.0              # CLI framework
customtkinter>=5.2.0      # Modern GUI framework
Pillow>=10.0.0            # Image handling
```

### Cloud Provider SDKs

```
google-api-python-client>=2.100.0    # Google Drive
msal>=1.24.0                         # Microsoft OneDrive
boxsdk>=3.9.0                        # Box
requests>=2.31.0                     # HTTP client
```

### Optional Features

```
pystray>=0.19.0          # System tray integration
watchdog>=3.0.0          # File system monitoring
plyer>=2.1.0             # Desktop notifications
PyPDF2>=3.0.0            # PDF preview support
```

See [requirements.txt](requirements.txt) for complete list with exact versions.

## 🛠️ Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/IamSteveV/file-sync.git
cd file-sync

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install with dev dependencies
pip install -e ".[dev]"
```

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=filesync --cov-report=html

# Run specific test file
pytest tests/test_manifest.py

# Run with verbose output
pytest -v
```

### Code Quality

```bash
# Format code with black
black src/

# Type checking with mypy
mypy src/

# Linting with flake8
flake8 src/
```

### Project Structure

```
file-sync/
├── src/filesync/          # Main package
│   ├── core/             # Core business logic
│   ├── gui/              # GUI components (14 modules)
│   ├── cli/              # CLI commands
│   ├── providers/        # Storage provider implementations
│   ├── encryption/       # Encryption layer
│   ├── auth/             # OAuth2 authentication
│   ├── daemon/           # Background auto-sync
│   ├── watcher/          # File system monitoring
│   ├── notifications/    # Desktop notifications
│   ├── scheduler/        # Task scheduling
│   └── quota/            # Quota monitoring
├── tests/                # Test suite
├── docs/                 # Documentation
│   ├── ARCHITECTURE.md
│   ├── ARCHITECTURE_DIAGRAM.md
│   └── GUI_USAGE.md
├── setup.py             # Package configuration
├── requirements.txt      # Dependencies
└── README.md            # This file
```

## 🔒 Security

### Encryption Details

- **Algorithm**: AES-256-GCM (Authenticated Encryption with Associated Data)
- **Key Derivation**: PBKDF2-HMAC-SHA256 with 100,000 iterations
- **Salt**: Unique 16-byte salt per file
- **Nonce**: Unique 12-byte nonce per encryption operation
- **Authentication**: HMAC tag verification on decryption

### File Format

```
[Magic: 4 bytes "FSYN"]
[Version: 1 byte]
[Salt: 16 bytes]
[Nonce: 12 bytes]
[Ciphertext + Authentication Tag]
```

### Zero-Trust Architecture

1. Files encrypted client-side before upload
2. Cloud providers never receive unencrypted data
3. Encryption keys never leave your device
4. Master passphrase stored only in memory (not persisted)
5. Per-file derived keys from master passphrase

### Security Best Practices

- Use strong passphrases (16+ characters, mixed case, numbers, symbols)
- Enable encryption for all Tier 0 (Critical) files
- Regularly verify file integrity with validation
- Keep backups of your manifest database
- Use Proton Drive for maximum privacy (E2EE)

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/amazing-feature`)
3. **Make your changes** with clear, descriptive commits
4. **Add tests** for new functionality
5. **Run tests** (`pytest`) and ensure they pass
6. **Format code** (`black src/`)
7. **Update documentation** as needed
8. **Push to branch** (`git push origin feature/amazing-feature`)
9. **Open a Pull Request** with detailed description

### Development Guidelines

- Follow PEP 8 style guide
- Write docstrings for all public functions and classes
- Add type hints where applicable
- Write tests for new features (aim for >80% coverage)
- Update ARCHITECTURE.md for significant changes
- Add examples to README for new features

### Areas for Contribution

- Additional cloud provider integrations
- Enhanced conflict resolution strategies
- Improved file preview support (more formats)
- Performance optimizations
- Mobile app development (iOS/Android)
- Web interface
- Documentation improvements
- Bug fixes and testing

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **CustomTkinter** by Tom Schimansky - Modern and customizable Tkinter UI library
- **cryptography** - High-level cryptographic recipes and primitives
- **Click** - Command-line interface creation kit
- **Cloud Provider SDKs** - Google, Microsoft, Box for their Python SDKs
- **watchdog** - Python library for file system monitoring
- **plyer** - Cross-platform native library access
- **PIL/Pillow** - Python Imaging Library

## 📞 Support & Community

- **Documentation**: See [docs/](docs/) directory for detailed guides
- **Issues**: [GitHub Issues](https://github.com/IamSteveV/file-sync/issues)
- **Discussions**: [GitHub Discussions](https://github.com/IamSteveV/file-sync/discussions)
- **Architecture**: [ARCHITECTURE.md](ARCHITECTURE.md) and [ARCHITECTURE_DIAGRAM.md](ARCHITECTURE_DIAGRAM.md)
- **GUI Guide**: [GUI_USAGE.md](docs/GUI_USAGE.md)

## 🗺️ Roadmap

### v0.1.0 - Current Release ✅

- ✅ Core deduplication engine with SHA-256
- ✅ 4-tier importance system with configurable redundancy
- ✅ Client-side AES-256-GCM encryption
- ✅ SQLite manifest database
- ✅ Local filesystem provider (offline backup)
- ✅ Modern GUI with CustomTkinter
- ✅ Complete CLI with Click
- ✅ Advanced search with multiple filter types
- ✅ File preview (text, images, PDFs)
- ✅ Conflict resolution UI
- ✅ Backup scheduler with multiple task types
- ✅ Cloud quota monitoring with alerts
- ✅ File system watching and auto-import
- ✅ Desktop notifications
- ✅ OAuth2 authentication framework
- ✅ System tray integration
- ✅ Keyboard shortcuts
- ✅ Drag-and-drop file addition

### v0.2.0 - Cloud Provider Integration

- [ ] Complete Google Drive implementation
- [ ] Complete OneDrive implementation
- [ ] Complete Box implementation
- [ ] Proton Drive integration (when API available)
- [ ] Multi-provider file synchronization
- [ ] Real-time sync status updates
- [ ] Bandwidth throttling
- [ ] Retry logic with exponential backoff
- [ ] Provider health monitoring

### v0.3.0 - Advanced Features

- [ ] File versioning with history
- [ ] Incremental sync (delta uploads)
- [ ] Compression options (optional)
- [ ] Advanced analytics and reporting
- [ ] Perceptual hashing for similar image detection
- [ ] Automated backup testing
- [ ] Custom lifecycle policy builder
- [ ] Bulk operations (batch add, move, delete)
- [ ] Import from existing cloud storage

### v1.0.0 - Production Ready

- [ ] Comprehensive test coverage (>90%)
- [ ] Performance optimizations
- [ ] Plugin system for extensibility
- [ ] Web-based management interface
- [ ] Cross-device manifest synchronization
- [ ] Team collaboration features
- [ ] Advanced security audit logging
- [ ] Multi-language support (i18n)
- [ ] Professional documentation site

### Future Considerations

- [ ] Mobile apps (iOS/Android)
- [ ] End-to-end encrypted sharing
- [ ] Blockchain-based integrity verification
- [ ] AI-powered file organization
- [ ] Smart deduplication for media files
- [ ] Integration with popular backup tools
- [ ] Enterprise features (LDAP, SSO, etc.)

---

**Built with ❤️ using Python and CustomTkinter**

**FileSync** - Your files, everywhere, safely.
