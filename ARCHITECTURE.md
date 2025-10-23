# Cloud Storage Deduplication System - Architecture

## Overview

A cross-platform, provider-agnostic file synchronization and deduplication system with importance-based tiering, redundancy management, and client-side encryption.

## Core Principles

1. **Content-Addressable Storage**: Files identified by SHA-256 hash
2. **Single Source of Truth**: Centralized manifest tracks all file metadata
3. **Zero-Trust Security**: Client-side encryption before upload
4. **Provider Agnostic**: Abstracted interface for all storage providers
5. **Automated Lifecycle**: Policy-driven file placement and migration

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Client Applications                     │
│              (CLI, Desktop, Mobile - Future)                 │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────┴──────────────────────────────────┐
│                     Core Engine                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              Manifest Manager                          │ │
│  │  - Content hash index                                  │ │
│  │  - Location tracking                                   │ │
│  │  - Metadata & tags                                     │ │
│  │  - Importance tier                                     │ │
│  └────────────────────────────────────────────────────────┘ │
│                           │                                  │
│  ┌────────────────────────┴──────────────────────────────┐  │
│  │         Deduplication Engine                          │  │
│  │  - Content hashing (SHA-256)                          │  │
│  │  - Similarity detection (future: perceptual hashing)  │  │
│  │  - Duplicate resolution                               │  │
│  └───────────────────────────────────────────────────────┘  │
│                           │                                  │
│  ┌────────────────────────┴──────────────────────────────┐  │
│  │         Encryption Layer                              │  │
│  │  - AES-256-GCM encryption                             │  │
│  │  - Key derivation (PBKDF2/Argon2)                     │  │
│  │  - Per-file encryption keys                           │  │
│  └───────────────────────────────────────────────────────┘  │
│                           │                                  │
│  ┌────────────────────────┴──────────────────────────────┐  │
│  │         Tier & Redundancy Manager                     │  │
│  │  - Tier assignment rules                              │  │
│  │  - Redundancy validation (3-2-1 backup)               │  │
│  │  - Policy enforcement                                 │  │
│  └───────────────────────────────────────────────────────┘  │
│                           │                                  │
│  ┌────────────────────────┴──────────────────────────────┐  │
│  │         Sync Engine                                   │  │
│  │  - Upload/download queue                              │  │
│  │  - Bandwidth management                               │  │
│  │  - Conflict resolution                                │  │
│  │  - Retry logic                                        │  │
│  └───────────────────────────────────────────────────────┘  │
│                           │                                  │
│  ┌────────────────────────┴──────────────────────────────┐  │
│  │         Provider Abstraction Layer                    │  │
│  │  Common Interface:                                    │  │
│  │  - upload(file, path)                                 │  │
│  │  - download(path)                                     │  │
│  │  - delete(path)                                       │  │
│  │  - list(path)                                         │  │
│  │  - getMetadata(path)                                  │  │
│  └───────────────────────────────────────────────────────┘  │
└──────────────────────────┬──────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┬────────────────┐
        │                  │                  │                │
┌───────▼────┐    ┌────────▼───────┐   ┌─────▼──────┐  ┌──────▼─────┐
│  Google    │    │   OneDrive     │   │    Box     │  │   Proton   │
│  Drive     │    │                │   │            │  │   Drive    │
└────────────┘    └────────────────┘   └────────────┘  └────────────┘
```

## Data Models

### Manifest Entry

```json
{
  "contentHash": "sha256:abc123...",
  "fileName": "vacation-photo.jpg",
  "size": 2048576,
  "mimeType": "image/jpeg",
  "tier": 0,
  "tags": ["personal", "vacation", "2024"],
  "encrypted": true,
  "encryptionKeyId": "key-abc123",
  "locations": [
    {
      "provider": "proton",
      "path": "/encrypted/vacation-photo.jpg.enc",
      "uploadedAt": "2024-01-15T10:30:00Z",
      "verified": true,
      "lastVerified": "2024-01-16T08:00:00Z"
    },
    {
      "provider": "gdrive",
      "path": "/backups/vacation-photo.jpg.enc",
      "uploadedAt": "2024-01-15T10:35:00Z",
      "verified": true,
      "lastVerified": "2024-01-16T08:00:00Z"
    }
  ],
  "createdAt": "2024-01-15T10:00:00Z",
  "modifiedAt": "2024-01-15T10:00:00Z",
  "importanceReason": "Family vacation photos - irreplaceable"
}
```

### Tier Configuration

```json
{
  "tier": 0,
  "name": "Critical",
  "description": "Irreplaceable + sensitive or business-critical",
  "minCopies": 3,
  "minProviders": 2,
  "requireOffline": true,
  "requireEncryption": true,
  "requireProton": true,
  "allowedProviders": ["proton", "gdrive", "box", "onedrive", "local"],
  "verificationInterval": "7d"
}
```

## Importance Tiers

### Tier 0 - Critical
- **Examples**: Legal docs, taxes, passports, birth videos, contracts
- **Redundancy**: 3 copies across ≥2 providers + offline
- **Encryption**: Always (client-side)
- **Providers**: Proton (required) + 2 others
- **Verification**: Weekly

### Tier 1 - Important
- **Examples**: Work artifacts, edited photo sets
- **Redundancy**: 2 copies across 2 providers
- **Encryption**: Required for PII/financial
- **Providers**: Any 2 providers
- **Verification**: Bi-weekly

### Tier 2 - Standard
- **Examples**: Reference PDFs, downloads, media
- **Redundancy**: 1 primary + optional secondary
- **Encryption**: Optional
- **Providers**: Any provider
- **Verification**: Monthly

### Tier 3 - Cold/Archive
- **Examples**: Duplicates, RAW bursts, installers
- **Redundancy**: Single copy or delete
- **Encryption**: Optional
- **Providers**: Cheapest provider
- **Verification**: On-demand

## Deduplication Strategy

### Content-Based Deduplication
1. Calculate SHA-256 hash of file content
2. Check manifest for existing hash
3. If exists:
   - Verify tier requirements met
   - Add new location if needed for redundancy
   - Update metadata (tags, filename, etc.)
4. If new:
   - Create manifest entry
   - Upload to required providers based on tier

### Similarity Detection (Future)
- Perceptual hashing for images (pHash, dHash)
- Near-duplicate detection
- User-guided merge/keep decisions

## Encryption Strategy

### Client-Side Encryption
- **Algorithm**: AES-256-GCM
- **Key Derivation**: Argon2id (or PBKDF2 fallback)
- **Master Key**: User-provided passphrase
- **Per-File Keys**: Derived from master key + file hash
- **Metadata**: Encrypted separately (filename, tags)

### Key Management
```
Master Key (from passphrase)
    ├─> File Encryption Key = HKDF(master, context="file", info=contentHash)
    ├─> Metadata Key = HKDF(master, context="meta", info=contentHash)
    └─> Manifest Key = HKDF(master, context="manifest", info=userID)
```

### Encrypted File Format
```
[Magic Bytes: 4B] [Version: 1B] [Nonce: 12B] [Encrypted Data] [Auth Tag: 16B]
```

## Provider Abstraction

### Interface Definition
```python
class StorageProvider:
    def authenticate(credentials) -> Session
    def upload(session, localPath, remotePath, metadata) -> UploadResult
    def download(session, remotePath, localPath) -> DownloadResult
    def delete(session, remotePath) -> DeleteResult
    def list(session, remotePath, recursive) -> List[FileInfo]
    def getMetadata(session, remotePath) -> FileMetadata
    def getQuota(session) -> QuotaInfo
```

### Supported Providers
1. **Google Drive**: OAuth2, REST API
2. **OneDrive**: OAuth2, Microsoft Graph API
3. **Box**: OAuth2, Box API
4. **Proton Drive**: E2EE, Proton API
5. **Local**: File system (for offline copies)

## Sync Engine

### Upload Flow
```
1. Scan local file/directory
2. Calculate content hash
3. Check manifest for duplicates
4. Determine tier (user input or rules)
5. Encrypt if required
6. Upload to required providers
7. Verify uploads
8. Update manifest
```

### Download Flow
```
1. Query manifest by filename/hash/tag
2. Select optimal provider (speed, cost, availability)
3. Download file
4. Decrypt if encrypted
5. Verify content hash
6. Cache locally
```

### Conflict Resolution
- **Content-based**: Same hash = same file (no conflict)
- **Metadata conflicts**: Last-write-wins with version history
- **User override**: Manual resolution for edge cases

## Lifecycle Management

### Automated Policies

#### Promotion (Increase Importance)
```
IF tag IN ["passport", "legal", "contract", "tax"]
THEN tier = 0

IF tag IN ["work", "project"] AND modified_within("30d")
THEN tier = 1
```

#### Demotion (Decrease Importance)
```
IF tier = 2 AND not_accessed_for("365d")
THEN tier = 3

IF tier = 1 AND marked_as("completed") AND age > "90d"
THEN tier = 2
```

#### Deletion
```
IF tier = 3 AND age > "730d" AND tag = "duplicate"
THEN delete (keep manifest entry)
```

### Migration
```
IF tier_changed
THEN
  - Validate current locations
  - Add/remove copies to match tier requirements
  - Re-encrypt if encryption requirement changed
  - Update manifest
```

## Technology Stack

### Core (Python-based for cross-platform)
- **Language**: Python 3.11+
- **Hashing**: hashlib (SHA-256), imagehash (perceptual)
- **Encryption**: cryptography library (AES-256-GCM, Argon2)
- **Database**: SQLite (manifest) + JSON export
- **Config**: YAML/TOML

### Provider SDKs
- **Google Drive**: google-api-python-client
- **OneDrive**: OneDrive SDK for Python
- **Box**: boxsdk
- **Proton Drive**: Custom REST client

### CLI
- **Framework**: Click or Typer
- **Progress**: Rich library
- **Config**: python-dotenv

### Future: Desktop GUI
- **Framework**: Electron or Tauri
- **Language**: TypeScript + React

### Future: Mobile
- **iOS**: Swift + SwiftUI
- **Android**: Kotlin + Jetpack Compose

## Security Considerations

1. **Zero-Trust**: Never trust provider storage (encrypt first)
2. **Key Security**: Master key never stored, only derived in memory
3. **Manifest Security**: Encrypt manifest database
4. **Authentication**: OAuth2 tokens stored securely (OS keychain)
5. **Audit Trail**: Log all operations for forensics
6. **Access Control**: Per-user encryption keys
7. **Secure Delete**: Overwrite before deletion for local files

## Performance Optimizations

1. **Chunked Uploads**: Split large files (>100MB) into chunks
2. **Parallel Uploads**: Upload to multiple providers concurrently
3. **Resume Support**: Checkpoint uploads for retry
4. **Compression**: Optional pre-encryption compression (gzip, zstd)
5. **Caching**: Local cache for frequently accessed files
6. **Incremental Sync**: Only sync changes, not full re-upload
7. **Smart Hashing**: Skip hashing if file size/mtime unchanged

## Deployment Architecture

### Phase 1: CLI Tool (Current)
- Local installation on desktop (Windows, macOS, Linux)
- Manual sync triggered by user
- Local manifest database

### Phase 2: Desktop GUI
- System tray integration
- Auto-sync daemon
- Visual file browser

### Phase 3: Mobile Apps
- Photo upload integration
- Mobile manifest sync
- Offline mode

### Phase 4: Cloud Service (Optional)
- Centralized manifest sync across devices
- Web interface
- Shared folders

## Roadmap

### MVP (v0.1)
- [x] Architecture design
- [ ] Manifest system
- [ ] Content hashing
- [ ] Single provider (Google Drive)
- [ ] Tier system (manual assignment)
- [ ] CLI interface
- [ ] Basic encryption

### v0.2
- [ ] All 4 providers (GDrive, OneDrive, Box, Proton)
- [ ] Automated tier assignment
- [ ] Redundancy validation
- [ ] Sync engine

### v0.3
- [ ] Lifecycle policies
- [ ] Migration automation
- [ ] Verification system
- [ ] Offline backup

### v1.0
- [ ] Desktop GUI
- [ ] Cross-device manifest sync
- [ ] Perceptual hashing for images
- [ ] Performance optimizations

## Configuration Example

```yaml
# config.yaml
storage:
  manifest_path: ~/.file-sync/manifest.db
  cache_path: ~/.file-sync/cache
  temp_path: ~/.file-sync/temp

providers:
  gdrive:
    enabled: true
    auth: oauth2
    credentials_file: ~/.file-sync/gdrive-creds.json
    root_folder: /FileSync

  onedrive:
    enabled: true
    auth: oauth2
    credentials_file: ~/.file-sync/onedrive-creds.json
    root_folder: /FileSync

  box:
    enabled: true
    auth: oauth2
    credentials_file: ~/.file-sync/box-creds.json
    root_folder: /FileSync

  proton:
    enabled: true
    auth: credentials
    credentials_file: ~/.file-sync/proton-creds.json
    root_folder: /FileSync

  local:
    enabled: true
    path: ~/FileSync-Offline

encryption:
  enabled: true
  algorithm: AES-256-GCM
  key_derivation: argon2id
  master_key_source: env  # env, file, or prompt

tiers:
  - id: 0
    name: Critical
    min_copies: 3
    min_providers: 2
    require_offline: true
    require_encryption: true
    require_proton: true
    verification_days: 7

  - id: 1
    name: Important
    min_copies: 2
    min_providers: 2
    require_encryption: false
    verification_days: 14

  - id: 2
    name: Standard
    min_copies: 1
    min_providers: 1
    verification_days: 30

  - id: 3
    name: Archive
    min_copies: 1
    min_providers: 1
    verification_days: 0

policies:
  auto_tier: true
  auto_tag: true
  auto_encrypt_sensitive: true
  verify_on_upload: true
  checksum_algorithm: sha256

  lifecycle:
    - name: "Promote legal documents"
      condition: "tag:legal OR tag:tax OR tag:contract"
      action: "set_tier:0"

    - name: "Archive old duplicates"
      condition: "tier:2 AND age:>365d AND tag:duplicate"
      action: "set_tier:3"
```

## License
TBD (MIT or Apache 2.0 recommended for open source)
