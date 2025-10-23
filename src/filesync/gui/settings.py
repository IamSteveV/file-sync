"""Settings and configuration view."""

import customtkinter as ctk
from tkinter import messagebox
from pathlib import Path
from ..core.manifest import ManifestManager
from ..providers.local import LocalProvider


class SettingsFrame(ctk.CTkFrame):
    """Settings and configuration interface."""

    def __init__(self, parent, manifest_path: Path, app):
        super().__init__(parent)
        self.manifest_path = manifest_path
        self.app = app

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

    def _create_encryption_section(self):
        """Create encryption configuration section."""
        encrypt_frame = ctk.CTkFrame(self)
        encrypt_frame.grid(row=3, column=0, sticky="ew", pady=(0, 20))

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
        about_frame.grid(row=4, column=0, sticky="ew")

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
