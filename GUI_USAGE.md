# FileSync GUI - User Guide

This guide covers the graphical user interface (GUI) for FileSync, providing an easy-to-use desktop application for managing your cloud storage files.

## Installation

The GUI is included with FileSync by default:

```bash
pip install -e .
```

Or with cloud provider support:

```bash
pip install -e ".[gdrive,onedrive,box]"
```

## Launching the GUI

Start the FileSync GUI with:

```bash
filesync-gui
```

Or from Python:

```bash
python -m filesync.gui.main
```

## Interface Overview

The FileSync GUI consists of a sidebar navigation and main content area:

### Sidebar Navigation

- **📊 Dashboard** - Overview and statistics
- **📁 Files** - File management and browsing
- **✓ Validation** - Redundancy checking
- **☁️ Providers** - Cloud provider configuration
- **⚙️ Settings** - System settings

## First Run

### Initialize FileSync

If this is your first time using FileSync:

1. Click **⚙️ Settings** in the sidebar
2. Click **Initialize FileSync** button
3. FileSync will create:
   - Manifest database at `~/.filesync/manifest.db`
   - Offline storage at `~/filesync-offline/`
4. Return to Dashboard

## Using the Dashboard

The Dashboard provides an at-a-glance view of your file sync status:

### Statistics Cards

- **Total Files** - Number of files tracked
- **Total Size** - Combined size of all files
- **Encrypted** - Count of encrypted files
- **Active Providers** - Number of connected providers

### Files by Tier

Shows distribution across importance tiers:
- Critical (Tier 0)
- Important (Tier 1)
- Standard (Tier 2)
- Archive (Tier 3)

### Files by Provider

Shows which providers are storing your files

### Redundancy Status

- Compliant files count
- Non-compliant files needing attention
- Average redundancy score
- Critical issues warnings

## Managing Files

### Adding Files

1. Click **📁 Files** in the sidebar
2. Click **+ Add File** button
3. In the dialog:
   - Click **Select File** to choose a file
   - Choose **Importance Tier**:
     - **Critical** - Legal docs, passports (3 copies, encrypted)
     - **Important** - Work files (2 copies)
     - **Standard** - General files (1 copy)
     - **Archive** - Low-value files (1 copy)
   - Add **Tags** (comma-separated)
   - Check **Encrypt** if needed (required for Critical tier)
   - Optionally add a **Reason**
4. Click **Add File**

### Encryption Passphrase

When adding an encrypted file for the first time, you'll be prompted to set an encryption passphrase:

- Use a strong passphrase (12+ characters)
- Mix uppercase, lowercase, numbers, and symbols
- This passphrase encrypts all your files
- **Important**: Remember this passphrase - it cannot be recovered!

### Browsing Files

The Files view shows all tracked files with:
- File name
- Importance tier
- Size
- Number of locations
- Encryption status (🔒)
- Tags

### Search and Filter

- **Search box** - Find files by name or tag
- **Tier filter** - Show only files of a specific tier
- **🔄 Refresh** - Reload file list

### Viewing File Details

Double-click any file to see detailed information:
- Content hash
- Full metadata
- All storage locations
- Verification status

## Validating Redundancy

The Validation view helps ensure your files meet their tier requirements:

### Running Validation

1. Click **✓ Validation** in the sidebar
2. Review the **Summary**:
   - Compliant files (meeting requirements)
   - Non-compliant files (need attention)
   - Average redundancy score
3. Check **Files Needing Attention** list

### Actions

- **🔄 Refresh** - Reload validation results
- **✓ Verify All Files** - Check file integrity across providers
  - Downloads and verifies content hash
  - Updates verification timestamps
  - Reports any corrupted files

### Understanding Issues

For each non-compliant file, you'll see:
- Current number of copies and providers
- Required number of copies and providers
- Actions needed to become compliant

Common actions:
- `add_provider_1` - Upload to another provider
- `add_copy_1` - Create additional backup
- `add_proton_copy` - Upload to Proton Drive (Tier 0)
- `add_offline_copy` - Create offline backup (Tier 0)
- `encrypt_file` - Encryption required for tier

## Managing Providers

### Local Storage

Local storage is always active for offline backups:

1. Click **☁️ Providers** in the sidebar
2. Click **View Storage** on Local Storage card
3. See total, used, and available space

### Cloud Providers

Cloud provider configuration coming in future update. For now:

1. Manually configure in `~/.filesync/config.yaml`
2. Or use CLI: `filesync init --provider gdrive`
3. See README for OAuth2 setup instructions

Supported providers:
- **Google Drive** - OAuth2 required
- **Microsoft OneDrive** - OAuth2 required
- **Box** - OAuth2 required
- **Proton Drive** - Coming soon (awaiting official API)

## Settings

### Paths

View configured paths for:
- Manifest database
- Cache directory
- Offline storage

### Manifest Export/Import

**Export Manifest**
1. Click **Export Manifest**
2. Choose save location
3. Manifest exported as JSON

Use exports for:
- Backups
- Transferring to another machine
- Disaster recovery

**Import Manifest**
1. Click **Import Manifest**
2. Select JSON file
3. Entries merged into current manifest

### About

View FileSync version and license information.

## Tips and Best Practices

### File Organization

- Use consistent tagging (e.g., `work`, `personal`, `2024`)
- Add reasons for Critical tier files
- Tag legal documents: `legal`, `tax`, `contract`
- Tag by project: `project-name`, `client-name`

### Tier Guidelines

**Critical (Tier 0)**
- Irreplaceable documents
- Legal and financial records
- Passports, birth certificates
- Family photos/videos
- Business contracts

**Important (Tier 1)**
- Current work files
- Active projects
- Edited media
- Recreatable but valuable

**Standard (Tier 2)**
- Reference materials
- Downloads
- General media
- Documentation

**Archive (Tier 3)**
- Duplicates
- Old installers
- RAW photo bursts
- Completed project archives

### Security

- Use strong passphrases (12+ chars)
- Never share your encryption passphrase
- Keep manifest backups
- Verify files regularly (monthly)
- Review redundancy status weekly

### Performance

- Batch add similar files together
- Use tags for organization instead of folders
- Run validation during off-peak hours
- Clean up Archive tier files periodically

## Keyboard Shortcuts

Currently no keyboard shortcuts implemented. Coming in future update.

## Troubleshooting

### GUI Won't Start

```bash
# Check dependencies
pip install customtkinter>=5.2.0

# Try running directly
python -m filesync.gui.main
```

### Files Not Appearing

1. Click **🔄 Refresh** in Files view
2. Check if FileSync is initialized (Settings)
3. Verify manifest database exists

### Encryption Issues

- Make sure you've set an encryption passphrase
- Passphrase is required for all Critical tier files
- Can't decrypt? Check if passphrase is correct

### Provider Connection Errors

- Provider implementations coming soon
- Currently only local storage works
- Check README for provider setup

## Known Limitations

Current version (0.1.0):
- Cloud provider OAuth2 not yet implemented in GUI
- Must use CLI or config files for cloud setup
- No keyboard shortcuts
- Limited context menus
- No drag-and-drop file adding

Coming in future versions:
- Full provider configuration in GUI
- Drag-and-drop file upload
- Batch file operations
- Advanced search filters
- File preview
- System tray integration
- Auto-sync daemon

## Getting Help

- **Documentation**: See README.md and ARCHITECTURE.md
- **Issues**: https://github.com/IamSteveV/file-sync/issues
- **CLI Alternative**: Use `filesync --help` for command-line interface

## Advanced Features

### Custom Lifecycle Policies

(Coming soon in GUI - currently CLI only)

Policies can automatically:
- Promote files based on tags
- Demote old unused files
- Archive completed projects
- Tag by file type

### Batch Operations

(Coming soon in GUI - currently CLI only)

- Apply policies to multiple files
- Bulk tier changes
- Mass tag updates

## Feedback

We'd love to hear your feedback on the GUI!

Report issues or suggestions:
- GitHub Issues: https://github.com/IamSteveV/file-sync/issues
- Label with `gui` for GUI-specific issues
