"""File system watching for automatic file detection."""

import threading
import time
from pathlib import Path
from typing import Optional, Callable, List, Set
from datetime import datetime

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileCreatedEvent, FileModifiedEvent
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    print("Warning: watchdog not installed. File watching disabled.")
    print("Install with: pip install watchdog")


class FileWatcher(FileSystemEventHandler):
    """Watches a folder for new files and triggers callbacks."""

    def __init__(self, on_file_added: Callable[[Path], None]):
        """
        Initialize file watcher.

        Args:
            on_file_added: Callback function called when new file detected
        """
        super().__init__()
        self.on_file_added = on_file_added
        self.processed_files: Set[str] = set()
        self.ignore_patterns = ['.tmp', '.temp', '~', '.DS_Store', 'Thumbs.db']

    def on_created(self, event):
        """Handle file creation events."""
        if event.is_directory:
            return

        file_path = Path(event.src_path)

        # Ignore temporary and system files
        if any(pattern in file_path.name for pattern in self.ignore_patterns):
            return

        # Avoid processing same file multiple times
        if str(file_path) in self.processed_files:
            return

        # Wait a bit to ensure file is fully written
        time.sleep(0.5)

        # Verify file still exists and is readable
        if not file_path.exists() or not file_path.is_file():
            return

        try:
            # Try to open file to ensure it's not locked
            with open(file_path, 'rb') as f:
                f.read(1)

            # Mark as processed
            self.processed_files.add(str(file_path))

            # Trigger callback
            self.on_file_added(file_path)

        except (IOError, PermissionError):
            # File still being written or locked
            pass

    def on_modified(self, event):
        """Handle file modification events."""
        # Only process modifications as potential new files
        # if we haven't seen them before
        if event.is_directory:
            return

        file_path = Path(event.src_path)

        if str(file_path) not in self.processed_files:
            self.on_created(event)


class FolderWatchManager:
    """Manages multiple folder watches."""

    def __init__(self):
        """Initialize folder watch manager."""
        self.observers: dict[str, Observer] = {}
        self.watchers: dict[str, FileWatcher] = {}
        self.running = False

        if not WATCHDOG_AVAILABLE:
            print("Folder watching not available - watchdog not installed")

    def add_watch(self, folder_path: Path, callback: Callable[[Path], None],
                  recursive: bool = False) -> bool:
        """
        Add a folder to watch.

        Args:
            folder_path: Path to folder to watch
            callback: Function to call when new file detected
            recursive: Whether to watch subfolders

        Returns:
            True if watch added successfully
        """
        if not WATCHDOG_AVAILABLE:
            return False

        folder_str = str(folder_path.absolute())

        # Don't add duplicate watches
        if folder_str in self.observers:
            return False

        if not folder_path.exists() or not folder_path.is_dir():
            return False

        try:
            # Create watcher
            watcher = FileWatcher(callback)
            self.watchers[folder_str] = watcher

            # Create observer
            observer = Observer()
            observer.schedule(watcher, str(folder_path), recursive=recursive)
            observer.start()

            self.observers[folder_str] = observer
            self.running = True

            return True

        except Exception as e:
            print(f"Failed to add watch for {folder_path}: {e}")
            return False

    def remove_watch(self, folder_path: Path) -> bool:
        """
        Remove a folder watch.

        Args:
            folder_path: Path to folder to stop watching

        Returns:
            True if watch removed successfully
        """
        folder_str = str(folder_path.absolute())

        if folder_str not in self.observers:
            return False

        try:
            observer = self.observers[folder_str]
            observer.stop()
            observer.join(timeout=5)

            del self.observers[folder_str]
            del self.watchers[folder_str]

            if not self.observers:
                self.running = False

            return True

        except Exception as e:
            print(f"Failed to remove watch for {folder_path}: {e}")
            return False

    def stop_all(self):
        """Stop all folder watches."""
        for folder_path in list(self.observers.keys()):
            self.remove_watch(Path(folder_path))

        self.running = False

    def get_watched_folders(self) -> List[Path]:
        """Get list of currently watched folders."""
        return [Path(p) for p in self.observers.keys()]

    def is_watching(self, folder_path: Path) -> bool:
        """Check if a folder is being watched."""
        return str(folder_path.absolute()) in self.observers


class AutoImportConfig:
    """Configuration for automatic file import."""

    def __init__(self):
        """Initialize auto-import config."""
        self.enabled = False
        self.watched_folders: List[dict] = []
        self.default_tier = 2  # Standard
        self.default_tags: List[str] = ["auto-imported"]
        self.require_confirmation = True
        self.auto_encrypt_critical = True

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "enabled": self.enabled,
            "watched_folders": self.watched_folders,
            "default_tier": self.default_tier,
            "default_tags": self.default_tags,
            "require_confirmation": self.require_confirmation,
            "auto_encrypt_critical": self.auto_encrypt_critical,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AutoImportConfig":
        """Create from dictionary."""
        config = cls()
        config.enabled = data.get("enabled", False)
        config.watched_folders = data.get("watched_folders", [])
        config.default_tier = data.get("default_tier", 2)
        config.default_tags = data.get("default_tags", ["auto-imported"])
        config.require_confirmation = data.get("require_confirmation", True)
        config.auto_encrypt_critical = data.get("auto_encrypt_critical", True)
        return config

    def add_folder(self, path: Path, tier: int = 2, tags: List[str] = None,
                   recursive: bool = False):
        """Add a folder to watch list."""
        self.watched_folders.append({
            "path": str(path.absolute()),
            "tier": tier,
            "tags": tags or self.default_tags,
            "recursive": recursive,
            "added_at": datetime.now().isoformat(),
        })

    def remove_folder(self, path: Path) -> bool:
        """Remove a folder from watch list."""
        path_str = str(path.absolute())
        for i, folder in enumerate(self.watched_folders):
            if folder["path"] == path_str:
                self.watched_folders.pop(i)
                return True
        return False
