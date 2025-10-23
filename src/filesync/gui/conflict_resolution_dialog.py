"""Conflict resolution dialog for handling file version conflicts."""

import customtkinter as ctk
from tkinter import messagebox
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from ..models.manifest_entry import FileLocation


class ConflictResolutionDialog(ctk.CTkToplevel):
    """Dialog for resolving file conflicts."""

    def __init__(self, parent, file_name: str, conflicts: List[Dict[str, Any]]):
        """
        Initialize conflict resolution dialog.

        Args:
            parent: Parent window
            file_name: Name of the conflicting file
            conflicts: List of conflicting versions with metadata
                Each dict should have: provider, path, size, modified, hash
        """
        super().__init__(parent)

        self.file_name = file_name
        self.conflicts = conflicts
        self.resolution = None  # Will be set to the chosen resolution
        self.selected_version = None

        self.title(f"Resolve Conflict: {file_name}")
        self.geometry("800x600")

        # Make modal
        self.transient(parent)
        self.grab_set()

        self._create_widgets()

    def _create_widgets(self):
        """Create dialog widgets."""
        # Header
        header_frame = ctk.CTkFrame(self, fg_color="gray20")
        header_frame.pack(fill="x", padx=0, pady=0)

        ctk.CTkLabel(
            header_frame,
            text="⚠ File Conflict Detected",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="orange"
        ).pack(pady=20)

        ctk.CTkLabel(
            header_frame,
            text=f"Multiple versions of '{self.file_name}' were found",
            font=ctk.CTkFont(size=14),
            text_color="gray"
        ).pack(pady=(0, 20))

        # Info section
        info_frame = ctk.CTkFrame(self, fg_color="transparent")
        info_frame.pack(fill="x", padx=20, pady=20)

        ctk.CTkLabel(
            info_frame,
            text=f"Found {len(self.conflicts)} different versions:",
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(anchor="w")

        # Scrollable versions list
        scroll_frame = ctk.CTkScrollableFrame(self, height=300)
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self.version_vars = []
        for idx, conflict in enumerate(self.conflicts):
            self._add_version_card(scroll_frame, idx, conflict)

        # Resolution options
        resolution_frame = ctk.CTkFrame(self)
        resolution_frame.pack(fill="x", padx=20, pady=(0, 20))

        ctk.CTkLabel(
            resolution_frame,
            text="Resolution Strategy:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=15, pady=(15, 10))

        self.resolution_var = ctk.StringVar(value="keep_selected")

        resolutions = [
            ("keep_selected", "Keep Selected Version", "Keep only the selected version, remove others"),
            ("keep_all", "Keep All Versions", "Rename files and keep all versions"),
            ("merge", "Manual Merge", "Download both versions for manual comparison"),
        ]

        for value, label, description in resolutions:
            radio_frame = ctk.CTkFrame(resolution_frame, fg_color="transparent")
            radio_frame.pack(fill="x", padx=15, pady=5)

            radio = ctk.CTkRadioButton(
                radio_frame,
                text=label,
                variable=self.resolution_var,
                value=value,
                font=ctk.CTkFont(size=12, weight="bold")
            )
            radio.pack(anchor="w")

            desc_label = ctk.CTkLabel(
                radio_frame,
                text=f"    {description}",
                font=ctk.CTkFont(size=10),
                text_color="gray"
            )
            desc_label.pack(anchor="w", padx=20)

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
            text="Resolve Conflict",
            command=self._resolve,
            width=140,
            height=40
        ).pack(side="left", padx=10)

    def _add_version_card(self, parent, idx: int, conflict: Dict[str, Any]):
        """Add a version card to the list."""
        card = ctk.CTkFrame(parent, fg_color="gray25")
        card.pack(fill="x", pady=10, padx=5)

        # Selection radio button
        var = ctk.StringVar(value="0" if idx == 0 else "")
        radio = ctk.CTkRadioButton(
            card,
            text="",
            variable=var,
            value="1"
        )
        radio.pack(side="left", padx=15, pady=15)
        self.version_vars.append((var, idx))

        # Version details
        details_frame = ctk.CTkFrame(card, fg_color="transparent")
        details_frame.pack(side="left", fill="both", expand=True, padx=(0, 15), pady=15)

        # Version header
        header_row = ctk.CTkFrame(details_frame, fg_color="transparent")
        header_row.pack(fill="x")

        ctk.CTkLabel(
            header_row,
            text=f"Version {idx + 1}",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(side="left")

        # Provider badge
        provider_badge = ctk.CTkLabel(
            header_row,
            text=conflict.get('provider', 'unknown'),
            font=ctk.CTkFont(size=10),
            fg_color="blue",
            corner_radius=5,
            padx=8,
            pady=3
        )
        provider_badge.pack(side="left", padx=10)

        # Newest badge
        if idx == 0:  # Assume first is newest
            newest_badge = ctk.CTkLabel(
                header_row,
                text="NEWEST",
                font=ctk.CTkFont(size=10, weight="bold"),
                fg_color="green",
                corner_radius=5,
                padx=8,
                pady=3
            )
            newest_badge.pack(side="left")

        # Details grid
        details_grid = ctk.CTkFrame(details_frame, fg_color="transparent")
        details_grid.pack(fill="x", pady=(10, 0))

        details = [
            ("Path:", conflict.get('path', 'N/A')),
            ("Size:", self._format_size(conflict.get('size', 0))),
            ("Modified:", self._format_date(conflict.get('modified'))),
            ("Hash:", self._format_hash(conflict.get('hash', 'N/A'))),
        ]

        for label, value in details:
            row = ctk.CTkFrame(details_grid, fg_color="transparent")
            row.pack(fill="x", pady=2)

            ctk.CTkLabel(
                row,
                text=label,
                font=ctk.CTkFont(size=11, weight="bold"),
                width=80,
                anchor="w"
            ).pack(side="left")

            ctk.CTkLabel(
                row,
                text=value,
                font=ctk.CTkFont(size=11),
                text_color="gray",
                anchor="w"
            ).pack(side="left", fill="x", expand=True)

        # Preview button (if supported)
        if self._is_previewable(conflict.get('path', '')):
            preview_btn = ctk.CTkButton(
                card,
                text="Preview",
                command=lambda: self._preview_version(conflict),
                width=80,
                height=30,
                fg_color="gray40",
                hover_color="gray50"
            )
            preview_btn.pack(side="left", padx=(0, 15))

    def _format_size(self, size: int) -> str:
        """Format file size in human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

    def _format_date(self, timestamp: Optional[float]) -> str:
        """Format timestamp to readable date."""
        if timestamp is None:
            return "Unknown"
        try:
            dt = datetime.fromtimestamp(timestamp)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except:
            return "Invalid date"

    def _format_hash(self, hash_str: str) -> str:
        """Format hash for display."""
        if len(hash_str) > 20:
            return f"{hash_str[:16]}...{hash_str[-8:]}"
        return hash_str

    def _is_previewable(self, path: str) -> bool:
        """Check if file can be previewed."""
        path_obj = Path(path)
        preview_extensions = {'.txt', '.jpg', '.jpeg', '.png', '.gif', '.pdf', '.md'}
        return path_obj.suffix.lower() in preview_extensions

    def _preview_version(self, conflict: Dict[str, Any]):
        """Preview a specific version (placeholder)."""
        messagebox.showinfo(
            "Preview",
            f"Preview functionality for:\n{conflict.get('path', 'N/A')}\n\n"
            f"This would open a preview window showing the file contents.",
            parent=self
        )

    def _resolve(self):
        """Resolve the conflict with chosen strategy."""
        # Find selected version
        selected_idx = None
        for var, idx in self.version_vars:
            if var.get() == "1":
                selected_idx = idx
                break

        resolution_type = self.resolution_var.get()

        if resolution_type == "keep_selected" and selected_idx is None:
            messagebox.showerror(
                "Error",
                "Please select a version to keep",
                parent=self
            )
            return

        self.resolution = {
            'type': resolution_type,
            'selected_version': selected_idx,
            'selected_conflict': self.conflicts[selected_idx] if selected_idx is not None else None
        }

        messagebox.showinfo(
            "Conflict Resolved",
            f"Conflict resolution applied: {resolution_type}\n\n"
            f"The changes will be synced to all providers.",
            parent=self
        )

        self.destroy()


class ConflictListDialog(ctk.CTkToplevel):
    """Dialog showing all files with conflicts."""

    def __init__(self, parent, conflicts: List[Dict[str, Any]]):
        """
        Initialize conflict list dialog.

        Args:
            parent: Parent window
            conflicts: List of files with conflicts
                Each dict should have: file_name, count, last_detected
        """
        super().__init__(parent)

        self.parent_window = parent
        self.conflicts = conflicts

        self.title("File Conflicts")
        self.geometry("700x500")

        # Make modal
        self.transient(parent)
        self.grab_set()

        self._create_widgets()

    def _create_widgets(self):
        """Create dialog widgets."""
        # Header
        header_frame = ctk.CTkFrame(self, fg_color="gray20")
        header_frame.pack(fill="x")

        ctk.CTkLabel(
            header_frame,
            text=f"⚠ {len(self.conflicts)} Files with Conflicts",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="orange"
        ).pack(pady=20)

        # Info
        info_label = ctk.CTkLabel(
            self,
            text="The following files have multiple conflicting versions across providers:",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        info_label.pack(pady=15)

        # Conflicts list
        scroll_frame = ctk.CTkScrollableFrame(self)
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        for conflict in self.conflicts:
            self._add_conflict_row(scroll_frame, conflict)

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=20)

        ctk.CTkButton(
            btn_frame,
            text="Close",
            command=self.destroy,
            width=120,
            height=40
        ).pack()

    def _add_conflict_row(self, parent, conflict: Dict[str, Any]):
        """Add a conflict row."""
        row_frame = ctk.CTkFrame(parent, fg_color="gray25")
        row_frame.pack(fill="x", pady=5)

        # File info
        info_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
        info_frame.pack(side="left", fill="both", expand=True, padx=15, pady=15)

        ctk.CTkLabel(
            info_frame,
            text=conflict.get('file_name', 'Unknown'),
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w"
        ).pack(anchor="w")

        details_text = f"{conflict.get('count', 0)} conflicting versions"
        if 'last_detected' in conflict:
            details_text += f" • Detected: {conflict['last_detected']}"

        ctk.CTkLabel(
            info_frame,
            text=details_text,
            font=ctk.CTkFont(size=11),
            text_color="gray",
            anchor="w"
        ).pack(anchor="w", pady=(3, 0))

        # Resolve button
        resolve_btn = ctk.CTkButton(
            row_frame,
            text="Resolve",
            command=lambda: self._open_resolution(conflict),
            width=100,
            height=35
        )
        resolve_btn.pack(side="right", padx=15)

    def _open_resolution(self, conflict: Dict[str, Any]):
        """Open conflict resolution dialog for a specific file."""
        # This would fetch the actual conflict data
        # For now, show a placeholder
        ConflictResolutionDialog(
            self,
            conflict.get('file_name', 'Unknown'),
            conflict.get('versions', [])
        )
