# FileSync Application Architecture Diagram

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              FILESYNC APPLICATION                                │
│                   Cloud Storage Deduplication & Sync System                      │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                                 USER INTERFACES                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                   │
│  ┌─────────────────────────┐              ┌──────────────────────────┐          │
│  │   CLI (Click-based)     │              │   GUI (CustomTkinter)    │          │
│  ├─────────────────────────┤              ├──────────────────────────┤          │
│  │ • filesync init         │              │ ┌──────────────────────┐ │          │
│  │ • filesync add          │              │ │  Main Window         │ │          │
│  │ • filesync list         │              │ │  ┌────────────────┐  │ │          │
│  │ • filesync status       │              │ │  │ Navigation     │  │ │          │
│  │ • filesync validate     │              │ │  │ - Dashboard    │  │ │          │
│  │ • filesync tiers        │              │ │  │ - Files        │  │ │          │
│  │ • filesync apply-policies│             │ │  │ - Providers    │  │ │          │
│  └─────────────────────────┘              │ │  │ - Validation   │  │ │          │
│           │                                │ │  │ - Settings     │  │ │          │
│           │                                │ │  └────────────────┘  │ │          │
│           │                                │ └──────────────────────┘ │          │
│           │                                │                          │          │
│           │                                │ ┌──────────────────────┐ │          │
│           │                                │ │  Advanced Features   │ │          │
│           │                                │ │  • Drag & Drop       │ │          │
│           │                                │ │  • OAuth2 Dialogs    │ │          │
│           │                                │ │  • Keyboard Shortcuts│ │          │
│           │                                │ │  • System Tray       │ │          │
│           │                                │ │  • Advanced Search   │ │          │
│           │                                │ │  • File Preview      │ │          │
│           │                                │ │  • Conflict Resolver │ │          │
│           │                                │ │  • Scheduler Config  │ │          │
│           │                                │ │  • Quota Monitor     │ │          │
│           │                                │ └──────────────────────┘ │          │
│           │                                └──────────────────────────┘          │
│           │                                           │                           │
└───────────┼───────────────────────────────────────────┼───────────────────────────┘
            │                                           │
            └───────────────────┬───────────────────────┘
                                │
┌───────────────────────────────▼───────────────────────────────────────────────────┐
│                              CORE BUSINESS LOGIC                                   │
├────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                    │
│  ┌──────────────────────────────────────────────────────────────────────────┐    │
│  │                         SYNC ENGINE (Orchestrator)                       │    │
│  │  ┌────────────────────────────────────────────────────────────────────┐  │    │
│  │  │ • add_file() - Add file to manifest & upload to providers          │  │    │
│  │  │ • sync_file() - Sync file across configured providers              │  │    │
│  │  │ • sync_all() - Full synchronization across all files                │  │    │
│  │  │ • validate_redundancy() - Check tier requirements                   │  │    │
│  │  │ • verify_integrity() - Hash verification                            │  │    │
│  │  └────────────────────────────────────────────────────────────────────┘  │    │
│  └───────────────┬──────────────────────────────────────────────────────────┘    │
│                  │                                                                │
│       ┌──────────┼──────────┬─────────────┬────────────┬─────────────┐          │
│       │          │           │             │            │             │          │
│       ▼          ▼           ▼             ▼            ▼             ▼          │
│  ┌─────────┐ ┌──────┐  ┌─────────┐  ┌──────────┐ ┌─────────┐  ┌──────────┐    │
│  │Manifest │ │Dedupe│  │Encryption│ │Redundancy│ │Lifecycle│  │ Watcher  │    │
│  │ Manager │ │Engine│  │  Layer   │ │Validator │ │ Manager │  │  System  │    │
│  └─────────┘ └──────┘  └─────────┘  └──────────┘ └─────────┘  └──────────┘    │
│       │          │           │             │            │             │          │
└───────┼──────────┼───────────┼─────────────┼────────────┼─────────────┼──────────┘
        │          │           │             │            │             │
        ▼          ▼           ▼             ▼            ▼             ▼

┌────────────────────────────────────────────────────────────────────────────────┐
│                            DATA & STORAGE LAYER                                 │
├────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────────┐         ┌──────────────────────────────────┐         │
│  │  Manifest Database  │         │      Provider Abstraction        │         │
│  │    (SQLite)         │         │                                  │         │
│  ├─────────────────────┤         │  ┌────────────────────────────┐  │         │
│  │ Tables:             │         │  │  StorageProvider (ABC)     │  │         │
│  │ • manifest_entries  │◄────────┤  │  ┌──────────────────────┐  │  │         │
│  │ • file_locations    │         │  │  │ Abstract Interface:  │  │  │         │
│  │ • tier_configs      │         │  │  │ • upload()           │  │  │         │
│  │                     │         │  │  │ • download()         │  │  │         │
│  │ Fields:             │         │  │  │ • delete()           │  │  │         │
│  │ • content_hash      │         │  │  │ • list_files()       │  │  │         │
│  │ • file_name         │         │  │  │ • get_metadata()     │  │  │         │
│  │ • size              │         │  │  └──────────────────────┘  │  │         │
│  │ • mime_type         │         │  └────────────────────────────┘  │         │
│  │ • tier              │         │               │                   │         │
│  │ • tags[]            │         │  ┌────────────▼────────────────┐ │         │
│  │ • encrypted         │         │  │   Provider Implementations  │ │         │
│  │ • created_at        │         │  └─────────────────────────────┘ │         │
│  │ • updated_at        │         │                                   │         │
│  │                     │         │  ┌─────────┐  ┌─────────┐        │         │
│  │ Indexes:            │         │  │  Local  │  │ GDrive  │        │         │
│  │ • content_hash      │         │  │Provider │  │Provider │        │         │
│  │ • tier              │         │  └─────────┘  └─────────┘        │         │
│  │ • tags              │         │       │            │              │         │
│  └─────────────────────┘         │  ┌────▼────┐  ┌───▼─────┐       │         │
│                                   │  │OneDrive│  │   Box   │       │         │
│                                   │  │Provider│  │Provider │       │         │
│                                   │  └─────────┘  └─────────┘       │         │
│                                   │       │                          │         │
│                                   │  ┌────▼────┐                    │         │
│                                   │  │ Proton  │                    │         │
│                                   │  │Provider │                    │         │
│                                   │  └─────────┘                    │         │
│                                   └──────────────────────────────────┘         │
└────────────────────────────────────────────────────────────────────────────────┘
                                          │
                                          ▼
┌────────────────────────────────────────────────────────────────────────────────┐
│                        EXTERNAL CLOUD STORAGE SERVICES                          │
├────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│   ┌─────────────┐  ┌─────────────┐  ┌──────────┐  ┌──────────┐               │
│   │   Google    │  │  Microsoft  │  │   Box    │  │  Proton  │               │
│   │   Drive     │  │  OneDrive   │  │   Cloud  │  │   Drive  │               │
│   │             │  │             │  │          │  │          │               │
│   │   OAuth2    │  │   OAuth2    │  │  OAuth2  │  │  OAuth2  │               │
│   │   REST API  │  │  Graph API  │  │  REST    │  │  REST    │               │
│   └─────────────┘  └─────────────┘  └──────────┘  └──────────┘               │
│                                                                                 │
│   ┌─────────────────────────────────────────────────────────────┐             │
│   │           Local Filesystem (Offline Backup)                 │             │
│   │           ~/filesync-offline/                               │             │
│   └─────────────────────────────────────────────────────────────┘             │
└────────────────────────────────────────────────────────────────────────────────┘


┌────────────────────────────────────────────────────────────────────────────────┐
│                          SUPPORTING SUBSYSTEMS                                  │
├────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌──────────────────────┐  ┌──────────────────────┐  ┌────────────────────┐  │
│  │  Encryption System   │  │  Authentication      │  │  Notification      │  │
│  ├──────────────────────┤  ├──────────────────────┤  ├────────────────────┤  │
│  │ • AES-256-GCM        │  │ • OAuth2Manager      │  │ • Desktop Notifier │  │
│  │ • PBKDF2 (100k iter) │  │ • Browser flow       │  │ • plyer library    │  │
│  │ • Per-file keys      │  │ • Local callback     │  │ • Cross-platform   │  │
│  │ • Master passphrase  │  │ • Token refresh      │  │ • Event types:     │  │
│  │ • Key manager        │  │ • Credential store   │  │   - Success        │  │
│  │                      │  │                      │  │   - Warning        │  │
│  │ File Format:         │  │ Providers:           │  │   - Error          │  │
│  │ [Magic][Ver][Salt]   │  │ • Google Drive       │  │   - Info           │  │
│  │ [Nonce][Ciphertext+  │  │ • OneDrive           │  │                    │  │
│  │        Tag]          │  │ • Box                │  │                    │  │
│  └──────────────────────┘  └──────────────────────┘  └────────────────────┘  │
│                                                                                 │
│  ┌──────────────────────┐  ┌──────────────────────┐  ┌────────────────────┐  │
│  │  Backup Scheduler    │  │  Quota Monitor       │  │  File Watcher      │  │
│  ├──────────────────────┤  ├──────────────────────┤  ├────────────────────┤  │
│  │ • Task types:        │  │ • QuotaInfo tracking │  │ • watchdog library │  │
│  │   - Validation       │  │ • Warning >80%       │  │ • File events:     │  │
│  │   - Verification     │  │ • Critical >95%      │  │   - Created        │  │
│  │   - Lifecycle        │  │ • Per-provider quota │  │   - Modified       │  │
│  │   - Sync             │  │ • Total summary      │  │ • Recursive watch  │  │
│  │   - Backup           │  │ • Cached data        │  │ • Auto-import      │  │
│  │                      │  │ • Real-time refresh  │  │ • Filter temp files│  │
│  │ • Frequencies:       │  │                      │  │ • Config per folder│  │
│  │   - Hourly           │  │ QuotaWidget modes:   │  │                    │  │
│  │   - Daily            │  │ • Full dialog        │  │ FolderWatchManager │  │
│  │   - Weekly           │  │ • Compact widget     │  │ • Multiple watches │  │
│  │   - Monthly          │  │ • Dashboard card     │  │ • Tier assignment  │  │
│  │   - Custom           │  │                      │  │                    │  │
│  └──────────────────────┘  └──────────────────────┘  └────────────────────┘  │
└────────────────────────────────────────────────────────────────────────────────┘
```

## Tier System Architecture

```
┌────────────────────────────────────────────────────────────────────────────────┐
│                           IMPORTANCE TIER SYSTEM                                │
├────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  Tier 0: CRITICAL                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐  │
│  │ Requirements:                                                            │  │
│  │ • Minimum 3 copies                                                       │  │
│  │ • Minimum 2 providers (cloud)                                            │  │
│  │ • Offline backup REQUIRED                                                │  │
│  │ • Encryption REQUIRED                                                    │  │
│  │ • Proton Drive REQUIRED (zero-trust)                                     │  │
│  │                                                                           │  │
│  │ Example: [Local] + [Proton] + [GDrive/OneDrive] (all encrypted)         │  │
│  └─────────────────────────────────────────────────────────────────────────┘  │
│                                                                                 │
│  Tier 1: IMPORTANT                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐  │
│  │ Requirements:                                                            │  │
│  │ • Minimum 2 copies                                                       │  │
│  │ • Minimum 2 providers                                                    │  │
│  │ • Offline backup optional                                                │  │
│  │ • Encryption optional                                                    │  │
│  │ • Proton Drive optional                                                  │  │
│  │                                                                           │  │
│  │ Example: [GDrive] + [OneDrive]                                           │  │
│  └─────────────────────────────────────────────────────────────────────────┘  │
│                                                                                 │
│  Tier 2: STANDARD                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐  │
│  │ Requirements:                                                            │  │
│  │ • Minimum 2 copies                                                       │  │
│  │ • Minimum 1 provider                                                     │  │
│  │ • Offline backup optional                                                │  │
│  │ • Encryption optional                                                    │  │
│  │                                                                           │  │
│  │ Example: [GDrive] + [Local]                                              │  │
│  └─────────────────────────────────────────────────────────────────────────┘  │
│                                                                                 │
│  Tier 3: ARCHIVE                                                               │
│  ┌─────────────────────────────────────────────────────────────────────────┐  │
│  │ Requirements:                                                            │  │
│  │ • Minimum 1 copy                                                         │  │
│  │ • Minimum 1 provider                                                     │  │
│  │                                                                           │  │
│  │ Example: [Box] (single copy, cost-optimized)                             │  │
│  └─────────────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────────────┘
```

## Data Flow Diagrams

### File Addition Flow

```
┌──────────┐
│   USER   │
└────┬─────┘
     │
     │ 1. Add File (GUI/CLI)
     ▼
┌─────────────────┐
│  Sync Engine    │
└────┬────────────┘
     │
     │ 2. Calculate SHA-256 hash
     ▼
┌─────────────────┐
│ Deduplication   │──── Check if hash exists ────┐
│    Engine       │                              │
└────┬────────────┘                              │
     │                                           │
     │ 3. New file (not duplicate)              │ Duplicate found
     ▼                                           │
┌─────────────────┐                              │
│   Encryption    │◄─── If tier requires ────────┤
│     Layer       │     encryption               │
└────┬────────────┘                              │
     │                                           │
     │ 4. Encrypted file (or original)          │
     ▼                                           │
┌─────────────────┐                              │
│    Manifest     │◄──────────────────────────────┘
│    Manager      │
└────┬────────────┘
     │
     │ 5. Create manifest entry
     ▼
┌─────────────────────────────────────────────────────┐
│              Upload to Providers                    │
│  (based on tier configuration)                      │
│                                                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐          │
│  │ Provider │  │ Provider │  │ Provider │          │
│  │    1     │  │    2     │  │    3     │          │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘          │
│       │             │             │                 │
└───────┼─────────────┼─────────────┼─────────────────┘
        │             │             │
        ▼             ▼             ▼
┌─────────────────────────────────────────────────────┐
│            Update manifest with locations           │
└─────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────┐
│           Validate redundancy requirements          │
└─────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────┐
│         Send notification (success/failure)         │
└─────────────────────────────────────────────────────┘
```

### Validation Flow

```
┌────────────────┐
│ Validator Run  │ (Manual or Scheduled)
└───────┬────────┘
        │
        ▼
┌─────────────────────────────────┐
│  Fetch all manifest entries     │
└────────┬────────────────────────┘
         │
         │ For each entry:
         ▼
┌─────────────────────────────────┐
│   Get tier requirements         │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────┐
│  Check against actual locations:                │
│  • Minimum copies met?                          │
│  • Minimum providers met?                       │
│  • Offline requirement met? (if required)       │
│  • Encryption requirement met? (if required)    │
│  • Proton requirement met? (if required)        │
└────────┬────────────────────────────────────────┘
         │
         ├──── PASS ────┐
         │              │
         ├──── FAIL ────┤
         │              │
         ▼              ▼
┌────────────┐   ┌──────────────────┐
│  Generate  │   │ Generate warning │
│   report   │   │  and remediation │
└────────────┘   │    suggestions   │
                 └──────────┬───────┘
                            │
                            ▼
                 ┌──────────────────┐
                 │ Notify user of   │
                 │ compliance issues│
                 └──────────────────┘
```

### Lifecycle Management Flow

```
┌──────────────────┐
│ Lifecycle Manager│ (Daily scheduled task)
└────────┬─────────┘
         │
         ▼
┌─────────────────────────────────┐
│ Load lifecycle policies          │
│ • Tag-based rules                │
│ • Time-based rules               │
│ • Size-based rules               │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│ Scan all manifest entries        │
└────────┬────────────────────────┘
         │
         │ For each file:
         ▼
┌─────────────────────────────────┐
│ Evaluate promotion rules:        │
│ • Has tag "important"?           │
│ • Accessed recently?             │
│ • Project file?                  │
└────────┬────────────────────────┘
         │
         ├──── Promote to higher tier
         │
         ▼
┌─────────────────────────────────┐
│ Evaluate demotion rules:         │
│ • Not accessed in 90 days?       │
│ • Has tag "archive"?             │
│ • Large file with low priority?  │
└────────┬────────────────────────┘
         │
         ├──── Demote to lower tier
         │
         ▼
┌─────────────────────────────────┐
│ Update manifest with new tier    │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│ Trigger sync to meet new         │
│ tier requirements                │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│ Generate lifecycle report        │
└──────────────────────────────────┘
```

## Component Interaction Matrix

```
┌──────────────┬────────┬────────┬────────┬──────┬───────┬────────┬────────┐
│ Component    │Manifest│Dedupe  │Encrypt │Sync  │Redund.│Lifecyc.│Provider│
├──────────────┼────────┼────────┼────────┼──────┼───────┼────────┼────────┤
│ Manifest Mgr │   -    │  READ  │  READ  │ R/W  │  READ │  R/W   │   -    │
│ Dedupe Engine│  READ  │   -    │   -    │ CALL │   -   │   -    │   -    │
│ Encryption   │  READ  │   -    │   -    │ CALL │   -   │   -    │   -    │
│ Sync Engine  │  R/W   │  CALL  │  CALL  │   -  │ CALL  │   -    │  R/W   │
│ Redundancy   │  READ  │   -    │   -    │   -  │   -   │   -    │  READ  │
│ Lifecycle    │  R/W   │   -    │   -    │ CALL │   -   │   -    │   -    │
│ Provider     │   -    │   -    │   -    │ USED │   -   │   -    │   -    │
│ GUI/CLI      │  READ  │   -    │   -    │ CALL │ CALL  │ CALL   │  READ  │
└──────────────┴────────┴────────┴────────┴──────┴───────┴────────┴────────┘

Legend: READ = Reads data, R/W = Read/Write, CALL = Invokes methods, USED = Used by
```

## GUI Component Tree

```
FileSyncApp (Main Window)
│
├─── Navigation Sidebar
│    ├─── Dashboard Button
│    ├─── Files Button
│    ├─── Providers Button
│    ├─── Validation Button
│    └─── Settings Button
│
├─── Content Area (Dynamic)
│    │
│    ├─── DashboardFrame
│    │    ├─── Statistics Cards
│    │    │    ├─── Total Files
│    │    │    ├─── Total Size
│    │    │    ├─── Encrypted Files
│    │    │    └─── Tier Distribution
│    │    ├─── Tier Breakdown Chart
│    │    ├─── Provider Distribution Chart
│    │    └─── QuotaCompactWidget
│    │
│    ├─── FilesFrame
│    │    ├─── Header (Title + Add Button)
│    │    ├─── Search/Filter Bar
│    │    │    ├─── Search Entry
│    │    │    ├─── Tier Filter Dropdown
│    │    │    ├─── Advanced Search Button → AdvancedSearchDialog
│    │    │    └─── Refresh Button
│    │    ├─── Drag & Drop Zone
│    │    ├─── File TreeView (Table)
│    │    │    └─── Context Menu
│    │    │         ├─── View Details
│    │    │         ├─── Preview → FilePreviewDialog
│    │    │         ├─── Download
│    │    │         └─── Delete
│    │    └─── File Details Panel
│    │
│    ├─── ProvidersFrame
│    │    ├─── Provider Cards (Local, GDrive, OneDrive, Box, Proton)
│    │    │    └─── Configure Button → OAuth2Dialog
│    │    └─── Add Provider Button
│    │
│    ├─── ValidationFrame
│    │    ├─── Validation Controls
│    │    │    ├─── Run Validation Button
│    │    │    └─── Last Run Info
│    │    ├─── Compliance Status
│    │    └─── Non-compliant Files List
│    │         └─── Fix Button (per file)
│    │
│    └─── SettingsFrame
│         ├─── Initialization Section
│         ├─── Paths Section
│         ├─── Auto-Import Section (File Watcher)
│         │    ├─── Watched Folders List
│         │    ├─── Add Folder Button → WatchFolderDialog
│         │    └─── Remove Folder Buttons
│         ├─── Notifications Section
│         │    ├─── Enable/Disable Toggle
│         │    └─── Test Notification Button
│         ├─── Encryption Section
│         └─── About Section
│
├─── System Tray Integration
│    ├─── Show/Hide Window
│    ├─── Quick Sync
│    ├─── Notifications
│    └─── Exit
│
├─── Auto-Sync Daemon (Background Thread)
│    ├─── Periodic Validation
│    ├─── Periodic Lifecycle
│    └─── Periodic Verification
│
└─── Keyboard Shortcuts
     ├─── Ctrl+1-5: Navigate views
     ├─── Ctrl+N: Add file
     ├─── Ctrl+R: Refresh
     ├─── Ctrl+F: Focus search
     ├─── Ctrl+S: Sync all
     └─── F1: Help

Dialogs (Modal Windows):
│
├─── PassphraseDialog (Encryption key entry)
├─── FileDetailsDialog (Detailed file information)
├─── BatchAddDialog (Multiple file addition)
├─── OAuth2Dialogs (Provider authentication)
│    ├─── GoogleDriveOAuth2Dialog
│    ├─── OneDriveOAuth2Dialog
│    └─── BoxOAuth2Dialog
├─── AdvancedSearchDialog (Complex search queries)
├─── FilePreviewDialog (File content preview)
├─── ConflictResolutionDialog (Version conflict resolution)
├─── WatchFolderDialog (Folder watch configuration)
├─── SchedulerDialog (Backup task scheduling)
│    └─── TaskEditorDialog (Individual task configuration)
└─── QuotaDialog (Full quota monitoring view)
```

## Technology Stack

```
┌────────────────────────────────────────────────────────────────────────┐
│                           TECHNOLOGY STACK                              │
├────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│ Programming Language:                                                  │
│  • Python 3.11+                                                        │
│                                                                         │
│ Core Libraries:                                                        │
│  • cryptography         - AES-256-GCM encryption                       │
│  • sqlite3             - Manifest database                             │
│  • hashlib             - SHA-256 hashing                               │
│  • pathlib             - File path handling                            │
│  • dataclasses         - Data models                                   │
│  • json                - Configuration storage                         │
│  • threading           - Background tasks                              │
│  • enum                - Type-safe enumerations                        │
│                                                                         │
│ GUI Framework:                                                         │
│  • customtkinter       - Modern dark-theme GUI                         │
│  • tkinter             - Base GUI framework                            │
│  • PIL/Pillow          - Image handling                                │
│                                                                         │
│ CLI Framework:                                                         │
│  • click               - Command-line interface                        │
│                                                                         │
│ Cloud Provider SDKs:                                                   │
│  • google-api-python-client  - Google Drive                            │
│  • msal                      - Microsoft OneDrive (Graph API)          │
│  • boxsdk                    - Box                                     │
│  • requests                  - HTTP client for Proton                  │
│                                                                         │
│ Additional Features:                                                   │
│  • pystray            - System tray integration                        │
│  • watchdog           - File system monitoring                         │
│  • plyer              - Cross-platform notifications                   │
│  • PyPDF2             - PDF preview (optional)                         │
│                                                                         │
│ Development Tools:                                                     │
│  • pytest             - Testing framework                              │
│  • black              - Code formatting                                │
│  • mypy               - Type checking                                  │
│  • setuptools         - Package distribution                           │
└────────────────────────────────────────────────────────────────────────┘
```

## File Structure

```
file-sync/
│
├── src/filesync/
│   ├── __init__.py
│   │
│   ├── models/                    # Data models
│   │   ├── __init__.py
│   │   ├── tier.py               # Tier enum and configurations
│   │   └── manifest_entry.py     # File entry data class
│   │
│   ├── core/                     # Core business logic
│   │   ├── __init__.py
│   │   ├── manifest.py           # Manifest database manager
│   │   ├── deduplication.py      # Content hashing
│   │   ├── sync.py               # Sync orchestration
│   │   ├── redundancy.py         # Redundancy validation
│   │   └── lifecycle.py          # Lifecycle policies
│   │
│   ├── encryption/               # Encryption layer
│   │   ├── __init__.py
│   │   └── crypto.py             # AES-256-GCM encryption
│   │
│   ├── providers/                # Storage provider abstraction
│   │   ├── __init__.py
│   │   ├── base.py               # Abstract provider interface
│   │   ├── local.py              # Local filesystem provider
│   │   ├── gdrive.py             # Google Drive provider
│   │   ├── onedrive.py           # OneDrive provider
│   │   ├── box.py                # Box provider
│   │   └── proton.py             # Proton Drive provider
│   │
│   ├── auth/                     # Authentication
│   │   ├── __init__.py
│   │   └── oauth2.py             # OAuth2 flow manager
│   │
│   ├── gui/                      # GUI components
│   │   ├── __init__.py
│   │   ├── main.py               # Main window
│   │   ├── dashboard.py          # Dashboard view
│   │   ├── files.py              # File management view
│   │   ├── providers.py          # Provider configuration view
│   │   ├── validation.py         # Validation view
│   │   ├── settings.py           # Settings view
│   │   ├── dialogs.py            # Common dialogs
│   │   ├── batch_add_dialog.py   # Batch file addition
│   │   ├── oauth_dialogs.py      # OAuth2 configuration
│   │   ├── shortcuts.py          # Keyboard shortcuts
│   │   ├── system_tray.py        # System tray integration
│   │   ├── advanced_search_dialog.py       # Advanced search
│   │   ├── file_preview_dialog.py          # File preview
│   │   ├── conflict_resolution_dialog.py   # Conflict resolution
│   │   ├── watch_folder_dialog.py          # Folder watch config
│   │   ├── scheduler_dialog.py             # Scheduler config
│   │   └── quota_widget.py                 # Quota monitoring
│   │
│   ├── cli/                      # CLI components
│   │   ├── __init__.py
│   │   └── main.py               # Click-based CLI
│   │
│   ├── daemon/                   # Background services
│   │   ├── __init__.py
│   │   └── auto_sync.py          # Auto-sync daemon
│   │
│   ├── watcher/                  # File system monitoring
│   │   ├── __init__.py
│   │   └── file_watcher.py       # Folder watching
│   │
│   ├── notifications/            # Notification system
│   │   ├── __init__.py
│   │   └── desktop.py            # Desktop notifications
│   │
│   ├── scheduler/                # Task scheduling
│   │   ├── __init__.py
│   │   └── backup_scheduler.py   # Backup scheduler
│   │
│   └── quota/                    # Quota monitoring
│       ├── __init__.py
│       └── quota_monitor.py      # Quota tracking
│
├── tests/                        # Test suite
│   ├── __init__.py
│   ├── test_manifest.py
│   ├── test_deduplication.py
│   ├── test_encryption.py
│   ├── test_sync.py
│   ├── test_redundancy.py
│   └── test_lifecycle.py
│
├── docs/                         # Documentation
│   ├── ARCHITECTURE.md
│   ├── ARCHITECTURE_DIAGRAM.md   # This file
│   ├── GUI_USAGE.md
│   └── API.md
│
├── setup.py                      # Package setup
├── requirements.txt              # Dependencies
├── README.md                     # Project overview
└── .gitignore
```

## Security Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                        SECURITY LAYERS                                  │
├────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Layer 1: Encryption at Rest                                           │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │ • AES-256-GCM (Authenticated Encryption)                          │ │
│  │ • PBKDF2 key derivation (100,000 iterations, SHA-256)             │ │
│  │ • Unique salt per file                                            │ │
│  │ • Unique nonce per encryption operation                           │ │
│  │ • HMAC verification on decrypt                                    │ │
│  │ • Master passphrase never stored (memory only)                    │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│  Layer 2: Encryption in Transit                                        │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │ • TLS 1.2+ for all provider communications                        │ │
│  │ • Certificate validation                                          │ │
│  │ • OAuth2 token encryption                                         │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│  Layer 3: Authentication & Authorization                                │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │ • OAuth2 for cloud providers                                      │ │
│  │ • Token refresh with secure storage                               │ │
│  │ • Credential encryption in config files                           │ │
│  │ • No plain-text password storage                                  │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│  Layer 4: Zero-Trust Architecture                                      │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │ • Client-side encryption before upload                            │ │
│  │ • Providers never see unencrypted critical data                   │ │
│  │ • Manifest hash verification                                      │ │
│  │ • Integrity checks on download                                    │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│  Layer 5: Data Redundancy                                              │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │ • Multiple provider copies                                        │ │
│  │ • Offline backup requirement for critical files                   │ │
│  │ • Continuous validation of redundancy                             │ │
│  │ • Automatic remediation on copy loss                              │ │
│  └──────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────┘
```

---

**Document Version:** 1.0
**Last Updated:** 2025-10-23
**FileSync Version:** 0.1.0
