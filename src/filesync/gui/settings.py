"""Settings and configuration view."""

import customtkinter as ctk
from tkinter import messagebox, filedialog
from pathlib import Path
from ..core.manifest import ManifestManager
from ..providers.local import LocalProvider
from ..watcher.file_watcher import FolderWatchManager, AutoImportConfig
from ..notifications.desktop import get_notifier
from .watch_folder_dialog import WatchFolderDialog


class SettingsFrame(ctk.CTkFrame):
    """Settings and configuration interface."""

    def __init__(self, parent, manifest_path: Path, app):
        super().__init__(parent)
        self.manifest_path = manifest_path
        self.app = app

        # Auto-import components
        config_path = manifest_path.parent / "auto_import_config.json"
        self.auto_import_config = AutoImportConfig(config_path)
        self.watch_manager = FolderWatchManager()
        self.notifier = get_notifier()

        # Load existing watches
        self._load_watched_folders()

        self.grid_columnconfigure(0, weight=1)

        self._create_widgets()

    def _create_widgets(self):
        """Create widgets."""
        # Title
        title = ctk.CTkLabel(
            self,
            text="Settings",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title.grid(row=0, column=0, sticky="w", pady=(0, 30))

        # Initialization section
        self._create_init_section()

        # Paths section
        self._create_paths_section()

        # Auto-import section
        self._create_auto_import_section()

        # Notifications section
        self._create_notifications_section()

        # Encryption section
        self._create_encryption_section()

        # About section
        self._create_about_section()

    def _create_init_section(self):
        """Create initialization section."""
        init_frame = ctk.CTkFrame(self)
        init_frame.grid(row=1, column=0, sticky="ew", pady=(0, 20))

        ctk.CTkLabel(
            init_frame,
            text="Initialization",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(anchor="w", padx=20, pady=(20, 10))

        if self.manifest_path.exists():
            status_text = f"✓ FileSync is initialized\nManifest: {self.manifest_path}"
            status_color = "green"
        else:
            status_text = "✗ FileSync is not initialized"
            status_color = "red"

        ctk.CTkLabel(
            init_frame,
            text=status_text,
            font=ctk.CTkFont(size=12),
            text_color=status_color
        ).pack(anchor="w", padx=20, pady=10)

        if not self.manifest_path.exists():
            ctk.CTkButton(
                init_frame,
                text="Initialize FileSync",
                command=self._initialize,
                height=40
            ).pack(anchor="w", padx=20, pady=(10, 20))
        else:
            btn_frame = ctk.CTkFrame(init_frame, fg_color="transparent")
            btn_frame.pack(anchor="w", padx=20, pady=(10, 20))

            ctk.CTkButton(
                btn_frame,
                text="Export Manifest",
                command=self._export_manifest,
                height=35,
                width=150
            ).pack(side="left", padx=(0, 10))

            ctk.CTkButton(
                btn_frame,
                text="Import Manifest",
                command=self._import_manifest,
                height=35,
                width=150,
                fg_color="gray40",
                hover_color="gray50"
            ).pack(side="left")

    def _create_paths_section(self):
        """Create paths configuration section."""
        paths_frame = ctk.CTkFrame(self)
        paths_frame.grid(row=2, column=0, sticky="ew", pady=(0, 20))

        ctk.CTkLabel(
            paths_frame,
            text="Paths",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(anchor="w", padx=20, pady=(20, 10))

        # Manifest path
        self._add_path_row(
            paths_frame,
            "Manifest Database",
            str(self.manifest_path)
        )

        # Cache path
        cache_path = self.manifest_path.parent / "cache"
        self._add_path_row(paths_frame, "Cache Directory", str(cache_path))

        # Offline storage
        offline_path = self.manifest_path.parent.parent / "filesync-offline"
        self._add_path_row(paths_frame, "Offline Storage", str(offline_path))

    def _create_auto_import_section(self):
        """Create auto-import configuration section."""
        import_frame = ctk.CTkFrame(self)
        import_frame.grid(row=3, column=0, sticky="ew", pady=(0, 20))

        ctk.CTkLabel(
            import_frame,
            text="Auto-Import from Folders",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(anchor="w", padx=20, pady=(20, 10))

        info = ctk.CTkLabel(
            import_frame,
            text="FileSync can automatically watch folders and import new files as they are added.",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        info.pack(anchor="w", padx=20, pady=(0, 15))

        # Watched folders list
        list_frame = ctk.CTkFrame(import_frame, fg_color="gray25")
        list_frame.pack(fill="both", expand=True, padx=20, pady=(0, 15))

        ctk.CTkLabel(
            list_frame,
            text="Watched Folders:",
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(anchor="w", padx=15, pady=(15, 10))

        # Scrollable list of watched folders
        self.watched_folders_list = ctk.CTkScrollableFrame(
            list_frame,
            height=150,
            fg_color="gray20"
        )
        self.watched_folders_list.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        self._refresh_watched_folders_list()

        # Buttons
        btn_frame = ctk.CTkFrame(import_frame, fg_color="transparent")
        btn_frame.pack(anchor="w", padx=20, pady=(0, 20))

        ctk.CTkButton(
            btn_frame,
            text="+ Add Folder",
            command=self._add_watched_folder,
            height=35,
            width=140
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            btn_frame,
            text="Remove All",
            command=self._remove_all_watched_folders,
            height=35,
            width=140,
            fg_color="gray40",
            hover_color="gray50"
        ).pack(side="left")

    def _create_notifications_section(self):
        """Create notifications configuration section."""
        notif_frame = ctk.CTkFrame(self)
        notif_frame.grid(row=4, column=0, sticky="ew", pady=(0, 20))

        ctk.CTkLabel(
            notif_frame,
            text="Desktop Notifications",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(anchor="w", padx=20, pady=(20, 10))

        info = ctk.CTkLabel(
            notif_frame,
            text="FileSync can show desktop notifications for important events.",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        info.pack(anchor="w", padx=20, pady=(0, 15))

        # Enable/disable notifications
        self.notifications_enabled = ctk.CTkSwitch(
            notif_frame,
            text="Enable desktop notifications",
            command=self._toggle_notifications,
            font=ctk.CTkFont(size=13)
        )
        self.notifications_enabled.pack(anchor="w", padx=20, pady=(0, 10))

        # Set initial state
        if self.notifier.enabled:
            self.notifications_enabled.select()

        # Test notification button
        ctk.CTkButton(
            notif_frame,
            text="Test Notification",
            command=self._test_notification,
            height=35,
            width=160,
            fg_color="gray40",
            hover_color="gray50"
        ).pack(anchor="w", padx=20, pady=(10, 20))

    def _create_encryption_section(self):
        """Create encryption configuration section."""
        encrypt_frame = ctk.CTkFrame(self)
        encrypt_frame.grid(row=5, column=0, sticky="ew", pady=(0, 20))

        ctk.CTkLabel(
            encrypt_frame,
            text="Encryption",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(anchor="w", padx=20, pady=(20, 10))

        info = ctk.CTkLabel(
            encrypt_frame,
            text="FileSync uses AES-256-GCM encryption with PBKDF2 key derivation.\n"
                 "Encryption passphrase is required for Tier 0 (Critical) files.",
            font=ctk.CTkFont(size=12),
            justify="left"
        )
        info.pack(anchor="w", padx=20, pady=(0, 20))

    def _create_about_section(self):
        """Create about section."""
        about_frame = ctk.CTkFrame(self)
        about_frame.grid(row=6, column=0, sticky="ew")

        ctk.CTkLabel(
            about_frame,
            text="About FileSync",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(anchor="w", padx=20, pady=(20, 10))

        about_text = """FileSync v0.1.0
Cloud Storage Deduplication System

A cross-platform file synchronization and deduplication system with
importance-based tiering and client-side encryption.

© 2025 FileSync Team
Licensed under MIT License"""

        ctk.CTkLabel(
            about_frame,
            text=about_text,
            font=ctk.CTkFont(size=12),
            justify="left"
        ).pack(anchor="w", padx=20, pady=(0, 20))

    def _add_path_row(self, parent, label: str, path: str):
        """Add a path display row."""
        row_frame = ctk.CTkFrame(parent, fg_color="transparent")
        row_frame.pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(
            row_frame,
            text=f"{label}:",
            font=ctk.CTkFont(size=12, weight="bold"),
            width=150,
            anchor="w"
        ).pack(side="left")

        ctk.CTkLabel(
            row_frame,
            text=path,
            font=ctk.CTkFont(size=11),
            anchor="w",
            text_color="gray"
        ).pack(side="left", fill="x", expand=True)

    def _initialize(self):
        """Initialize FileSync."""
        try:
            # Create directories
            self.manifest_path.parent.mkdir(parents=True, exist_ok=True)

            local_path = self.manifest_path.parent.parent / "filesync-offline"
            local_path.mkdir(parents=True, exist_ok=True)

            # Initialize manifest
            manifest = ManifestManager(self.manifest_path)
            manifest.close()

            # Initialize local provider
            LocalProvider(local_path)

            messagebox.showinfo(
                "Success",
                f"FileSync initialized successfully!\n\n"
                f"Manifest: {self.manifest_path}\n"
                f"Offline storage: {local_path}",
                parent=self
            )

            # Reload app
            self.app.reload_components()

        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Failed to initialize FileSync:\n{str(e)}",
                parent=self
            )

    def _export_manifest(self):
        """Export manifest to JSON."""
        try:
            from tkinter import filedialog

            output_path = filedialog.asksaveasfilename(
                title="Export Manifest",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                parent=self
            )

            if output_path:
                with ManifestManager(self.manifest_path) as manifest:
                    manifest.export_to_json(output_path)

                messagebox.showinfo(
                    "Success",
                    f"Manifest exported to:\n{output_path}",
                    parent=self
                )

        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Failed to export manifest:\n{str(e)}",
                parent=self
            )

    def _import_manifest(self):
        """Import manifest from JSON."""
        try:
            from tkinter import filedialog

            input_path = filedialog.askopenfilename(
                title="Import Manifest",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                parent=self
            )

            if input_path:
                with ManifestManager(self.manifest_path) as manifest:
                    count = manifest.import_from_json(input_path)

                messagebox.showinfo(
                    "Success",
                    f"Imported {count} entries from:\n{input_path}",
                    parent=self
                )

                # Reload app
                self.app.reload_components()

        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Failed to import manifest:\n{str(e)}",
                parent=self
            )

    def _load_watched_folders(self):
        """Load and start watching configured folders."""
        for folder_path, tier, recursive in self.auto_import_config.get_all_watches():
            self.watch_manager.add_watch(
                folder_path,
                lambda fp, t=tier: self._on_file_added(fp, t),
                recursive
            )

    def _refresh_watched_folders_list(self):
        """Refresh the watched folders display."""
        # Clear existing widgets
        for widget in self.watched_folders_list.winfo_children():
            widget.destroy()

        watches = self.auto_import_config.get_all_watches()

        if not watches:
            ctk.CTkLabel(
                self.watched_folders_list,
                text="No folders being watched",
                text_color="gray",
                font=ctk.CTkFont(size=12)
            ).pack(pady=20)
        else:
            for folder_path, tier, recursive in watches:
                self._add_watched_folder_row(folder_path, tier, recursive)

    def _add_watched_folder_row(self, folder_path: Path, tier: int, recursive: bool):
        """Add a row showing a watched folder."""
        from ..models.tier import Tier

        row_frame = ctk.CTkFrame(self.watched_folders_list, fg_color="gray30")
        row_frame.pack(fill="x", pady=5, padx=5)

        # Folder path
        path_label = ctk.CTkLabel(
            row_frame,
            text=str(folder_path),
            font=ctk.CTkFont(size=12),
            anchor="w"
        )
        path_label.pack(side="left", fill="x", expand=True, padx=10, pady=8)

        # Tier badge
        tier_text = f"Tier {tier}"
        tier_label = ctk.CTkLabel(
            row_frame,
            text=tier_text,
            font=ctk.CTkFont(size=11),
            width=70,
            fg_color="gray40",
            corner_radius=5
        )
        tier_label.pack(side="left", padx=5)

        # Recursive badge
        if recursive:
            rec_label = ctk.CTkLabel(
                row_frame,
                text="Recursive",
                font=ctk.CTkFont(size=11),
                width=80,
                fg_color="blue",
                corner_radius=5
            )
            rec_label.pack(side="left", padx=5)

        # Remove button
        remove_btn = ctk.CTkButton(
            row_frame,
            text="✕",
            width=30,
            height=30,
            command=lambda: self._remove_watched_folder(folder_path),
            fg_color="red",
            hover_color="darkred"
        )
        remove_btn.pack(side="left", padx=5)

    def _add_watched_folder(self):
        """Add a folder to watch."""
        folder_path = filedialog.askdirectory(
            title="Select Folder to Watch",
            parent=self
        )

        if not folder_path:
            return

        folder_path = Path(folder_path)

        # Show configuration dialog
        dialog = WatchFolderDialog(self, folder_path)
        self.wait_window(dialog)

        if hasattr(dialog, 'tier') and dialog.tier is not None:
            tier = dialog.tier
            recursive = dialog.recursive

            # Add to configuration
            self.auto_import_config.add_watch(folder_path, tier, recursive)

            # Start watching
            self.watch_manager.add_watch(
                folder_path,
                lambda fp: self._on_file_added(fp, tier),
                recursive
            )

            # Refresh display
            self._refresh_watched_folders_list()

            self.notifier.notify_success(
                "Folder Added",
                f"Now watching: {folder_path.name}"
            )

    def _remove_watched_folder(self, folder_path: Path):
        """Remove a watched folder."""
        self.watch_manager.remove_watch(folder_path)
        self.auto_import_config.remove_watch(folder_path)
        self._refresh_watched_folders_list()

        self.notifier.notify(
            "Folder Removed",
            f"Stopped watching: {folder_path.name}"
        )

    def _remove_all_watched_folders(self):
        """Remove all watched folders."""
        if not self.auto_import_config.get_all_watches():
            return

        result = messagebox.askyesno(
            "Confirm",
            "Remove all watched folders?",
            parent=self
        )

        if result:
            self.watch_manager.stop_all()
            self.auto_import_config.clear_all()
            self._refresh_watched_folders_list()

            self.notifier.notify(
                "Folders Cleared",
                "All watched folders removed"
            )

    def _on_file_added(self, file_path: Path, tier: int):
        """Handle file added to watched folder."""
        try:
            # This would integrate with the file addition logic
            # For now, just show notification
            self.notifier.notify_file_added(file_path.name, f"Tier {tier}")

            # In a real implementation, this would call the sync engine
            # to add the file to the manifest
            # self.app.sync_engine.add_file(file_path, tier=tier)

        except Exception as e:
            self.notifier.notify_error(
                "Auto-Import Failed",
                f"Failed to import {file_path.name}: {str(e)}"
            )

    def _toggle_notifications(self):
        """Toggle notifications on/off."""
        enabled = self.notifications_enabled.get()
        self.notifier.set_enabled(enabled)

        if enabled:
            self.notifier.notify(
                "Notifications Enabled",
                "Desktop notifications are now enabled"
            )

    def _test_notification(self):
        """Test notification functionality."""
        self.notifier.notify(
            "FileSync Test",
            "Notifications are working correctly!"
        )
