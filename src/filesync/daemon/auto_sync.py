"""Auto-sync daemon for background file synchronization."""

import threading
import time
from pathlib import Path
from typing import Optional, Dict, List, Callable
from datetime import datetime, timedelta
from ..core.manifest import ManifestManager
from ..core.sync import SyncEngine
from ..core.redundancy import RedundancyManager
from ..core.lifecycle import LifecycleManager


class AutoSyncDaemon:
    """
    Background daemon for automatic file synchronization and monitoring.

    Features:
    - Periodic redundancy validation
    - Automatic lifecycle policy application
    - Background file verification
    - Watch folder monitoring (future)
    """

    def __init__(self, manifest: ManifestManager, sync: SyncEngine,
                 redundancy: RedundancyManager, lifecycle: LifecycleManager):
        """
        Initialize auto-sync daemon.

        Args:
            manifest: Manifest manager
            sync: Sync engine
            redundancy: Redundancy manager
            lifecycle: Lifecycle manager
        """
        self.manifest = manifest
        self.sync = sync
        self.redundancy = redundancy
        self.lifecycle = lifecycle

        self.running = False
        self.thread: Optional[threading.Thread] = None

        # Configuration
        self.validation_interval = 3600  # 1 hour
        self.lifecycle_interval = 3600 * 24  # 24 hours
        self.verification_interval = 3600 * 24 * 7  # 7 days

        # Tracking
        self.last_validation = None
        self.last_lifecycle = None
        self.last_verification = None

        # Callbacks
        self.status_callback: Optional[Callable] = None
        self.notification_callback: Optional[Callable] = None

    def start(self):
        """Start the auto-sync daemon."""
        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

        self._notify("Auto-sync daemon started")

    def stop(self):
        """Stop the auto-sync daemon."""
        if not self.running:
            return

        self.running = False
        if self.thread:
            self.thread.join(timeout=5)

        self._notify("Auto-sync daemon stopped")

    def _run(self):
        """Main daemon loop."""
        while self.running:
            try:
                # Check if it's time for validation
                if self._should_validate():
                    self._update_status("Running redundancy validation...")
                    self._run_validation()

                # Check if it's time for lifecycle policies
                if self._should_run_lifecycle():
                    self._update_status("Applying lifecycle policies...")
                    self._run_lifecycle()

                # Check if it's time for verification
                if self._should_verify():
                    self._update_status("Verifying file integrity...")
                    self._run_verification()

                # Sleep
                self._update_status("Idle")
                time.sleep(60)  # Check every minute

            except Exception as e:
                print(f"Auto-sync daemon error: {e}")
                time.sleep(60)

    def _should_validate(self) -> bool:
        """Check if it's time to run validation."""
        if not self.last_validation:
            return True

        elapsed = (datetime.now() - self.last_validation).total_seconds()
        return elapsed >= self.validation_interval

    def _should_run_lifecycle(self) -> bool:
        """Check if it's time to run lifecycle policies."""
        if not self.last_lifecycle:
            return True

        elapsed = (datetime.now() - self.last_lifecycle).total_seconds()
        return elapsed >= self.lifecycle_interval

    def _should_verify(self) -> bool:
        """Check if it's time to run verification."""
        if not self.last_verification:
            return True

        elapsed = (datetime.now() - self.last_verification).total_seconds()
        return elapsed >= self.verification_interval

    def _run_validation(self):
        """Run redundancy validation."""
        try:
            entries = self.manifest.get_all_entries()
            report = self.redundancy.generate_redundancy_report(entries)

            self.last_validation = datetime.now()

            # Notify if issues found
            if report['non_compliant'] > 0:
                self._notify(
                    f"Found {report['non_compliant']} non-compliant files",
                    f"{report['non_compliant']} files need attention"
                )

            if report['critical_issues']:
                self._notify(
                    "Critical redundancy issues!",
                    f"{len(report['critical_issues'])} critical files at risk",
                    urgent=True
                )

        except Exception as e:
            print(f"Validation error: {e}")

    def _run_lifecycle(self):
        """Run lifecycle policies."""
        try:
            entries = self.manifest.get_all_entries()
            report = self.lifecycle.apply_policies(entries, dry_run=False)

            self.last_lifecycle = datetime.now()

            # Notify if changes made
            if report['entries_modified'] > 0:
                self._notify(
                    "Lifecycle policies applied",
                    f"Modified {report['entries_modified']} files"
                )

        except Exception as e:
            print(f"Lifecycle error: {e}")

    def _run_verification(self):
        """Run file verification."""
        try:
            report = self.sync.verify_all_locations()

            self.last_verification = datetime.now()

            # Notify if failures found
            if report['failed'] > 0:
                self._notify(
                    "Verification issues found",
                    f"{report['failed']} locations failed verification",
                    urgent=True
                )

        except Exception as e:
            print(f"Verification error: {e}")

    def _update_status(self, message: str):
        """Update status via callback."""
        if self.status_callback:
            self.status_callback(message)

    def _notify(self, title: str, message: str = "", urgent: bool = False):
        """Send notification via callback."""
        if self.notification_callback:
            self.notification_callback(title, message, urgent)

    def set_status_callback(self, callback: Callable):
        """Set callback for status updates."""
        self.status_callback = callback

    def set_notification_callback(self, callback: Callable):
        """Set callback for notifications."""
        self.notification_callback = callback

    def get_status(self) -> Dict:
        """Get current daemon status."""
        return {
            "running": self.running,
            "last_validation": self.last_validation,
            "last_lifecycle": self.last_lifecycle,
            "last_verification": self.last_verification,
            "validation_interval": self.validation_interval,
            "lifecycle_interval": self.lifecycle_interval,
            "verification_interval": self.verification_interval,
        }

    def configure(self, validation_interval: Optional[int] = None,
                 lifecycle_interval: Optional[int] = None,
                 verification_interval: Optional[int] = None):
        """
        Configure daemon intervals.

        Args:
            validation_interval: Seconds between validations
            lifecycle_interval: Seconds between lifecycle runs
            verification_interval: Seconds between verifications
        """
        if validation_interval is not None:
            self.validation_interval = validation_interval

        if lifecycle_interval is not None:
            self.lifecycle_interval = lifecycle_interval

        if verification_interval is not None:
            self.verification_interval = verification_interval


class WatchFolder:
    """
    Monitor a folder for new files and automatically add them.

    Future feature - not implemented yet.
    """

    def __init__(self, path: Path, sync: SyncEngine):
        """Initialize watch folder."""
        self.path = path
        self.sync = sync
        self.running = False

    def start(self):
        """Start watching folder."""
        # TODO: Implement file system watching
        # Use watchdog library: pip install watchdog
        pass

    def stop(self):
        """Stop watching folder."""
        pass
