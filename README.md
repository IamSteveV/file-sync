# FileSync - Cloud Storage Deduplication System

A cross-platform, provider-agnostic file synchronization and deduplication system with importance-based tiering, redundancy management, and client-side encryption.

## Overview

FileSync helps you manage files across multiple cloud storage providers while:
- **Eliminating duplicates** using content-based deduplication
- **Organizing by importance** with 4-tier classification system
- **Ensuring redundancy** following 3-2-1 backup principles
- **Protecting privacy** with client-side encryption (AES-256-GCM)
- **Automating lifecycle** with policy-based file management

## Features

### Core Capabilities

- **Content-Based Deduplication**: SHA-256 hashing identifies duplicate files across all storage locations
- **Multi-Provider Support**: Unified interface for Google Drive, OneDrive, Box, Proton Drive, and local storage
- **Importance Tiers**: 4 tiers (Critical, Important, Standard, Archive) with automatic redundancy requirements
- **Client-Side Encryption**: AES-256-GCM encryption before upload to untrusted providers
- **Single Source of Truth**: SQLite-based manifest tracks all file metadata and locations
- **Automated Policies**: Rule-based lifecycle management for tier assignment and archival

### Security

- **Zero-Trust**: Client-side encryption ensures providers never see unencrypted data
- **Key Derivation**: PBKDF2 with 100,000 iterations for passphrase-based key generation
- **Per-File Keys**: Each file encrypted with unique derived key
- **Authenticated Encryption**: AES-256-GCM provides confidentiality and integrity

### Redundancy Strategy

Implements 3-2-1 backup strategy:
- **Tier 0 (Critical)**: 3 copies across ≥2 providers + offline backup
- **Tier 1 (Important)**: 2 copies across 2 providers
- **Tier 2 (Standard)**: 1 primary copy + optional secondary
- **Tier 3 (Archive)**: Single copy on cheapest storage

## Installation

### Prerequisites

- Python 3.11 or higher
- pip package manager

### Basic Installation

```bash
# Clone the repository
git clone https://github.com/IamSteveV/file-sync.git
cd file-sync

# Install in development mode
pip install -e .

# Or install from PyPI (when published)
# pip install filesync
```

### With Cloud Provider Support

```bash
# Install with Google Drive support
pip install -e ".[gdrive]"

# Install with all providers
pip install -e ".[gdrive,onedrive,box]"
```

## Quick Start

### 1. Initialize FileSync

```bash
filesync init
```

This creates:
- Manifest database at `~/.filesync/manifest.db`
- Configuration file at `~/.filesync/config.yaml`
- Local offline storage at `~/filesync-offline/`

### 2. Add a File

```bash
# Add a standard file
filesync add document.pdf --tier 2

# Add a critical file with encryption
filesync add passport.pdf --tier 0 --encrypt --tags "legal,personal"

# Add with custom reason
filesync add contract.pdf --tier 0 --encrypt --reason "Employment contract"
```

### 3. Check Status

```bash
# View overall status
filesync status

# List all files
filesync list

# List by tier
filesync list --tier 0

# List by tag
filesync list --tag legal
```

### 4. Validate Redundancy

```bash
# Check if all files meet tier requirements
filesync validate
```

### 5. Apply Lifecycle Policies

```bash
# Preview policy actions
filesync apply-policies --dry-run

# Apply policies
filesync apply-policies
```

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed system design.

### Key Components

```
┌─────────────────────────────────────────────┐
│            CLI Interface                    │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────┴──────────────────────────┐
│          Core Engine                        │
│  ┌────────────────────────────────────────┐ │
│  │  Manifest Manager (SQLite)             │ │
│  │  - Content hash index                  │ │
│  │  - Location tracking                   │ │
│  │  - Metadata & tags                     │ │
│  └────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────┐ │
│  │  Deduplication Engine                  │ │
│  │  - SHA-256 content hashing             │ │
│  └────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────┐ │
│  │  Encryption Layer (AES-256-GCM)        │ │
│  └────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────┐ │
│  │  Sync Engine                           │ │
│  └────────────────────────────────────────┘ │
└──────────────────┬──────────────────────────┘
                   │
    ┌──────────────┼──────────────┬────────┐
    │              │              │        │
┌───▼───┐   ┌──────▼────┐  ┌─────▼───┐  ┌▼──────┐
│ GDrive│   │ OneDrive  │  │   Box   │  │Proton │
└───────┘   └───────────┘  └─────────┘  └───────┘
```

## Importance Tiers

### Tier 0 - Critical

**Use for**: Legal docs, taxes, passports, irreplaceable photos, contracts

**Requirements**:
- 3 copies minimum
- 2+ different providers
- Must include Proton Drive (E2EE)
- Offline backup required
- Encryption mandatory
- Verified weekly

**Example**:
```bash
filesync add passport.pdf --tier 0 --encrypt --tags "legal,id"
```

### Tier 1 - Important

**Use for**: Work files, edited photo sets, valuable documents

**Requirements**:
- 2 copies minimum
- 2 different providers
- Encryption for PII/financial
- Verified bi-weekly

**Example**:
```bash
filesync add project.zip --tier 1 --tags "work,project"
```

### Tier 2 - Standard

**Use for**: Reference PDFs, downloads, general media

**Requirements**:
- 1 primary copy
- Optional secondary
- Verified monthly

**Example**:
```bash
filesync add ebook.pdf --tier 2
```

### Tier 3 - Archive

**Use for**: Duplicates, RAW photo bursts, installers, low-value files

**Requirements**:
- Single copy
- Cheapest storage
- Verified on-demand

**Example**:
```bash
filesync add installer.exe --tier 3 --tags "software,archive"
```

## Configuration

Edit `~/.filesync/config.yaml`:

```yaml
storage:
  manifest_path: ~/.filesync/manifest.db
  cache_path: ~/.filesync/cache
  temp_path: ~/.filesync/temp

providers:
  local:
    enabled: true
    path: ~/filesync-offline

  gdrive:
    enabled: false
    credentials_file: ~/.filesync/gdrive-creds.json
    root_folder: /FileSync

  # ... other providers

encryption:
  enabled: true
  algorithm: AES-256-GCM
```

## CLI Commands

### Core Commands

- `filesync init` - Initialize FileSync
- `filesync add FILE` - Add a file
- `filesync status` - Show status
- `filesync list` - List files
- `filesync validate` - Validate redundancy
- `filesync tiers` - Show tier configuration

### Options

- `--tier N` - Set importance tier (0-3)
- `--tags TAGS` - Comma-separated tags
- `--encrypt` - Encrypt file
- `--reason TEXT` - Reason for tier assignment
- `--dry-run` - Preview without changes

## Lifecycle Policies

FileSync includes automated policies:

### Promotion Policies

- Files tagged `legal`, `tax`, `contract`, or `passport` → Tier 0
- Recently modified `work` files → Tier 1

### Demotion Policies

- Standard files not accessed in 365 days → Archive
- Completed projects after 90 days → Standard

### Auto-Tagging

- Files with "duplicate" in name → tagged `duplicate`
- Image MIME types → tagged `image`

## Provider Setup

### Google Drive

1. Create project in Google Cloud Console
2. Enable Google Drive API
3. Create OAuth 2.0 credentials
4. Download credentials as JSON
5. Save to `~/.filesync/gdrive-creds.json`
6. Enable in config.yaml
7. Run `filesync add` - will prompt for authorization

### OneDrive

1. Register app in Azure AD
2. Get client ID and secret
3. Configure redirect URI
4. Save credentials
5. Enable in config.yaml

### Box

1. Create Box application
2. Get OAuth credentials
3. Configure redirect URI
4. Save credentials
5. Enable in config.yaml

### Proton Drive

Note: Awaiting official Proton Drive API. Currently not implemented.

## Development

### Project Structure

```
file-sync/
├── src/filesync/
│   ├── core/           # Core engine components
│   │   ├── manifest.py
│   │   ├── deduplication.py
│   │   ├── sync.py
│   │   ├── redundancy.py
│   │   └── lifecycle.py
│   ├── providers/      # Storage provider implementations
│   │   ├── base.py
│   │   ├── local.py
│   │   ├── gdrive.py
│   │   ├── onedrive.py
│   │   ├── box.py
│   │   └── proton.py
│   ├── encryption/     # Encryption layer
│   │   └── crypto.py
│   ├── models/         # Data models
│   │   ├── tier.py
│   │   └── manifest_entry.py
│   ├── cli/            # Command-line interface
│   │   └── main.py
│   └── utils/          # Utilities
├── tests/              # Test suite
├── docs/               # Documentation
├── ARCHITECTURE.md     # Detailed architecture
├── README.md          # This file
├── requirements.txt   # Dependencies
└── setup.py           # Package setup
```

### Running Tests

```bash
pip install -e ".[dev]"
pytest tests/
```

### Code Style

```bash
black src/
mypy src/
```

## Roadmap

### v0.1 (MVP) - Current

- [x] Core architecture
- [x] Manifest system
- [x] Content-based deduplication
- [x] Local provider
- [x] Tier system
- [x] Client-side encryption
- [x] CLI interface
- [ ] Unit tests

### v0.2

- [ ] Google Drive implementation
- [ ] OneDrive implementation
- [ ] Box implementation
- [ ] Automated tier assignment
- [ ] Redundancy validation
- [ ] Full sync engine

### v0.3

- [ ] Lifecycle policies
- [ ] Migration automation
- [ ] Verification system
- [ ] Offline backup management

### v1.0

- [ ] Desktop GUI (Electron/Tauri)
- [ ] Cross-device manifest sync
- [ ] Perceptual hashing for images
- [ ] Performance optimizations
- [ ] Mobile apps (iOS/Android)

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## Security

### Reporting Vulnerabilities

Please report security issues to [security contact].

### Best Practices

- Never commit credentials or encryption keys
- Use strong passphrases (12+ characters, mixed case, numbers, symbols)
- Keep backups of your manifest database
- Verify file integrity regularly

## License

MIT License - see LICENSE file

## Support

- Issues: https://github.com/IamSteveV/file-sync/issues
- Documentation: See docs/ directory
- Architecture: See ARCHITECTURE.md

## Acknowledgments

- Built with Python 3.11+
- Uses cryptography library for AES-256-GCM
- CLI powered by Click
- Inspired by 3-2-1 backup principles
