"""Desktop notifications for FileSync."""

import platform
from typing import Optional

try:
    from plyer import notification as plyer_notify
    PLYER_AVAILABLE = True
except ImportError:
    PLYER_AVAILABLE = False
    print("Warning: plyer not installed. Desktop notifications disabled.")
    print("Install with: pip install plyer")


class DesktopNotifier:
    """Cross-platform desktop notifications."""

    def __init__(self, app_name: str = "FileSync"):
        """
        Initialize desktop notifier.

        Args:
            app_name: Name of the application for notifications
        """
        self.app_name = app_name
        self.enabled = True

    def notify(self, title: str, message: str, timeout: int = 5,
               urgency: str = "normal"):
        """
        Show a desktop notification.

        Args:
            title: Notification title
            message: Notification message
            timeout: How long to show notification (seconds)
            urgency: Urgency level: "low", "normal", "critical"
        """
        if not self.enabled or not PLYER_AVAILABLE:
            return

        try:
            plyer_notify.notify(
                title=title,
                message=message,
                app_name=self.app_name,
                timeout=timeout
            )
        except Exception as e:
            print(f"Notification error: {e}")

    def notify_success(self, title: str, message: str):
        """Show a success notification."""
        self.notify(f"✓ {title}", message, urgency="low")

    def notify_info(self, title: str, message: str):
        """Show an info notification."""
        self.notify(f"ℹ {title}", message, urgency="normal")

    def notify_warning(self, title: str, message: str):
        """Show a warning notification."""
        self.notify(f"⚠ {title}", message, timeout=10, urgency="normal")

    def notify_error(self, title: str, message: str):
        """Show an error notification."""
        self.notify(f"❌ {title}", message, timeout=15, urgency="critical")

    def notify_file_added(self, filename: str, tier: str):
        """Notify when a file is added."""
        self.notify_success(
            "File Added",
            f"{filename} added as {tier}"
        )

    def notify_sync_complete(self, count: int):
        """Notify when sync is complete."""
        self.notify_success(
            "Sync Complete",
            f"Synced {count} file{'s' if count != 1 else ''}"
        )

    def notify_redundancy_issue(self, count: int):
        """Notify about redundancy issues."""
        self.notify_warning(
            "Redundancy Issues",
            f"{count} file{'s' if count != 1 else ''} need attention"
        )

    def notify_critical_issue(self, message: str):
        """Notify about critical issues."""
        self.notify_error(
            "Critical Issue",
            message
        )

    def set_enabled(self, enabled: bool):
        """Enable or disable notifications."""
        self.enabled = enabled


# Global notifier instance
_notifier: Optional[DesktopNotifier] = None


def get_notifier() -> DesktopNotifier:
    """Get the global notifier instance."""
    global _notifier
    if _notifier is None:
        _notifier = DesktopNotifier()
    return _notifier


def notify(title: str, message: str, **kwargs):
    """Show a notification using the global notifier."""
    get_notifier().notify(title, message, **kwargs)


def notify_success(title: str, message: str):
    """Show a success notification."""
    get_notifier().notify_success(title, message)


def notify_error(title: str, message: str):
    """Show an error notification."""
    get_notifier().notify_error(title, message)


def notify_warning(title: str, message: str):
    """Show a warning notification."""
    get_notifier().notify_warning(title, message)
