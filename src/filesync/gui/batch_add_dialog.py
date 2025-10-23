"""Batch file addition dialog for drag-and-drop support."""

import customtkinter as ctk
from tkinter import messagebox
from pathlib import Path
from typing import List
from ..core.manifest import ManifestManager
from ..core.sync import SyncEngine
from ..models.tier import Tier
from ..encryption.crypto import key_manager
from .dialogs import PassphraseDialog


class BatchAddDialog(ctk.CTkToplevel):
    """Dialog for adding multiple files at once."""

    def __init__(self, parent, files: List[Path], manifest: ManifestManager,
                 sync: SyncEngine, app):
        super().__init__(parent)
        self.files = files
        self.manifest = manifest
        self.sync = sync
        self.app = app

        self.title(f"Add {len(files)} Files")
        self.geometry("700x600")

        # Make modal
        self.transient(parent)
        self.grab_set()

        self._create_widgets()

    def _create_widgets(self):
        """Create dialog widgets."""
        # Title
        title = ctk.CTkLabel(
            self,
            text=f"Add {len(self.files)} Files",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.pack(pady=(20, 10))

        # File list
        list_frame = ctk.CTkFrame(self)
        list_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        ctk.CTkLabel(
            list_frame,
            text="Files to add:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=15, pady=(15, 10))

        file_list = ctk.CTkScrollableFrame(list_frame, height=200)
        file_list.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        for f in self.files:
            ctk.CTkLabel(
                file_list,
                text=f"📄 {f.name}",
                font=ctk.CTkFont(size=12),
                anchor="w"
            ).pack(anchor="w", pady=2)

        # Common settings
        settings_frame = ctk.CTkFrame(self)
        settings_frame.pack(fill="x", padx=20, pady=(0, 20))

        ctk.CTkLabel(
            settings_frame,
            text="Settings for all files:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=15, pady=(15, 10))

        # Tier
        tier_inner = ctk.CTkFrame(settings_frame, fg_color="transparent")
        tier_inner.pack(fill="x", padx=15, pady=5)

        ctk.CTkLabel(
            tier_inner,
            text="Tier:",
            width=100,
            anchor="w"
        ).pack(side="left")

        self.tier_var = ctk.StringVar(value="Standard")
        self.tier_menu = ctk.CTkOptionMenu(
            tier_inner,
            variable=self.tier_var,
            values=["Critical", "Important", "Standard", "Archive"],
            width=200
        )
        self.tier_menu.pack(side="left")

        # Tags
        tags_inner = ctk.CTkFrame(settings_frame, fg_color="transparent")
        tags_inner.pack(fill="x", padx=15, pady=5)

        ctk.CTkLabel(
            tags_inner,
            text="Tags:",
            width=100,
            anchor="w"
        ).pack(side="left")

        self.tags_entry = ctk.CTkEntry(
            tags_inner,
            placeholder_text="e.g., work, project, 2024"
        )
        self.tags_entry.pack(side="left", fill="x", expand=True)

        # Encryption
        self.encrypt_var = ctk.BooleanVar(value=False)
        encrypt_check = ctk.CTkCheckBox(
            settings_frame,
            text="Encrypt all files",
            variable=self.encrypt_var,
            font=ctk.CTkFont(size=12)
        )
        encrypt_check.pack(anchor="w", padx=15, pady=10)

        # Progress info
        self.progress_label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.progress_label.pack(pady=(0, 10))

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=20)

        ctk.CTkButton(
            btn_frame,
            text="Cancel",
            command=self.destroy,
            fg_color="gray40",
            hover_color="gray50",
            width=140,
            height=40
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            btn_frame,
            text="Add All Files",
            command=self._add_all_files,
            width=140,
            height=40
        ).pack(side="left", padx=10)

    def _add_all_files(self):
        """Add all files with common settings."""
        # Parse settings
        tier_name = self.tier_var.get().upper()
        tier = Tier[tier_name]

        tags_text = self.tags_entry.get().strip()
        tags = [t.strip() for t in tags_text.split(",")] if tags_text else []

        encrypt = self.encrypt_var.get()

        # Check encryption
        if encrypt or tier == Tier.CRITICAL:
            if not key_manager.has_passphrase():
                dialog = PassphraseDialog(self)
                dialog.wait_window()

                if not key_manager.has_passphrase():
                    messagebox.showerror(
                        "Error",
                        "Encryption passphrase required",
                        parent=self
                    )
                    return
            encrypt = True

        # Add files
        success_count = 0
        error_count = 0
        errors = []

        for i, file_path in enumerate(self.files):
            self.progress_label.configure(
                text=f"Adding file {i+1} of {len(self.files)}: {file_path.name}..."
            )
            self.update()

            try:
                success, entry, result = self.sync.add_file(
                    file_path,
                    tier,
                    tags,
                    None,
                    encrypt
                )

                if success:
                    success_count += 1
                else:
                    error_count += 1
                    errors.append(f"{file_path.name}: {result.errors[0]['error'] if result.errors else 'Unknown error'}")

            except Exception as e:
                error_count += 1
                errors.append(f"{file_path.name}: {str(e)}")

        # Show results
        if error_count == 0:
            messagebox.showinfo(
                "Success",
                f"Successfully added {success_count} files!",
                parent=self
            )
            self.destroy()
        else:
            error_msg = f"Added {success_count} files successfully.\n\n"
            error_msg += f"Failed to add {error_count} files:\n"
            error_msg += "\n".join(errors[:5])
            if len(errors) > 5:
                error_msg += f"\n... and {len(errors)-5} more"

            messagebox.showwarning(
                "Partial Success",
                error_msg,
                parent=self
            )
            self.destroy()
