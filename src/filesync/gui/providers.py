"""Providers configuration view."""

import customtkinter as ctk
from tkinter import messagebox


class ProvidersFrame(ctk.CTkFrame):
    """Providers configuration interface."""

    def __init__(self, parent, providers: dict, app):
        super().__init__(parent)
        self.providers = providers
        self.app = app

        self.grid_columnconfigure(0, weight=1)

        self._create_widgets()

    def _create_widgets(self):
        """Create widgets."""
        # Title
        title = ctk.CTkLabel(
            self,
            text="Cloud Providers",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title.grid(row=0, column=0, sticky="w", pady=(0, 30))

        # Info
        info = ctk.CTkLabel(
            self,
            text="Configure cloud storage providers for file synchronization.",
            font=ctk.CTkFont(size=14)
        )
        info.grid(row=1, column=0, sticky="w", pady=(0, 20))

        # Local provider
        self._create_provider_card(
            "Local Storage",
            "local",
            "Local file system for offline backups",
            2,
            enabled=True,
            can_disable=False
        )

        # Google Drive
        self._create_provider_card(
            "Google Drive",
            "gdrive",
            "Google Drive cloud storage (requires OAuth2)",
            3,
            enabled=False
        )

        # OneDrive
        self._create_provider_card(
            "Microsoft OneDrive",
            "onedrive",
            "Microsoft OneDrive cloud storage (requires OAuth2)",
            4,
            enabled=False
        )

        # Box
        self._create_provider_card(
            "Box",
            "box",
            "Box cloud storage (requires OAuth2)",
            5,
            enabled=False
        )

        # Proton Drive
        self._create_provider_card(
            "Proton Drive",
            "proton",
            "Proton Drive with end-to-end encryption (coming soon)",
            6,
            enabled=False,
            coming_soon=True
        )

    def _create_provider_card(self, name: str, provider_id: str,
                             description: str, row: int,
                             enabled: bool = False, can_disable: bool = True,
                             coming_soon: bool = False):
        """Create a provider configuration card."""
        card = ctk.CTkFrame(self)
        card.grid(row=row, column=0, sticky="ew", pady=(0, 15))

        # Header
        header_frame = ctk.CTkFrame(card, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=15)

        # Name and status
        name_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        name_frame.pack(side="left", fill="x", expand=True)

        name_label = ctk.CTkLabel(
            name_frame,
            text=name,
            font=ctk.CTkFont(size=16, weight="bold")
        )
        name_label.pack(side="left")

        if coming_soon:
            status_label = ctk.CTkLabel(
                name_frame,
                text="Coming Soon",
                font=ctk.CTkFont(size=11),
                text_color="orange",
                fg_color="gray30",
                corner_radius=4
            )
            status_label.pack(side="left", padx=10)
        elif enabled:
            status_label = ctk.CTkLabel(
                name_frame,
                text="✓ Active",
                font=ctk.CTkFont(size=11),
                text_color="green",
                fg_color="gray30",
                corner_radius=4
            )
            status_label.pack(side="left", padx=10)

        # Description
        desc_label = ctk.CTkLabel(
            card,
            text=description,
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        desc_label.pack(anchor="w", padx=20, pady=(0, 15))

        # Buttons
        if not coming_soon:
            btn_frame = ctk.CTkFrame(card, fg_color="transparent")
            btn_frame.pack(anchor="w", padx=20, pady=(0, 15))

            if enabled and provider_id == "local":
                # Local provider - show info button
                ctk.CTkButton(
                    btn_frame,
                    text="View Storage",
                    command=lambda: self._view_local_storage(),
                    height=30,
                    width=120,
                    fg_color="gray40",
                    hover_color="gray50"
                ).pack(side="left", padx=(0, 10))
            elif not enabled:
                # Not configured - show configure button
                ctk.CTkButton(
                    btn_frame,
                    text="Configure",
                    command=lambda p=provider_id: self._configure_provider(p),
                    height=30,
                    width=120
                ).pack(side="left", padx=(0, 10))
            else:
                # Configured - show disconnect button
                ctk.CTkButton(
                    btn_frame,
                    text="Disconnect",
                    command=lambda p=provider_id: self._disconnect_provider(p),
                    height=30,
                    width=120,
                    fg_color="red",
                    hover_color="darkred"
                ).pack(side="left", padx=(0, 10))

    def _configure_provider(self, provider_id: str):
        """Configure a cloud provider."""
        messagebox.showinfo(
            "Coming Soon",
            f"Cloud provider configuration will be available in a future update.\n\n"
            f"For now, you can:\n"
            f"1. Manually add OAuth2 credentials to config.yaml\n"
            f"2. Use the CLI: filesync init --provider {provider_id}\n"
            f"3. Refer to the README for provider setup instructions",
            parent=self
        )

    def _disconnect_provider(self, provider_id: str):
        """Disconnect a cloud provider."""
        if provider_id in self.providers:
            del self.providers[provider_id]
            messagebox.showinfo(
                "Disconnected",
                f"Provider '{provider_id}' has been disconnected.",
                parent=self
            )
            # Refresh view
            self._create_widgets()

    def _view_local_storage(self):
        """View local storage information."""
        if "local" in self.providers:
            provider = self.providers["local"]
            quota = provider.get_quota()

            messagebox.showinfo(
                "Local Storage",
                f"Path: {provider.root_path}\n\n"
                f"Total: {self._format_bytes(quota.total_bytes)}\n"
                f"Used: {self._format_bytes(quota.used_bytes)}\n"
                f"Available: {self._format_bytes(quota.available_bytes)}\n"
                f"Usage: {quota.usage_percent:.1f}%",
                parent=self
            )

    def _format_bytes(self, size: int) -> str:
        """Format bytes as human-readable string."""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} PB"
