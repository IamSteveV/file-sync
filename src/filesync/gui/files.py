"""Files management view."""

import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
from typing import Optional
from ..core.manifest import ManifestManager
from ..core.sync import SyncEngine
from ..models.tier import Tier
from ..encryption.crypto import key_manager
from .dialogs import PassphraseDialog


class FilesFrame(ctk.CTkFrame):
    """Files management interface."""

    def __init__(self, parent, manifest: ManifestManager, sync: SyncEngine, app):
        super().__init__(parent)
        self.manifest = manifest
        self.sync = sync
        self.app = app

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self._create_widgets()
        self._load_files()

    def _create_widgets(self):
        """Create widgets."""
        # Title and add button
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        header_frame.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            header_frame,
            text="Files",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title.grid(row=0, column=0, sticky="w")

        add_btn = ctk.CTkButton(
            header_frame,
            text="+ Add File",
            command=self._add_file_dialog,
            height=35,
            font=ctk.CTkFont(size=14)
        )
        add_btn.grid(row=0, column=1, padx=10)

        # Search and filter
        search_frame = ctk.CTkFrame(self)
        search_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        search_frame.grid_columnconfigure(0, weight=1)

        self.search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="Search files...",
            height=35
        )
        self.search_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.search_entry.bind("<KeyRelease>", lambda e: self._filter_files())

        self.tier_filter = ctk.CTkOptionMenu(
            search_frame,
            values=["All Tiers", "Critical", "Important", "Standard", "Archive"],
            command=lambda _: self._filter_files(),
            height=35,
            width=150
        )
        self.tier_filter.grid(row=0, column=1, padx=(0, 10))
        self.tier_filter.set("All Tiers")

        refresh_btn = ctk.CTkButton(
            search_frame,
            text="🔄 Refresh",
            command=self._load_files,
            width=100,
            height=35
        )
        refresh_btn.grid(row=0, column=2)

        # Files list
        self._create_file_list()

    def _create_file_list(self):
        """Create the scrollable file list."""
        list_frame = ctk.CTkFrame(self)
        list_frame.grid(row=2, column=0, sticky="nsew")
        list_frame.grid_columnconfigure(0, weight=1)
        list_frame.grid_rowconfigure(0, weight=1)

        # Create treeview for file list
        columns = ("name", "tier", "size", "locations", "encrypted", "tags")
        self.file_tree = tk.ttk.Treeview(
            list_frame,
            columns=columns,
            show="tree headings",
            selectmode="browse"
        )

        # Configure columns
        self.file_tree.heading("name", text="File Name")
        self.file_tree.heading("tier", text="Tier")
        self.file_tree.heading("size", text="Size")
        self.file_tree.heading("locations", text="Locations")
        self.file_tree.heading("encrypted", text="Encrypted")
        self.file_tree.heading("tags", text="Tags")

        self.file_tree.column("#0", width=0, stretch=False)
        self.file_tree.column("name", width=300)
        self.file_tree.column("tier", width=100)
        self.file_tree.column("size", width=100)
        self.file_tree.column("locations", width=100)
        self.file_tree.column("encrypted", width=80)
        self.file_tree.column("tags", width=200)

        # Scrollbar
        scrollbar = ctk.CTkScrollbar(list_frame, command=self.file_tree.yview)
        self.file_tree.configure(yscrollcommand=scrollbar.set)

        self.file_tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        # Context menu
        self.file_tree.bind("<Double-Button-1>", self._show_file_details)
        self.file_tree.bind("<Button-3>", self._show_context_menu)

    def _load_files(self):
        """Load files from manifest."""
        # Clear existing items
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)

        if not self.manifest:
            return

        entries = self.manifest.get_all_entries()

        for entry in entries:
            encrypted = "🔒" if entry.encrypted else ""
            tags = ", ".join(entry.tags[:3])
            if len(entry.tags) > 3:
                tags += "..."

            self.file_tree.insert(
                "",
                "end",
                values=(
                    entry.file_name,
                    entry.tier.name,
                    self._format_bytes(entry.size),
                    len(entry.locations),
                    encrypted,
                    tags
                ),
                tags=(entry.content_hash,)
            )

    def _filter_files(self):
        """Filter files based on search and tier."""
        search_text = self.search_entry.get().lower()
        tier_filter = self.tier_filter.get()

        # Clear current display
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)

        if not self.manifest:
            return

        entries = self.manifest.get_all_entries()

        for entry in entries:
            # Apply tier filter
            if tier_filter != "All Tiers" and entry.tier.name != tier_filter.upper():
                continue

            # Apply search filter
            if search_text and search_text not in entry.file_name.lower():
                if not any(search_text in tag.lower() for tag in entry.tags):
                    continue

            encrypted = "🔒" if entry.encrypted else ""
            tags = ", ".join(entry.tags[:3])
            if len(entry.tags) > 3:
                tags += "..."

            self.file_tree.insert(
                "",
                "end",
                values=(
                    entry.file_name,
                    entry.tier.name,
                    self._format_bytes(entry.size),
                    len(entry.locations),
                    encrypted,
                    tags
                ),
                tags=(entry.content_hash,)
            )

    def _add_file_dialog(self):
        """Show dialog to add a new file."""
        dialog = AddFileDialog(self, self.manifest, self.sync, self.app)
        dialog.wait_window()
        self._load_files()

    def _show_file_details(self, event):
        """Show detailed information about a file."""
        selection = self.file_tree.selection()
        if not selection:
            return

        item = self.file_tree.item(selection[0])
        content_hash = item["tags"][0]

        entry = self.manifest.get_entry(content_hash)
        if entry:
            FileDetailsDialog(self, entry)

    def _show_context_menu(self, event):
        """Show context menu for file operations."""
        # TODO: Implement context menu
        pass

    def _format_bytes(self, size: int) -> str:
        """Format bytes as human-readable string."""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} PB"


class AddFileDialog(ctk.CTkToplevel):
    """Dialog for adding a new file."""

    def __init__(self, parent, manifest: ManifestManager, sync: SyncEngine, app):
        super().__init__(parent)
        self.manifest = manifest
        self.sync = sync
        self.app = app

        self.title("Add File")
        self.geometry("600x500")
        self.resizable(False, False)

        # Make modal
        self.transient(parent)
        self.grab_set()

        self.file_path: Optional[Path] = None

        self._create_widgets()

    def _create_widgets(self):
        """Create dialog widgets."""
        # File selection
        file_frame = ctk.CTkFrame(self)
        file_frame.pack(fill="x", padx=20, pady=20)

        ctk.CTkLabel(
            file_frame,
            text="File:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", pady=(0, 10))

        self.file_label = ctk.CTkLabel(
            file_frame,
            text="No file selected",
            fg_color="gray30",
            corner_radius=6,
            height=40
        )
        self.file_label.pack(fill="x", pady=(0, 10))

        ctk.CTkButton(
            file_frame,
            text="Select File",
            command=self._select_file,
            height=35
        ).pack(fill="x")

        # Tier selection
        tier_frame = ctk.CTkFrame(self)
        tier_frame.pack(fill="x", padx=20, pady=(0, 20))

        ctk.CTkLabel(
            tier_frame,
            text="Importance Tier:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", pady=(0, 10))

        self.tier_var = ctk.StringVar(value="Standard")
        tier_options = ["Critical", "Important", "Standard", "Archive"]
        self.tier_menu = ctk.CTkOptionMenu(
            tier_frame,
            variable=self.tier_var,
            values=tier_options,
            height=35
        )
        self.tier_menu.pack(fill="x")

        # Tags
        tags_frame = ctk.CTkFrame(self)
        tags_frame.pack(fill="x", padx=20, pady=(0, 20))

        ctk.CTkLabel(
            tags_frame,
            text="Tags (comma-separated):",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", pady=(0, 10))

        self.tags_entry = ctk.CTkEntry(
            tags_frame,
            placeholder_text="e.g., work, project, 2024",
            height=35
        )
        self.tags_entry.pack(fill="x")

        # Encryption
        encrypt_frame = ctk.CTkFrame(self)
        encrypt_frame.pack(fill="x", padx=20, pady=(0, 20))

        self.encrypt_var = ctk.BooleanVar(value=False)
        self.encrypt_check = ctk.CTkCheckBox(
            encrypt_frame,
            text="Encrypt file before upload",
            variable=self.encrypt_var,
            font=ctk.CTkFont(size=14)
        )
        self.encrypt_check.pack(anchor="w")

        # Reason
        reason_frame = ctk.CTkFrame(self)
        reason_frame.pack(fill="x", padx=20, pady=(0, 20))

        ctk.CTkLabel(
            reason_frame,
            text="Reason (optional):",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", pady=(0, 10))

        self.reason_entry = ctk.CTkEntry(
            reason_frame,
            placeholder_text="Why is this file important?",
            height=35
        )
        self.reason_entry.pack(fill="x")

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=20)

        ctk.CTkButton(
            btn_frame,
            text="Cancel",
            command=self.destroy,
            fg_color="gray40",
            hover_color="gray50",
            height=40
        ).pack(side="right", padx=(10, 0))

        ctk.CTkButton(
            btn_frame,
            text="Add File",
            command=self._add_file,
            height=40
        ).pack(side="right")

    def _select_file(self):
        """Open file picker."""
        filename = filedialog.askopenfilename(
            title="Select a file",
            parent=self
        )
        if filename:
            self.file_path = Path(filename)
            self.file_label.configure(text=self.file_path.name)

    def _add_file(self):
        """Add the selected file."""
        if not self.file_path:
            messagebox.showerror("Error", "Please select a file", parent=self)
            return

        # Parse inputs
        tier_name = self.tier_var.get().upper()
        tier = Tier[tier_name]

        tags_text = self.tags_entry.get().strip()
        tags = [t.strip() for t in tags_text.split(",")] if tags_text else []

        encrypt = self.encrypt_var.get()
        reason = self.reason_entry.get().strip() or None

        # Check if encryption is needed
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

        # Add file
        self.app.set_status(f"Adding {self.file_path.name}...")

        success, entry, result = self.sync.add_file(
            self.file_path,
            tier,
            tags,
            reason,
            encrypt
        )

        if success:
            messagebox.showinfo(
                "Success",
                f"File added successfully!\n\n"
                f"Hash: {entry.content_hash[:24]}...\n"
                f"Tier: {entry.tier.name}\n"
                f"Locations: {len(entry.locations)}",
                parent=self
            )
            self.app.set_status("Ready")
            self.destroy()
        else:
            error_msg = "\n".join([e["error"] for e in result.errors])
            messagebox.showerror(
                "Error",
                f"Failed to add file:\n{error_msg}",
                parent=self
            )
            self.app.set_status("Error")


class FileDetailsDialog(ctk.CTkToplevel):
    """Dialog showing detailed file information."""

    def __init__(self, parent, entry):
        super().__init__(parent)
        self.entry = entry

        self.title(f"File Details - {entry.file_name}")
        self.geometry("700x600")

        # Make modal
        self.transient(parent)
        self.grab_set()

        self._create_widgets()

    def _create_widgets(self):
        """Create dialog widgets."""
        # Scrollable frame
        scroll_frame = ctk.CTkScrollableFrame(self)
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # File name
        ctk.CTkLabel(
            scroll_frame,
            text=self.entry.file_name,
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(anchor="w", pady=(0, 20))

        # Basic info
        self._add_info_row(scroll_frame, "Content Hash", self.entry.content_hash[:64] + "...")
        self._add_info_row(scroll_frame, "Size", self._format_bytes(self.entry.size))
        self._add_info_row(scroll_frame, "MIME Type", self.entry.mime_type)
        self._add_info_row(scroll_frame, "Tier", self.entry.tier.name)
        self._add_info_row(scroll_frame, "Encrypted", "Yes 🔒" if self.entry.encrypted else "No")

        if self.entry.tags:
            self._add_info_row(scroll_frame, "Tags", ", ".join(self.entry.tags))

        if self.entry.importance_reason:
            self._add_info_row(scroll_frame, "Reason", self.entry.importance_reason)

        # Locations
        ctk.CTkLabel(
            scroll_frame,
            text="Locations:",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", pady=(20, 10))

        for loc in self.entry.locations:
            loc_frame = ctk.CTkFrame(scroll_frame)
            loc_frame.pack(fill="x", pady=5)

            verified = "✓" if loc.verified else "✗"
            loc_text = f"{verified} {loc.provider}: {loc.path}"

            ctk.CTkLabel(
                loc_frame,
                text=loc_text,
                font=ctk.CTkFont(size=12)
            ).pack(anchor="w", padx=10, pady=10)

        # Close button
        ctk.CTkButton(
            self,
            text="Close",
            command=self.destroy,
            height=40
        ).pack(pady=20)

    def _add_info_row(self, parent, label: str, value: str):
        """Add an information row."""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=5)

        ctk.CTkLabel(
            frame,
            text=f"{label}:",
            font=ctk.CTkFont(size=12, weight="bold"),
            width=150,
            anchor="w"
        ).pack(side="left")

        ctk.CTkLabel(
            frame,
            text=value,
            font=ctk.CTkFont(size=12),
            anchor="w"
        ).pack(side="left", fill="x", expand=True)

    def _format_bytes(self, size: int) -> str:
        """Format bytes as human-readable string."""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} PB"
