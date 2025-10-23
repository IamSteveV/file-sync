"""Keyboard shortcuts for the GUI."""

import customtkinter as ctk


class KeyboardShortcuts:
    """Manages keyboard shortcuts for the application."""

    def __init__(self, app):
        """
        Initialize keyboard shortcuts.

        Args:
            app: The main FileSyncApp instance
        """
        self.app = app
        self._setup_shortcuts()

    def _setup_shortcuts(self):
        """Setup all keyboard shortcuts."""
        # Navigation shortcuts
        self.app.bind("<Control-1>", lambda e: self.app.show_dashboard())
        self.app.bind("<Control-2>", lambda e: self.app.show_files())
        self.app.bind("<Control-3>", lambda e: self.app.show_validation())
        self.app.bind("<Control-4>", lambda e: self.app.show_providers())
        self.app.bind("<Control-5>", lambda e: self.app.show_settings())

        # Alt key navigation (macOS-friendly)
        self.app.bind("<Alt-d>", lambda e: self.app.show_dashboard())
        self.app.bind("<Alt-f>", lambda e: self.app.show_files())
        self.app.bind("<Alt-v>", lambda e: self.app.show_validation())
        self.app.bind("<Alt-p>", lambda e: self.app.show_providers())
        self.app.bind("<Alt-s>", lambda e: self.app.show_settings())

        # File operations
        self.app.bind("<Control-n>", lambda e: self._add_file())
        self.app.bind("<Control-r>", lambda e: self._refresh())
        self.app.bind("<Control-f>", lambda e: self._focus_search())

        # Application shortcuts
        self.app.bind("<Control-q>", lambda e: self._quit())
        self.app.bind("<Control-w>", lambda e: self._quit())
        self.app.bind("<F5>", lambda e: self._refresh_all())
        self.app.bind("<F1>", lambda e: self._show_help())

        # Escape to unfocus
        self.app.bind("<Escape>", lambda e: self.app.focus())

    def _add_file(self):
        """Shortcut to add a new file."""
        # Switch to files view and trigger add
        self.app.show_files()
        # Try to trigger the add file dialog if files view exists
        try:
            if hasattr(self.app, 'main_frame'):
                for widget in self.app.main_frame.winfo_children():
                    if hasattr(widget, '_add_file_dialog'):
                        widget._add_file_dialog()
                        break
        except:
            pass

    def _refresh(self):
        """Refresh current view."""
        try:
            for widget in self.app.main_frame.winfo_children():
                if hasattr(widget, 'refresh'):
                    widget.refresh()
                elif hasattr(widget, '_load_files'):
                    widget._load_files()
                elif hasattr(widget, '_load_validation'):
                    widget._load_validation()
                break
        except:
            pass

    def _focus_search(self):
        """Focus the search box if in files view."""
        try:
            for widget in self.app.main_frame.winfo_children():
                if hasattr(widget, 'search_entry'):
                    widget.search_entry.focus()
                    break
        except:
            pass

    def _refresh_all(self):
        """Refresh everything."""
        self.app.reload_components()

    def _show_help(self):
        """Show keyboard shortcuts help."""
        from tkinter import messagebox
        help_text = """
Keyboard Shortcuts:

Navigation:
  Ctrl+1 / Alt+D   - Dashboard
  Ctrl+2 / Alt+F   - Files
  Ctrl+3 / Alt+V   - Validation
  Ctrl+4 / Alt+P   - Providers
  Ctrl+5 / Alt+S   - Settings

File Operations:
  Ctrl+N           - Add New File
  Ctrl+F           - Focus Search
  Ctrl+R           - Refresh Current View
  F5               - Refresh Everything

Application:
  F1               - Show This Help
  Ctrl+Q / Ctrl+W  - Quit Application
  Esc              - Clear Focus
"""
        messagebox.showinfo("Keyboard Shortcuts", help_text, parent=self.app)

    def _quit(self):
        """Quit the application."""
        from tkinter import messagebox
        if messagebox.askyesno(
            "Quit FileSync",
            "Are you sure you want to quit?",
            parent=self.app
        ):
            self.app.quit()


def setup_shortcuts(app):
    """
    Setup keyboard shortcuts for the application.

    Args:
        app: The main FileSyncApp instance

    Returns:
        KeyboardShortcuts instance
    """
    return KeyboardShortcuts(app)
