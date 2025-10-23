"""Desktop notifications module."""

from .desktop import (
    DesktopNotifier,
    get_notifier,
    notify,
    notify_success,
    notify_error,
    notify_warning,
)

__all__ = [
    "DesktopNotifier",
    "get_notifier",
    "notify",
    "notify_success",
    "notify_error",
    "notify_warning",
]
