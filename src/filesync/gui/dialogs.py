"""Reusable dialogs for the GUI."""

import customtkinter as ctk
from tkinter import messagebox
from ..encryption.crypto import key_manager


class PassphraseDialog(ctk.CTkToplevel):
    """Dialog for entering encryption passphrase."""

    def __init__(self, parent):
        super().__init__(parent)

        self.title("Encryption Passphrase")
        self.geometry("500x300")
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
            text="Enter Encryption Passphrase",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title.pack(pady=(30, 10))

        # Info
        info = ctk.CTkLabel(
            self,
            text="Your passphrase will be used to encrypt files.\n"
                 "Use a strong passphrase with at least 12 characters.",
            font=ctk.CTkFont(size=12)
        )
        info.pack(pady=(0, 20))

        # Passphrase entry
        self.passphrase_entry = ctk.CTkEntry(
            self,
            placeholder_text="Enter passphrase",
            show="*",
            width=400,
            height=40
        )
        self.passphrase_entry.pack(pady=10)

        # Confirm passphrase entry
        self.confirm_entry = ctk.CTkEntry(
            self,
            placeholder_text="Confirm passphrase",
            show="*",
            width=400,
            height=40
        )
        self.confirm_entry.pack(pady=10)

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=30)

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
            text="Set Passphrase",
            command=self._set_passphrase,
            width=120,
            height=40
        ).pack(side="left", padx=10)

        # Bind enter key
        self.confirm_entry.bind("<Return>", lambda e: self._set_passphrase())

    def _set_passphrase(self):
        """Validate and set the passphrase."""
        passphrase = self.passphrase_entry.get()
        confirm = self.confirm_entry.get()

        if not passphrase:
            messagebox.showerror("Error", "Passphrase cannot be empty", parent=self)
            return

        if passphrase != confirm:
            messagebox.showerror("Error", "Passphrases do not match", parent=self)
            return

        # Validate strength
        valid, message = key_manager.validate_passphrase_strength(passphrase)
        if not valid:
            messagebox.showerror("Error", message, parent=self)
            return

        # Set passphrase
        key_manager.set_master_passphrase(passphrase)
        messagebox.showinfo(
            "Success",
            "Encryption passphrase set successfully",
            parent=self
        )
        self.destroy()


class ProgressDialog(ctk.CTkToplevel):
    """Dialog showing progress for long-running operations."""

    def __init__(self, parent, title: str, message: str):
        super().__init__(parent)

        self.title(title)
        self.geometry("400x200")
        self.resizable(False, False)

        # Make modal
        self.transient(parent)
        self.grab_set()

        # Message
        self.message_label = ctk.CTkLabel(
            self,
            text=message,
            font=ctk.CTkFont(size=14)
        )
        self.message_label.pack(pady=(30, 20))

        # Progress bar
        self.progress = ctk.CTkProgressBar(self, width=300)
        self.progress.pack(pady=20)
        self.progress.set(0)

        # Status label
        self.status_label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=12)
        )
        self.status_label.pack(pady=10)

    def update_progress(self, value: float, status: str = ""):
        """Update progress bar and status."""
        self.progress.set(value)
        if status:
            self.status_label.configure(text=status)
        self.update()

    def set_status(self, status: str):
        """Update status text."""
        self.status_label.configure(text=status)
        self.update()


class ConfirmDialog(ctk.CTkToplevel):
    """Confirmation dialog."""

    def __init__(self, parent, title: str, message: str, callback):
        super().__init__(parent)

        self.title(title)
        self.geometry("400x200")
        self.resizable(False, False)

        self.callback = callback
        self.result = False

        # Make modal
        self.transient(parent)
        self.grab_set()

        # Message
        ctk.CTkLabel(
            self,
            text=message,
            font=ctk.CTkFont(size=14),
            wraplength=350
        ).pack(pady=(30, 30))

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=20)

        ctk.CTkButton(
            btn_frame,
            text="Cancel",
            command=self._cancel,
            fg_color="gray40",
            hover_color="gray50",
            width=120,
            height=40
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            btn_frame,
            text="Confirm",
            command=self._confirm,
            width=120,
            height=40
        ).pack(side="left", padx=10)

    def _cancel(self):
        """Cancel action."""
        self.result = False
        self.destroy()

    def _confirm(self):
        """Confirm action."""
        self.result = True
        self.callback()
        self.destroy()
