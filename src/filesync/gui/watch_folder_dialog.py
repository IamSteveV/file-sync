"""Dialog for configuring folder watching."""

import customtkinter as ctk
from pathlib import Path
from ..models.tier import Tier


class WatchFolderDialog(ctk.CTkToplevel):
    """Dialog for configuring auto-import settings for a folder."""

    def __init__(self, parent, folder_path: Path):
        super().__init__(parent)

        self.folder_path = folder_path
        self.tier = None
        self.recursive = False

        self.title("Configure Folder Watch")
        self.geometry("500x400")
        self.resizable(False, False)

        # Make modal
        self.transient(parent)
        self.grab_set()

        self._create_widgets()

    def _create_widgets(self):
        """Create dialog widgets."""
        # Title
        title = ctk.CTkLabel(
            self,
            text="Configure Folder Watch",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title.pack(pady=(30, 10))

        # Folder path
        path_frame = ctk.CTkFrame(self, fg_color="gray25")
        path_frame.pack(fill="x", padx=20, pady=(0, 20))

        ctk.CTkLabel(
            path_frame,
            text="Folder:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", padx=15, pady=(15, 5))

        ctk.CTkLabel(
            path_frame,
            text=str(self.folder_path),
            font=ctk.CTkFont(size=11),
            text_color="gray"
        ).pack(anchor="w", padx=15, pady=(0, 15))

        # Tier selection
        tier_frame = ctk.CTkFrame(self)
        tier_frame.pack(fill="x", padx=20, pady=(0, 20))

        ctk.CTkLabel(
            tier_frame,
            text="Default Tier for New Files:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=15, pady=(15, 10))

        ctk.CTkLabel(
            tier_frame,
            text="Files added to this folder will be assigned this importance tier.",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        ).pack(anchor="w", padx=15, pady=(0, 10))

        # Tier radio buttons
        self.tier_var = ctk.StringVar(value="2")  # Default to Standard

        tiers = [
            (Tier.CRITICAL, "Critical", "Maximum redundancy, offline backup, encryption required"),
            (Tier.IMPORTANT, "Important", "High redundancy, multiple providers"),
            (Tier.STANDARD, "Standard", "Standard redundancy"),
            (Tier.ARCHIVE, "Archive", "Minimum redundancy, cost-optimized"),
        ]

        for tier, name, description in tiers:
            radio_frame = ctk.CTkFrame(tier_frame, fg_color="transparent")
            radio_frame.pack(fill="x", padx=15, pady=5)

            radio = ctk.CTkRadioButton(
                radio_frame,
                text=f"Tier {tier.value}: {name}",
                variable=self.tier_var,
                value=str(tier.value),
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

        # Recursive option
        self.recursive_var = ctk.CTkSwitch(
            self,
            text="Watch subfolders recursively",
            font=ctk.CTkFont(size=12)
        )
        self.recursive_var.pack(anchor="w", padx=35, pady=(10, 20))

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=20)

        ctk.CTkButton(
            btn_frame,
            text="Cancel",
            command=self.destroy,
            fg_color="gray40",
            hover_color="gray50",
            width=120,
            height=40
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            btn_frame,
            text="Add Watch",
            command=self._confirm,
            width=120,
            height=40
        ).pack(side="left", padx=10)

    def _confirm(self):
        """Confirm and close dialog."""
        self.tier = int(self.tier_var.get())
        self.recursive = self.recursive_var.get()
        self.destroy()
