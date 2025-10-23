"""Main GUI application for FileSync."""

import customtkinter as ctk
from pathlib import Path
from typing import Optional
from .dashboard import DashboardFrame
from .files import FilesFrame
from .settings import SettingsFrame
from .providers import ProvidersFrame
from .validation import ValidationFrame
from ..core.manifest import ManifestManager
from ..providers.local import LocalProvider
from ..core.sync import SyncEngine
from ..core.redundancy import RedundancyManager
from ..core.lifecycle import LifecycleManager


class FileSyncApp(ctk.CTk):
    """Main FileSync GUI application."""

    def __init__(self):
        super().__init__()

        # Configure window
        self.title("FileSync - Cloud Storage Deduplication")
        self.geometry("1200x700")

        # Set theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Initialize state
        self.manifest_path = Path.home() / ".filesync" / "manifest.db"
        self.manifest: Optional[ManifestManager] = None
        self.providers = {}
        self.sync: Optional[SyncEngine] = None
        self.redundancy: Optional[RedundancyManager] = None
        self.lifecycle: Optional[LifecycleManager] = None

        # Initialize components if manifest exists
        self._initialize_components()

        # Create UI
        self._create_sidebar()
        self._create_main_content()

        # Show dashboard by default
        self.show_dashboard()

    def _initialize_components(self):
        """Initialize FileSync components."""
        if self.manifest_path.exists():
            self.manifest = ManifestManager(self.manifest_path)

            # Initialize local provider
            local_path = self.manifest_path.parent.parent / "filesync-offline"
            self.providers["local"] = LocalProvider(local_path)

            # Initialize engines
            self.sync = SyncEngine(self.manifest, self.providers)
            self.redundancy = RedundancyManager()
            self.lifecycle = LifecycleManager()

    def _create_sidebar(self):
        """Create the navigation sidebar."""
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsw")
        self.sidebar.grid_rowconfigure(6, weight=1)

        # Logo/Title
        self.logo_label = ctk.CTkLabel(
            self.sidebar,
            text="FileSync",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 30))

        # Navigation buttons
        self.nav_buttons = {}

        self.nav_buttons["dashboard"] = ctk.CTkButton(
            self.sidebar,
            text="📊 Dashboard",
            command=self.show_dashboard,
            height=40,
            font=ctk.CTkFont(size=14)
        )
        self.nav_buttons["dashboard"].grid(row=1, column=0, padx=20, pady=10)

        self.nav_buttons["files"] = ctk.CTkButton(
            self.sidebar,
            text="📁 Files",
            command=self.show_files,
            height=40,
            font=ctk.CTkFont(size=14)
        )
        self.nav_buttons["files"].grid(row=2, column=0, padx=20, pady=10)

        self.nav_buttons["validation"] = ctk.CTkButton(
            self.sidebar,
            text="✓ Validation",
            command=self.show_validation,
            height=40,
            font=ctk.CTkFont(size=14)
        )
        self.nav_buttons["validation"].grid(row=3, column=0, padx=20, pady=10)

        self.nav_buttons["providers"] = ctk.CTkButton(
            self.sidebar,
            text="☁️ Providers",
            command=self.show_providers,
            height=40,
            font=ctk.CTkFont(size=14)
        )
        self.nav_buttons["providers"].grid(row=4, column=0, padx=20, pady=10)

        self.nav_buttons["settings"] = ctk.CTkButton(
            self.sidebar,
            text="⚙️ Settings",
            command=self.show_settings,
            height=40,
            font=ctk.CTkFont(size=14)
        )
        self.nav_buttons["settings"].grid(row=5, column=0, padx=20, pady=10)

        # Status label at bottom
        self.status_label = ctk.CTkLabel(
            self.sidebar,
            text="Ready",
            font=ctk.CTkFont(size=12)
        )
        self.status_label.grid(row=7, column=0, padx=20, pady=(0, 20))

    def _create_main_content(self):
        """Create the main content area."""
        self.main_frame = ctk.CTkFrame(self, corner_radius=0)
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        # Configure grid weights
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

    def _highlight_nav_button(self, active_button: str):
        """Highlight the active navigation button."""
        for name, button in self.nav_buttons.items():
            if name == active_button:
                button.configure(fg_color=("gray75", "gray25"))
            else:
                button.configure(fg_color=("gray85", "gray20"))

    def _clear_main_content(self):
        """Clear the main content area."""
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def show_dashboard(self):
        """Show the dashboard view."""
        self._clear_main_content()
        self._highlight_nav_button("dashboard")

        if self.manifest:
            dashboard = DashboardFrame(
                self.main_frame,
                self.manifest,
                self.redundancy,
                self.lifecycle
            )
            dashboard.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        else:
            self._show_welcome_screen()

    def show_files(self):
        """Show the files management view."""
        self._clear_main_content()
        self._highlight_nav_button("files")

        if self.manifest:
            files = FilesFrame(
                self.main_frame,
                self.manifest,
                self.sync,
                self
            )
            files.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        else:
            self._show_welcome_screen()

    def show_validation(self):
        """Show the validation view."""
        self._clear_main_content()
        self._highlight_nav_button("validation")

        if self.manifest:
            validation = ValidationFrame(
                self.main_frame,
                self.manifest,
                self.redundancy,
                self.sync
            )
            validation.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        else:
            self._show_welcome_screen()

    def show_providers(self):
        """Show the providers configuration view."""
        self._clear_main_content()
        self._highlight_nav_button("providers")

        providers = ProvidersFrame(
            self.main_frame,
            self.providers,
            self
        )
        providers.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)

    def show_settings(self):
        """Show the settings view."""
        self._clear_main_content()
        self._highlight_nav_button("settings")

        settings = SettingsFrame(
            self.main_frame,
            self.manifest_path,
            self
        )
        settings.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)

    def _show_welcome_screen(self):
        """Show welcome screen when not initialized."""
        welcome = ctk.CTkFrame(self.main_frame)
        welcome.grid(row=0, column=0, sticky="nsew", padx=100, pady=100)

        title = ctk.CTkLabel(
            welcome,
            text="Welcome to FileSync",
            font=ctk.CTkFont(size=32, weight="bold")
        )
        title.pack(pady=(40, 20))

        subtitle = ctk.CTkLabel(
            welcome,
            text="Cloud Storage Deduplication System",
            font=ctk.CTkFont(size=18)
        )
        subtitle.pack(pady=(0, 40))

        info = ctk.CTkLabel(
            welcome,
            text="FileSync is not initialized.\nPlease initialize it from Settings.",
            font=ctk.CTkFont(size=14)
        )
        info.pack(pady=20)

        init_btn = ctk.CTkButton(
            welcome,
            text="Go to Settings",
            command=self.show_settings,
            height=40,
            font=ctk.CTkFont(size=16)
        )
        init_btn.pack(pady=20)

    def set_status(self, message: str):
        """Update the status message."""
        self.status_label.configure(text=message)
        self.update()

    def reload_components(self):
        """Reload components after initialization."""
        self._initialize_components()
        self.show_dashboard()

    def run(self):
        """Start the application."""
        self.mainloop()


def main():
    """Entry point for the GUI application."""
    app = FileSyncApp()
    app.run()


if __name__ == "__main__":
    main()
