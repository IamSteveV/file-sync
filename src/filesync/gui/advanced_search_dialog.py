"""Advanced search dialog with comprehensive filtering options."""

import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from ..models.tier import Tier


class AdvancedSearchDialog(ctk.CTkToplevel):
    """Advanced search dialog with multiple filter criteria."""

    def __init__(self, parent, on_search_callback):
        """
        Initialize advanced search dialog.

        Args:
            parent: Parent window
            on_search_callback: Function to call with search criteria
        """
        super().__init__(parent)

        self.on_search_callback = on_search_callback

        self.title("Advanced Search")
        self.geometry("600x700")

        # Make modal
        self.transient(parent)
        self.grab_set()

        self._create_widgets()

    def _create_widgets(self):
        """Create dialog widgets."""
        # Header
        header = ctk.CTkLabel(
            self,
            text="Advanced Search",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        header.pack(pady=(20, 10))

        ctk.CTkLabel(
            self,
            text="Build complex search queries with multiple criteria",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        ).pack(pady=(0, 20))

        # Scrollable content
        scroll_frame = ctk.CTkScrollableFrame(self)
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # File name/content search
        self._create_text_search_section(scroll_frame)

        # Date range filters
        self._create_date_filter_section(scroll_frame)

        # Size range filters
        self._create_size_filter_section(scroll_frame)

        # Tier filters
        self._create_tier_filter_section(scroll_frame)

        # Tags filters
        self._create_tags_filter_section(scroll_frame)

        # Provider filters
        self._create_provider_filter_section(scroll_frame)

        # Encryption filter
        self._create_encryption_filter_section(scroll_frame)

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=20)

        ctk.CTkButton(
            btn_frame,
            text="Clear All",
            command=self._clear_filters,
            fg_color="gray40",
            hover_color="gray50",
            width=120,
            height=40
        ).pack(side="left", padx=10)

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
            text="Search",
            command=self._execute_search,
            width=120,
            height=40
        ).pack(side="left", padx=10)

    def _create_text_search_section(self, parent):
        """Create text search section."""
        section = ctk.CTkFrame(parent)
        section.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            section,
            text="Text Search",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=15, pady=(15, 10))

        # Filename search
        ctk.CTkLabel(
            section,
            text="File Name:",
            font=ctk.CTkFont(size=12)
        ).pack(anchor="w", padx=15, pady=(0, 5))

        self.filename_entry = ctk.CTkEntry(
            section,
            placeholder_text="Enter filename or pattern (supports wildcards *)",
            height=35
        )
        self.filename_entry.pack(fill="x", padx=15, pady=(0, 10))

        # Tags search
        ctk.CTkLabel(
            section,
            text="Tags:",
            font=ctk.CTkFont(size=12)
        ).pack(anchor="w", padx=15, pady=(0, 5))

        self.tags_entry = ctk.CTkEntry(
            section,
            placeholder_text="Enter tags (comma-separated)",
            height=35
        )
        self.tags_entry.pack(fill="x", padx=15, pady=(0, 10))

        # Tag match mode
        self.tag_match_var = ctk.StringVar(value="any")
        tag_mode_frame = ctk.CTkFrame(section, fg_color="transparent")
        tag_mode_frame.pack(fill="x", padx=30, pady=(0, 15))

        ctk.CTkRadioButton(
            tag_mode_frame,
            text="Match ANY tag",
            variable=self.tag_match_var,
            value="any"
        ).pack(side="left", padx=(0, 15))

        ctk.CTkRadioButton(
            tag_mode_frame,
            text="Match ALL tags",
            variable=self.tag_match_var,
            value="all"
        ).pack(side="left")

    def _create_date_filter_section(self, parent):
        """Create date filter section."""
        section = ctk.CTkFrame(parent)
        section.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            section,
            text="Date Range",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=15, pady=(15, 10))

        # Date type selector
        self.date_type_var = ctk.StringVar(value="created")
        date_type_frame = ctk.CTkFrame(section, fg_color="transparent")
        date_type_frame.pack(fill="x", padx=15, pady=(0, 10))

        ctk.CTkRadioButton(
            date_type_frame,
            text="Created",
            variable=self.date_type_var,
            value="created"
        ).pack(side="left", padx=(0, 15))

        ctk.CTkRadioButton(
            date_type_frame,
            text="Modified",
            variable=self.date_type_var,
            value="modified"
        ).pack(side="left")

        # Quick date ranges
        ctk.CTkLabel(
            section,
            text="Quick Ranges:",
            font=ctk.CTkFont(size=11)
        ).pack(anchor="w", padx=15, pady=(0, 5))

        quick_frame = ctk.CTkFrame(section, fg_color="transparent")
        quick_frame.pack(fill="x", padx=15, pady=(0, 10))

        quick_ranges = [
            ("Today", 0),
            ("Last 7 days", 7),
            ("Last 30 days", 30),
            ("Last 90 days", 90),
        ]

        for label, days in quick_ranges:
            ctk.CTkButton(
                quick_frame,
                text=label,
                command=lambda d=days: self._set_quick_date_range(d),
                width=100,
                height=30,
                fg_color="gray40",
                hover_color="gray50"
            ).pack(side="left", padx=5)

        # Custom date range
        dates_frame = ctk.CTkFrame(section, fg_color="transparent")
        dates_frame.pack(fill="x", padx=15, pady=(10, 15))

        # From date
        from_frame = ctk.CTkFrame(dates_frame, fg_color="transparent")
        from_frame.pack(side="left", expand=True, fill="x", padx=(0, 10))

        ctk.CTkLabel(
            from_frame,
            text="From:",
            font=ctk.CTkFont(size=11)
        ).pack(anchor="w")

        self.date_from_entry = ctk.CTkEntry(
            from_frame,
            placeholder_text="YYYY-MM-DD",
            height=35
        )
        self.date_from_entry.pack(fill="x", pady=(5, 0))

        # To date
        to_frame = ctk.CTkFrame(dates_frame, fg_color="transparent")
        to_frame.pack(side="left", expand=True, fill="x")

        ctk.CTkLabel(
            to_frame,
            text="To:",
            font=ctk.CTkFont(size=11)
        ).pack(anchor="w")

        self.date_to_entry = ctk.CTkEntry(
            to_frame,
            placeholder_text="YYYY-MM-DD",
            height=35
        )
        self.date_to_entry.pack(fill="x", pady=(5, 0))

    def _create_size_filter_section(self, parent):
        """Create file size filter section."""
        section = ctk.CTkFrame(parent)
        section.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            section,
            text="File Size",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=15, pady=(15, 10))

        # Size range
        size_frame = ctk.CTkFrame(section, fg_color="transparent")
        size_frame.pack(fill="x", padx=15, pady=(0, 10))

        # Min size
        min_frame = ctk.CTkFrame(size_frame, fg_color="transparent")
        min_frame.pack(side="left", expand=True, fill="x", padx=(0, 10))

        ctk.CTkLabel(
            min_frame,
            text="Min Size:",
            font=ctk.CTkFont(size=11)
        ).pack(anchor="w")

        min_input_frame = ctk.CTkFrame(min_frame, fg_color="transparent")
        min_input_frame.pack(fill="x", pady=(5, 0))

        self.size_min_entry = ctk.CTkEntry(
            min_input_frame,
            placeholder_text="0",
            width=100,
            height=35
        )
        self.size_min_entry.pack(side="left", padx=(0, 5))

        self.size_min_unit = ctk.CTkOptionMenu(
            min_input_frame,
            values=["B", "KB", "MB", "GB"],
            width=70,
            height=35
        )
        self.size_min_unit.pack(side="left")
        self.size_min_unit.set("MB")

        # Max size
        max_frame = ctk.CTkFrame(size_frame, fg_color="transparent")
        max_frame.pack(side="left", expand=True, fill="x")

        ctk.CTkLabel(
            max_frame,
            text="Max Size:",
            font=ctk.CTkFont(size=11)
        ).pack(anchor="w")

        max_input_frame = ctk.CTkFrame(max_frame, fg_color="transparent")
        max_input_frame.pack(fill="x", pady=(5, 0))

        self.size_max_entry = ctk.CTkEntry(
            max_input_frame,
            placeholder_text="No limit",
            width=100,
            height=35
        )
        self.size_max_entry.pack(side="left", padx=(0, 5))

        self.size_max_unit = ctk.CTkOptionMenu(
            max_input_frame,
            values=["B", "KB", "MB", "GB"],
            width=70,
            height=35
        )
        self.size_max_unit.pack(side="left")
        self.size_max_unit.set("MB")

        # Quick size ranges
        ctk.CTkLabel(
            section,
            text="Quick Ranges:",
            font=ctk.CTkFont(size=11)
        ).pack(anchor="w", padx=15, pady=(10, 5))

        quick_size_frame = ctk.CTkFrame(section, fg_color="transparent")
        quick_size_frame.pack(fill="x", padx=15, pady=(0, 15))

        size_ranges = [
            ("< 1 MB", 0, 1, "MB"),
            ("1-10 MB", 1, 10, "MB"),
            ("10-100 MB", 10, 100, "MB"),
            ("> 100 MB", 100, None, "MB"),
        ]

        for label, min_val, max_val, unit in size_ranges:
            ctk.CTkButton(
                quick_size_frame,
                text=label,
                command=lambda mn=min_val, mx=max_val, u=unit: self._set_size_range(mn, mx, u),
                width=90,
                height=30,
                fg_color="gray40",
                hover_color="gray50"
            ).pack(side="left", padx=5)

    def _create_tier_filter_section(self, parent):
        """Create tier filter section."""
        section = ctk.CTkFrame(parent)
        section.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            section,
            text="Importance Tiers",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=15, pady=(15, 10))

        self.tier_checkboxes = {}

        for tier in Tier:
            var = ctk.BooleanVar(value=True)
            checkbox = ctk.CTkCheckBox(
                section,
                text=f"Tier {tier.value}: {tier.name.title()}",
                variable=var
            )
            checkbox.pack(anchor="w", padx=30, pady=5)
            self.tier_checkboxes[tier] = var

    def _create_tags_filter_section(self, parent):
        """Create tags filter section."""
        # This is handled in text search section
        pass

    def _create_provider_filter_section(self, parent):
        """Create provider filter section."""
        section = ctk.CTkFrame(parent)
        section.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            section,
            text="Storage Providers",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=15, pady=(15, 10))

        providers = ["local", "gdrive", "onedrive", "box", "proton"]
        self.provider_checkboxes = {}

        for provider in providers:
            var = ctk.BooleanVar(value=True)
            checkbox = ctk.CTkCheckBox(
                section,
                text=provider.title().replace("Gdrive", "Google Drive"),
                variable=var
            )
            checkbox.pack(anchor="w", padx=30, pady=5)
            self.provider_checkboxes[provider] = var

    def _create_encryption_filter_section(self, parent):
        """Create encryption filter section."""
        section = ctk.CTkFrame(parent)
        section.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            section,
            text="Encryption Status",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=15, pady=(15, 10))

        self.encryption_var = ctk.StringVar(value="all")

        options = [
            ("all", "All Files"),
            ("encrypted", "Encrypted Only"),
            ("unencrypted", "Unencrypted Only"),
        ]

        for value, label in options:
            radio = ctk.CTkRadioButton(
                section,
                text=label,
                variable=self.encryption_var,
                value=value
            )
            radio.pack(anchor="w", padx=30, pady=5)

    def _set_quick_date_range(self, days: int):
        """Set a quick date range."""
        today = datetime.now()
        if days == 0:
            from_date = today.replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            from_date = today - timedelta(days=days)

        self.date_from_entry.delete(0, 'end')
        self.date_from_entry.insert(0, from_date.strftime("%Y-%m-%d"))

        self.date_to_entry.delete(0, 'end')
        self.date_to_entry.insert(0, today.strftime("%Y-%m-%d"))

    def _set_size_range(self, min_val: Optional[float], max_val: Optional[float], unit: str):
        """Set size range."""
        self.size_min_entry.delete(0, 'end')
        if min_val is not None:
            self.size_min_entry.insert(0, str(min_val))
        self.size_min_unit.set(unit)

        self.size_max_entry.delete(0, 'end')
        if max_val is not None:
            self.size_max_entry.insert(0, str(max_val))
        self.size_max_unit.set(unit)

    def _clear_filters(self):
        """Clear all filters."""
        self.filename_entry.delete(0, 'end')
        self.tags_entry.delete(0, 'end')
        self.date_from_entry.delete(0, 'end')
        self.date_to_entry.delete(0, 'end')
        self.size_min_entry.delete(0, 'end')
        self.size_max_entry.delete(0, 'end')

        for var in self.tier_checkboxes.values():
            var.set(True)

        for var in self.provider_checkboxes.values():
            var.set(True)

        self.encryption_var.set("all")
        self.tag_match_var.set("any")

    def _execute_search(self):
        """Execute the search with current criteria."""
        criteria = self._build_search_criteria()

        # Call the callback with search criteria
        self.on_search_callback(criteria)

        # Close dialog
        self.destroy()

    def _build_search_criteria(self) -> Dict[str, Any]:
        """Build search criteria dictionary."""
        criteria = {}

        # Filename
        filename = self.filename_entry.get().strip()
        if filename:
            criteria['filename'] = filename

        # Tags
        tags = self.tags_entry.get().strip()
        if tags:
            criteria['tags'] = [t.strip() for t in tags.split(',')]
            criteria['tag_match_mode'] = self.tag_match_var.get()

        # Date range
        date_from = self.date_from_entry.get().strip()
        date_to = self.date_to_entry.get().strip()
        if date_from or date_to:
            criteria['date_type'] = self.date_type_var.get()
            if date_from:
                criteria['date_from'] = date_from
            if date_to:
                criteria['date_to'] = date_to

        # Size range
        size_min = self.size_min_entry.get().strip()
        size_max = self.size_max_entry.get().strip()
        if size_min or size_max:
            if size_min:
                criteria['size_min'] = self._convert_size_to_bytes(
                    float(size_min),
                    self.size_min_unit.get()
                )
            if size_max:
                criteria['size_max'] = self._convert_size_to_bytes(
                    float(size_max),
                    self.size_max_unit.get()
                )

        # Tiers
        selected_tiers = [
            tier.value for tier, var in self.tier_checkboxes.items()
            if var.get()
        ]
        if len(selected_tiers) < len(Tier):  # Only add if not all selected
            criteria['tiers'] = selected_tiers

        # Providers
        selected_providers = [
            provider for provider, var in self.provider_checkboxes.items()
            if var.get()
        ]
        if len(selected_providers) < len(self.provider_checkboxes):
            criteria['providers'] = selected_providers

        # Encryption
        encryption = self.encryption_var.get()
        if encryption != "all":
            criteria['encrypted'] = (encryption == "encrypted")

        return criteria

    def _convert_size_to_bytes(self, value: float, unit: str) -> int:
        """Convert size to bytes."""
        units = {
            'B': 1,
            'KB': 1024,
            'MB': 1024 ** 2,
            'GB': 1024 ** 3,
        }
        return int(value * units.get(unit, 1))
