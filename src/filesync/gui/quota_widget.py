"""Cloud quota monitoring widget."""

import customtkinter as ctk
from tkinter import messagebox
from typing import Dict
from ..quota.quota_monitor import QuotaMonitor, QuotaInfo
from datetime import datetime


class QuotaWidget(ctk.CTkFrame):
    """Widget displaying cloud storage quotas."""

    def __init__(self, parent, quota_monitor: QuotaMonitor):
        """
        Initialize quota widget.

        Args:
            parent: Parent widget
            quota_monitor: QuotaMonitor instance
        """
        super().__init__(parent, fg_color="gray20")

        self.quota_monitor = quota_monitor

        self._create_widgets()
        self._load_quotas()

    def _create_widgets(self):
        """Create widgets."""
        # Header
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(15, 10))

        ctk.CTkLabel(
            header_frame,
            text="Storage Quotas",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(side="left")

        ctk.CTkButton(
            header_frame,
            text="🔄 Refresh",
            command=self._refresh_quotas,
            width=100,
            height=30,
            fg_color="gray30",
            hover_color="gray40"
        ).pack(side="right")

        # Quotas container
        self.quotas_container = ctk.CTkFrame(self, fg_color="transparent")
        self.quotas_container.pack(fill="both", expand=True, padx=20, pady=(0, 15))

    def _load_quotas(self):
        """Load and display quotas."""
        # Clear existing widgets
        for widget in self.quotas_container.winfo_children():
            widget.destroy()

        quotas = self.quota_monitor.get_all_quotas()

        if not quotas:
            ctk.CTkLabel(
                self.quotas_container,
                text="No quota information available\nClick Refresh to fetch quota data",
                font=ctk.CTkFont(size=12),
                text_color="gray"
            ).pack(pady=30)
        else:
            for provider_name, quota_info in quotas.items():
                self._add_quota_card(quota_info)

            # Add summary
            self._add_summary()

    def _add_quota_card(self, quota: QuotaInfo):
        """Add a quota card for a provider."""
        # Determine color based on usage
        if quota.is_critical:
            bar_color = "red"
            text_color = "red"
        elif quota.is_warning:
            bar_color = "orange"
            text_color = "orange"
        else:
            bar_color = "green"
            text_color = "white"

        # Card frame
        card = ctk.CTkFrame(self.quotas_container, fg_color="gray25")
        card.pack(fill="x", pady=8)

        # Provider name and status
        header_frame = ctk.CTkFrame(card, fg_color="transparent")
        header_frame.pack(fill="x", padx=15, pady=(15, 10))

        provider_label = ctk.CTkLabel(
            header_frame,
            text=quota.provider.title().replace("Gdrive", "Google Drive"),
            font=ctk.CTkFont(size=15, weight="bold")
        )
        provider_label.pack(side="left")

        # Status badge
        if quota.is_critical:
            status_text = "CRITICAL"
            status_color = "red"
        elif quota.is_warning:
            status_text = "WARNING"
            status_color = "orange"
        else:
            status_text = "OK"
            status_color = "green"

        status_badge = ctk.CTkLabel(
            header_frame,
            text=status_text,
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color=status_color,
            corner_radius=5,
            padx=8,
            pady=3
        )
        status_badge.pack(side="right")

        # Usage info
        info_frame = ctk.CTkFrame(card, fg_color="transparent")
        info_frame.pack(fill="x", padx=15, pady=(0, 10))

        used_text = self.quota_monitor.format_bytes(quota.used_bytes)
        total_text = self.quota_monitor.format_bytes(quota.total_bytes)
        available_text = self.quota_monitor.format_bytes(quota.available_bytes)

        usage_text = f"{used_text} / {total_text} ({quota.used_percentage:.1f}%)"

        ctk.CTkLabel(
            info_frame,
            text=usage_text,
            font=ctk.CTkFont(size=13),
            text_color=text_color
        ).pack(anchor="w")

        ctk.CTkLabel(
            info_frame,
            text=f"Available: {available_text}",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        ).pack(anchor="w", pady=(3, 0))

        # Progress bar
        progress_frame = ctk.CTkFrame(card, fg_color="transparent")
        progress_frame.pack(fill="x", padx=15, pady=(0, 10))

        progress_bar = ctk.CTkProgressBar(
            progress_frame,
            height=12,
            progress_color=bar_color
        )
        progress_bar.pack(fill="x")
        progress_bar.set(quota.used_percentage / 100)

        # Last updated
        last_updated_dt = datetime.fromtimestamp(quota.last_updated)
        last_updated_text = last_updated_dt.strftime('%Y-%m-%d %H:%M:%S')

        ctk.CTkLabel(
            card,
            text=f"Last updated: {last_updated_text}",
            font=ctk.CTkFont(size=9),
            text_color="gray60"
        ).pack(anchor="e", padx=15, pady=(0, 10))

    def _add_summary(self):
        """Add summary section."""
        summary = self.quota_monitor.get_summary()

        summary_frame = ctk.CTkFrame(self.quotas_container, fg_color="gray30", corner_radius=10)
        summary_frame.pack(fill="x", pady=(15, 0))

        ctk.CTkLabel(
            summary_frame,
            text="Total Storage Summary",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=(15, 10))

        # Grid for summary stats
        stats_frame = ctk.CTkFrame(summary_frame, fg_color="transparent")
        stats_frame.pack(fill="x", padx=20, pady=(0, 15))

        stats = [
            ("Total Capacity", self.quota_monitor.format_bytes(summary['total_capacity'])),
            ("Total Used", self.quota_monitor.format_bytes(summary['total_used'])),
            ("Total Available", self.quota_monitor.format_bytes(summary['total_available'])),
            ("Overall Usage", f"{summary['total_used_percentage']:.1f}%"),
        ]

        for i, (label, value) in enumerate(stats):
            stat_frame = ctk.CTkFrame(stats_frame, fg_color="gray25", corner_radius=8)
            stat_frame.grid(row=i // 2, column=i % 2, padx=8, pady=8, sticky="ew")

            stats_frame.grid_columnconfigure(0, weight=1)
            stats_frame.grid_columnconfigure(1, weight=1)

            ctk.CTkLabel(
                stat_frame,
                text=label,
                font=ctk.CTkFont(size=11),
                text_color="gray"
            ).pack(pady=(10, 3))

            ctk.CTkLabel(
                stat_frame,
                text=value,
                font=ctk.CTkFont(size=14, weight="bold")
            ).pack(pady=(0, 10))

        # Warnings/alerts
        if summary['warnings'] > 0 or summary['critical'] > 0:
            alert_frame = ctk.CTkFrame(summary_frame, fg_color="orange" if summary['critical'] == 0 else "red", corner_radius=8)
            alert_frame.pack(fill="x", padx=20, pady=(10, 15))

            if summary['critical'] > 0:
                alert_text = f"⚠ {summary['critical']} provider(s) in CRITICAL state!"
            else:
                alert_text = f"⚠ {summary['warnings']} provider(s) in WARNING state"

            ctk.CTkLabel(
                alert_frame,
                text=alert_text,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="white"
            ).pack(pady=10)

    def _refresh_quotas(self):
        """Refresh quota information from providers."""
        # Show loading message
        for widget in self.quotas_container.winfo_children():
            widget.destroy()

        loading_label = ctk.CTkLabel(
            self.quotas_container,
            text="Refreshing quota information...",
            font=ctk.CTkFont(size=13)
        )
        loading_label.pack(pady=30)

        # Update in background (in real app, this would be threaded)
        self.after(100, self._do_refresh)

    def _do_refresh(self):
        """Perform the actual refresh."""
        try:
            self.quota_monitor.update_all_quotas()
            self._load_quotas()

        except Exception as e:
            for widget in self.quotas_container.winfo_children():
                widget.destroy()

            ctk.CTkLabel(
                self.quotas_container,
                text=f"Error refreshing quotas:\n{str(e)}",
                font=ctk.CTkFont(size=12),
                text_color="red"
            ).pack(pady=30)

    def refresh(self):
        """Public method to refresh display."""
        self._load_quotas()


class QuotaDialog(ctk.CTkToplevel):
    """Full-screen quota monitoring dialog."""

    def __init__(self, parent, quota_monitor: QuotaMonitor):
        """
        Initialize quota dialog.

        Args:
            parent: Parent window
            quota_monitor: QuotaMonitor instance
        """
        super().__init__(parent)

        self.quota_monitor = quota_monitor

        self.title("Storage Quota Monitor")
        self.geometry("800x700")

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
            text="📊 Cloud Storage Quotas",
            font=ctk.CTkFont(size=24, weight="bold")
        ).pack(pady=20)

        # Quota widget
        quota_widget = QuotaWidget(self, self.quota_monitor)
        quota_widget.pack(fill="both", expand=True, padx=20, pady=(10, 20))

        # Close button
        ctk.CTkButton(
            self,
            text="Close",
            command=self.destroy,
            width=120,
            height=40
        ).pack(pady=20)


class QuotaCompactWidget(ctk.CTkFrame):
    """Compact quota widget for dashboard."""

    def __init__(self, parent, quota_monitor: QuotaMonitor):
        """
        Initialize compact quota widget.

        Args:
            parent: Parent widget
            quota_monitor: QuotaMonitor instance
        """
        super().__init__(parent, fg_color="gray20", corner_radius=10)

        self.quota_monitor = quota_monitor

        self._create_widgets()
        self._load_data()

    def _create_widgets(self):
        """Create widgets."""
        # Header
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=15, pady=(15, 10))

        ctk.CTkLabel(
            header_frame,
            text="💾 Storage",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(side="left")

        # Content
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))

    def _load_data(self):
        """Load and display data."""
        summary = self.quota_monitor.get_summary()

        if summary['total_capacity'] == 0:
            ctk.CTkLabel(
                self.content_frame,
                text="No quota data",
                font=ctk.CTkFont(size=11),
                text_color="gray"
            ).pack(pady=10)
            return

        # Total usage
        used_text = self.quota_monitor.format_bytes(summary['total_used'])
        total_text = self.quota_monitor.format_bytes(summary['total_capacity'])

        ctk.CTkLabel(
            self.content_frame,
            text=f"{used_text} / {total_text}",
            font=ctk.CTkFont(size=13)
        ).pack(pady=(0, 8))

        # Progress bar
        progress = ctk.CTkProgressBar(self.content_frame, height=10)
        progress.pack(fill="x", pady=(0, 8))
        progress.set(summary['total_used_percentage'] / 100)

        # Usage percentage
        percentage_text = f"{summary['total_used_percentage']:.1f}% used"

        if summary['total_used_percentage'] >= 95:
            text_color = "red"
        elif summary['total_used_percentage'] >= 80:
            text_color = "orange"
        else:
            text_color = "gray"

        ctk.CTkLabel(
            self.content_frame,
            text=percentage_text,
            font=ctk.CTkFont(size=11),
            text_color=text_color
        ).pack()

        # Alert if needed
        if summary['critical'] > 0 or summary['warnings'] > 0:
            alert_text = f"⚠ {summary['critical'] + summary['warnings']} alert(s)"
            ctk.CTkLabel(
                self.content_frame,
                text=alert_text,
                font=ctk.CTkFont(size=10),
                text_color="orange"
            ).pack(pady=(8, 0))

    def refresh(self):
        """Refresh display."""
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        self._load_data()
