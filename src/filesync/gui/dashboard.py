"""Dashboard view showing statistics and overview."""

import customtkinter as ctk
from typing import Optional
from ..core.manifest import ManifestManager
from ..core.redundancy import RedundancyManager
from ..core.lifecycle import LifecycleManager


class DashboardFrame(ctk.CTkFrame):
    """Dashboard showing system statistics and status."""

    def __init__(self, parent, manifest: ManifestManager,
                 redundancy: Optional[RedundancyManager],
                 lifecycle: Optional[LifecycleManager]):
        super().__init__(parent)
        self.manifest = manifest
        self.redundancy = redundancy
        self.lifecycle = lifecycle

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self._create_widgets()
        self._load_data()

    def _create_widgets(self):
        """Create dashboard widgets."""
        # Title
        title = ctk.CTkLabel(
            self,
            text="Dashboard",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 20))

        # Statistics cards
        self._create_stats_section()

        # Tier breakdown
        self._create_tier_section()

        # Provider breakdown
        self._create_provider_section()

        # Redundancy status
        self._create_redundancy_section()

    def _create_stats_section(self):
        """Create statistics cards."""
        stats_frame = ctk.CTkFrame(self)
        stats_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 20))
        stats_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        # Total files card
        self.total_files_card = self._create_stat_card(
            stats_frame, "Total Files", "0", 0
        )

        # Total size card
        self.total_size_card = self._create_stat_card(
            stats_frame, "Total Size", "0 B", 1
        )

        # Encrypted files card
        self.encrypted_card = self._create_stat_card(
            stats_frame, "Encrypted", "0", 2
        )

        # Providers card
        self.providers_card = self._create_stat_card(
            stats_frame, "Active Providers", "0", 3
        )

    def _create_stat_card(self, parent, title: str, value: str, column: int):
        """Create a statistics card."""
        card = ctk.CTkFrame(parent)
        card.grid(row=0, column=column, padx=10, pady=10, sticky="ew")

        title_label = ctk.CTkLabel(
            card,
            text=title,
            font=ctk.CTkFont(size=12)
        )
        title_label.pack(pady=(15, 5))

        value_label = ctk.CTkLabel(
            card,
            text=value,
            font=ctk.CTkFont(size=24, weight="bold")
        )
        value_label.pack(pady=(0, 15))

        return value_label

    def _create_tier_section(self):
        """Create tier breakdown section."""
        tier_frame = ctk.CTkFrame(self)
        tier_frame.grid(row=2, column=0, sticky="nsew", padx=(0, 10), pady=(0, 20))

        title = ctk.CTkLabel(
            tier_frame,
            text="Files by Tier",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title.pack(pady=15, padx=15, anchor="w")

        # Tier list
        self.tier_list = ctk.CTkTextbox(tier_frame, height=200)
        self.tier_list.pack(fill="both", expand=True, padx=15, pady=(0, 15))

    def _create_provider_section(self):
        """Create provider breakdown section."""
        provider_frame = ctk.CTkFrame(self)
        provider_frame.grid(row=2, column=1, sticky="nsew", padx=(10, 0), pady=(0, 20))

        title = ctk.CTkLabel(
            provider_frame,
            text="Files by Provider",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title.pack(pady=15, padx=15, anchor="w")

        # Provider list
        self.provider_list = ctk.CTkTextbox(provider_frame, height=200)
        self.provider_list.pack(fill="both", expand=True, padx=15, pady=(0, 15))

    def _create_redundancy_section(self):
        """Create redundancy status section."""
        redundancy_frame = ctk.CTkFrame(self)
        redundancy_frame.grid(row=3, column=0, columnspan=2, sticky="ew")

        title = ctk.CTkLabel(
            redundancy_frame,
            text="Redundancy Status",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title.pack(pady=15, padx=15, anchor="w")

        # Status text
        self.redundancy_text = ctk.CTkTextbox(redundancy_frame, height=150)
        self.redundancy_text.pack(fill="both", expand=True, padx=15, pady=(0, 15))

    def _load_data(self):
        """Load and display data."""
        if not self.manifest:
            return

        stats = self.manifest.get_statistics()

        # Update stat cards
        self.total_files_card.configure(text=str(stats["total_files"]))
        self.total_size_card.configure(text=self._format_bytes(stats["total_size"]))
        self.encrypted_card.configure(text=str(stats["encrypted_files"]))
        self.providers_card.configure(text=str(len(stats["by_provider"])))

        # Update tier breakdown
        self.tier_list.delete("1.0", "end")
        for tier_name, count in stats["by_tier"].items():
            self.tier_list.insert("end", f"{tier_name}: {count} files\n")

        # Update provider breakdown
        self.provider_list.delete("1.0", "end")
        for provider, count in stats["by_provider"].items():
            self.provider_list.insert("end", f"{provider}: {count} files\n")

        # Update redundancy status
        if self.redundancy:
            self._update_redundancy_status()

    def _update_redundancy_status(self):
        """Update redundancy status information."""
        entries = self.manifest.get_all_entries()
        report = self.redundancy.generate_redundancy_report(entries)

        self.redundancy_text.delete("1.0", "end")
        self.redundancy_text.insert("end", f"Compliant files: {report['compliant']}\n")
        self.redundancy_text.insert("end", f"Non-compliant files: {report['non_compliant']}\n")
        self.redundancy_text.insert("end", f"Average redundancy score: {report['average_score']:.2%}\n\n")

        if report['critical_issues']:
            self.redundancy_text.insert("end", f"⚠️ {len(report['critical_issues'])} critical issues\n")

        if report['recommendations']:
            self.redundancy_text.insert("end", "\nRecommendations:\n")
            for rec in report['recommendations'][:3]:
                self.redundancy_text.insert("end", f"• {rec}\n")

    def _format_bytes(self, size: int) -> str:
        """Format bytes as human-readable string."""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} PB"

    def refresh(self):
        """Refresh the dashboard data."""
        self._load_data()
