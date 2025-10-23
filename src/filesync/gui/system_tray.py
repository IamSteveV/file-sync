"""System tray integration for FileSync."""

import sys
from pathlib import Path

try:
    from pystray import Icon, Menu, MenuItem
    from PIL import Image, ImageDraw
    PYSTRAY_AVAILABLE = True
except ImportError:
    PYSTRAY_AVAILABLE = False
    print("Warning: pystray not installed. System tray functionality disabled.")
    print("Install with: pip install pystray pillow")


class SystemTray:
    """System tray icon and menu for FileSync."""

    def __init__(self, app):
        """
        Initialize system tray.

        Args:
            app: The main FileSyncApp instance
        """
        self.app = app
        self.icon = None
        self.running = False

        if not PYSTRAY_AVAILABLE:
            return

        # Create icon image
        self.image = self._create_icon_image()

        # Create menu
        self.menu = Menu(
            MenuItem("Show FileSync", self._show_window, default=True),
            MenuItem("Dashboard", self._show_dashboard),
            MenuItem("Files", self._show_files),
            MenuItem("Validation", self._show_validation),
            Menu.SEPARATOR,
            MenuItem("Settings", self._show_settings),
            Menu.SEPARATOR,
            MenuItem("Quit", self._quit)
        )

        # Create icon
        self.icon = Icon(
            "FileSync",
            self.image,
            "FileSync - Cloud Storage Deduplication",
            self.menu
        )

    def _create_icon_image(self):
        """Create system tray icon image."""
        # Create a simple icon - blue circle with F
        width = 64
        height = 64

        image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)

        # Draw blue circle
        draw.ellipse([8, 8, 56, 56], fill='#1f6aa5', outline='white', width=2)

        # Draw 'F' letter
        draw.text((22, 16), 'F', fill='white', font=None)

        return image

    def start(self):
        """Start the system tray icon."""
        if not PYSTRAY_AVAILABLE or not self.icon:
            return

        self.running = True
        # Run icon in a separate thread
        import threading
        self.tray_thread = threading.Thread(target=self.icon.run, daemon=True)
        self.tray_thread.start()

    def stop(self):
        """Stop the system tray icon."""
        if self.icon and self.running:
            self.icon.stop()
            self.running = False

    def _show_window(self):
        """Show the main window."""
        self.app.after(0, self._restore_window)

    def _restore_window(self):
        """Restore window from minimized/hidden state."""
        self.app.deiconify()
        self.app.lift()
        self.app.focus_force()

    def _show_dashboard(self):
        """Show dashboard view."""
        self.app.after(0, lambda: (self._restore_window(), self.app.show_dashboard()))

    def _show_files(self):
        """Show files view."""
        self.app.after(0, lambda: (self._restore_window(), self.app.show_files()))

    def _show_validation(self):
        """Show validation view."""
        self.app.after(0, lambda: (self._restore_window(), self.app.show_validation()))

    def _show_settings(self):
        """Show settings view."""
        self.app.after(0, lambda: (self._restore_window(), self.app.show_settings()))

    def _quit(self):
        """Quit the application."""
        self.app.after(0, self.app.quit)

    def update_status(self, message: str):
        """Update the tray icon tooltip."""
        if self.icon and PYSTRAY_AVAILABLE:
            self.icon.title = f"FileSync - {message}"

    def show_notification(self, title: str, message: str):
        """Show a system notification."""
        if self.icon and PYSTRAY_AVAILABLE:
            self.icon.notify(message, title)


def setup_system_tray(app):
    """
    Setup system tray for the application.

    Args:
        app: The main FileSyncApp instance

    Returns:
        SystemTray instance or None if not available
    """
    if not PYSTRAY_AVAILABLE:
        return None

    tray = SystemTray(app)
    tray.start()
    return tray


def minimize_to_tray(app):
    """
    Configure app to minimize to system tray instead of taskbar.

    Args:
        app: The main FileSyncApp instance
    """
    def on_minimize(event=None):
        """Handle window minimize event."""
        app.withdraw()  # Hide window
        return "break"  # Prevent default minimize

    # Override window close to minimize instead
    app.protocol("WM_DELETE_WINDOW", on_minimize)

    # Bind iconify event
    app.bind("<Unmap>", on_minimize)
