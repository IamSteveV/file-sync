"""Redundancy validation view."""

import customtkinter as ctk
from tkinter import messagebox
from ..core.manifest import ManifestManager
from ..core.redundancy import RedundancyManager
from ..core.sync import SyncEngine
from .dialogs import ProgressDialog


class ValidationFrame(ctk.CTkFrame):
    """Redundancy validation interface."""

    def __init__(self, parent, manifest: ManifestManager,
                 redundancy: RedundancyManager, sync: SyncEngine):
        super().__init__(parent)
        self.manifest = manifest
        self.redundancy = redundancy
        self.sync = sync

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self._create_widgets()
        self._load_validation()

    def _create_widgets(self):
        """Create widgets."""
        # Title
        title = ctk.CTkLabel(
            self,
            text="Redundancy Validation",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title.grid(row=0, column=0, sticky="w", pady=(0, 20))

        # Action buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=1, column=0, sticky="ew", pady=(0, 20))

        ctk.CTkButton(
            btn_frame,
            text="🔄 Refresh",
            command=self._load_validation,
            height=35
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            btn_frame,
            text="✓ Verify All Files",
            command=self._verify_all,
            height=35,
            fg_color="green",
            hover_color="darkgreen"
        ).pack(side="left", padx=(0, 10))

        # Results
        self._create_results_section()

    def _create_results_section(self):
        """Create results section."""
        results_frame = ctk.CTkScrollableFrame(self)
        results_frame.grid(row=2, column=0, sticky="nsew")
        results_frame.grid_columnconfigure(0, weight=1)

        # Summary
        self.summary_frame = ctk.CTkFrame(results_frame)
        self.summary_frame.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(
            self.summary_frame,
            text="Summary",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(anchor="w", padx=20, pady=(15, 10))

        self.summary_text = ctk.CTkTextbox(self.summary_frame, height=120)
        self.summary_text.pack(fill="x", padx=20, pady=(0, 15))

        # Non-compliant files
        self.issues_frame = ctk.CTkFrame(results_frame)
        self.issues_frame.pack(fill="both", expand=True)

        ctk.CTkLabel(
            self.issues_frame,
            text="Files Needing Attention",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(anchor="w", padx=20, pady=(15, 10))

        self.issues_text = ctk.CTkTextbox(self.issues_frame, height=300)
        self.issues_text.pack(fill="both", expand=True, padx=20, pady=(0, 15))

    def _load_validation(self):
        """Load and display validation results."""
        if not self.manifest or not self.redundancy:
            return

        entries = self.manifest.get_all_entries()
        report = self.redundancy.generate_redundancy_report(entries)

        # Update summary
        self.summary_text.delete("1.0", "end")
        self.summary_text.insert("end", f"Total files: {report['total_files']}\n")
        self.summary_text.insert("end", f"Compliant: {report['compliant']} ✓\n")
        self.summary_text.insert("end", f"Non-compliant: {report['non_compliant']} ⚠\n")
        self.summary_text.insert("end", f"Average score: {report['average_score']:.1%}\n")

        if report['critical_issues']:
            self.summary_text.insert(
                "end",
                f"\n🔴 {len(report['critical_issues'])} critical issues!\n"
            )

        # Update issues
        self.issues_text.delete("1.0", "end")

        if report['non_compliant'] == 0:
            self.issues_text.insert(
                "end",
                "✓ All files meet their tier requirements!\n\n"
                "No action needed."
            )
        else:
            non_compliant = self.redundancy.get_non_compliant_entries(entries)

            for i, plan in enumerate(non_compliant[:50], 1):  # Show first 50
                entry = plan.entry
                self.issues_text.insert(
                    "end",
                    f"{i}. {entry.file_name} ({entry.tier.name})\n"
                )
                self.issues_text.insert(
                    "end",
                    f"   Current: {plan.current_copies} copies on "
                    f"{len(plan.current_providers)} providers\n"
                )
                self.issues_text.insert(
                    "end",
                    f"   Required: {plan.required_copies} copies on "
                    f"{plan.required_providers} providers\n"
                )
                self.issues_text.insert(
                    "end",
                    f"   Actions: {', '.join(plan.actions)}\n\n"
                )

            if len(non_compliant) > 50:
                self.issues_text.insert(
                    "end",
                    f"... and {len(non_compliant) - 50} more files\n"
                )

    def _verify_all(self):
        """Verify all file locations."""
        if not self.sync:
            messagebox.showerror(
                "Error",
                "Sync engine not available",
                parent=self
            )
            return

        # Create progress dialog
        progress = ProgressDialog(
            self,
            "Verifying Files",
            "Checking file integrity across all providers..."
        )

        try:
            # Run verification
            report = self.sync.verify_all_locations()

            progress.destroy()

            # Show results
            messagebox.showinfo(
                "Verification Complete",
                f"Total locations: {report['total_locations']}\n"
                f"Verified: {report['verified']} ✓\n"
                f"Failed: {report['failed']} ✗\n\n"
                f"Check the validation view for details.",
                parent=self
            )

            # Refresh
            self._load_validation()

        except Exception as e:
            progress.destroy()
            messagebox.showerror(
                "Error",
                f"Verification failed:\n{str(e)}",
                parent=self
            )
