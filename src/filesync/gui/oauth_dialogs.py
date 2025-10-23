"""OAuth2 configuration dialogs for cloud providers."""

import customtkinter as ctk
from tkinter import messagebox
import threading
from pathlib import Path
from ..auth.oauth2 import OAuth2Manager, DEFAULT_SCOPES


class OAuth2ConfigDialog(ctk.CTkToplevel):
    """Dialog for configuring OAuth2 for a cloud provider."""

    def __init__(self, parent, provider: str, oauth_manager: OAuth2Manager):
        super().__init__(parent)

        self.provider = provider
        self.oauth_manager = oauth_manager
        self.success = False

        provider_names = {
            "gdrive": "Google Drive",
            "onedrive": "Microsoft OneDrive",
            "box": "Box",
        }

        self.provider_name = provider_names.get(provider, provider)

        self.title(f"Configure {self.provider_name}")
        self.geometry("600x500")
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
            text=f"Connect to {self.provider_name}",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.pack(pady=(30, 10))

        # Instructions
        instructions = self._get_instructions()
        info_frame = ctk.CTkFrame(self)
        info_frame.pack(fill="x", padx=20, pady=20)

        ctk.CTkLabel(
            info_frame,
            text=instructions,
            font=ctk.CTkFont(size=12),
            justify="left",
            wraplength=540
        ).pack(padx=15, pady=15)

        # Client ID
        ctk.CTkLabel(
            self,
            text="Client ID:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=20, pady=(10, 5))

        self.client_id_entry = ctk.CTkEntry(
            self,
            placeholder_text="Enter OAuth2 Client ID",
            width=560,
            height=40
        )
        self.client_id_entry.pack(padx=20, pady=(0, 15))

        # Client Secret
        ctk.CTkLabel(
            self,
            text="Client Secret:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=20, pady=(0, 5))

        self.client_secret_entry = ctk.CTkEntry(
            self,
            placeholder_text="Enter OAuth2 Client Secret",
            width=560,
            height=40,
            show="*"
        )
        self.client_secret_entry.pack(padx=20, pady=(0, 15))

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=30)

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
            text="Authorize",
            command=self._start_authorization,
            width=140,
            height=40
        ).pack(side="left", padx=10)

        # Help link
        help_btn = ctk.CTkButton(
            self,
            text="📖 Setup Guide",
            command=self._show_setup_guide,
            fg_color="transparent",
            hover_color="gray30",
            width=120,
            height=30
        )
        help_btn.pack(pady=(0, 20))

    def _get_instructions(self) -> str:
        """Get provider-specific instructions."""
        if self.provider == "gdrive":
            return (
                "To connect Google Drive:\n\n"
                "1. Go to Google Cloud Console\n"
                "2. Create a new project or select existing\n"
                "3. Enable Google Drive API\n"
                "4. Create OAuth 2.0 credentials (Desktop app)\n"
                "5. Add http://localhost:8080 as redirect URI\n"
                "6. Copy Client ID and Client Secret below"
            )
        elif self.provider == "onedrive":
            return (
                "To connect OneDrive:\n\n"
                "1. Go to Azure Portal (portal.azure.com)\n"
                "2. Register a new app in Azure AD\n"
                "3. Add http://localhost:8080 as redirect URI\n"
                "4. Grant Files.ReadWrite.All permissions\n"
                "5. Copy Application (client) ID and create a secret\n"
                "6. Enter credentials below"
            )
        elif self.provider == "box":
            return (
                "To connect Box:\n\n"
                "1. Go to Box Developers Console\n"
                "2. Create a new Custom App (OAuth 2.0)\n"
                "3. Add http://localhost:8080 as redirect URI\n"
                "4. Grant necessary scopes\n"
                "5. Copy Client ID and Client Secret\n"
                "6. Enter credentials below"
            )
        else:
            return "Enter your OAuth2 credentials below."

    def _show_setup_guide(self):
        """Show detailed setup guide."""
        SetupGuideDialog(self, self.provider)

    def _start_authorization(self):
        """Start OAuth2 authorization flow."""
        client_id = self.client_id_entry.get().strip()
        client_secret = self.client_secret_entry.get().strip()

        if not client_id or not client_secret:
            messagebox.showerror(
                "Error",
                "Please enter both Client ID and Client Secret",
                parent=self
            )
            return

        # Show progress
        progress = ctk.CTkToplevel(self)
        progress.title("Authorizing...")
        progress.geometry("400x200")
        progress.resizable(False, False)
        progress.transient(self)
        progress.grab_set()

        ctk.CTkLabel(
            progress,
            text="Opening browser for authorization...",
            font=ctk.CTkFont(size=14)
        ).pack(pady=(40, 20))

        ctk.CTkLabel(
            progress,
            text="Please complete authorization in your browser.\nThis window will close automatically.",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        ).pack(pady=10)

        progress_bar = ctk.CTkProgressBar(progress, mode="indeterminate")
        progress_bar.pack(pady=20)
        progress_bar.start()

        # Run authorization in thread
        def authorize():
            try:
                scopes = DEFAULT_SCOPES.get(self.provider, [])
                success = self.oauth_manager.complete_oauth_flow(
                    self.provider,
                    client_id,
                    client_secret,
                    scopes
                )

                # Update UI from main thread
                self.after(0, lambda: self._authorization_complete(progress, success))

            except Exception as e:
                self.after(0, lambda: self._authorization_complete(progress, False, str(e)))

        thread = threading.Thread(target=authorize, daemon=True)
        thread.start()

    def _authorization_complete(self, progress_window, success: bool, error: str = None):
        """Handle authorization completion."""
        progress_window.destroy()

        if success:
            self.success = True
            messagebox.showinfo(
                "Success",
                f"{self.provider_name} connected successfully!",
                parent=self
            )
            self.destroy()
        else:
            error_msg = f"Failed to authorize {self.provider_name}"
            if error:
                error_msg += f"\n\nError: {error}"
            messagebox.showerror(
                "Authorization Failed",
                error_msg,
                parent=self
            )


class SetupGuideDialog(ctk.CTkToplevel):
    """Detailed setup guide for OAuth2 configuration."""

    def __init__(self, parent, provider: str):
        super().__init__(parent)

        self.provider = provider

        provider_names = {
            "gdrive": "Google Drive",
            "onedrive": "Microsoft OneDrive",
            "box": "Box",
        }

        self.provider_name = provider_names.get(provider, provider)

        self.title(f"{self.provider_name} Setup Guide")
        self.geometry("700x600")

        # Make modal
        self.transient(parent)
        self.grab_set()

        self._create_widgets()

    def _create_widgets(self):
        """Create widgets."""
        # Title
        title = ctk.CTkLabel(
            self,
            text=f"{self.provider_name} Setup Guide",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title.pack(pady=20)

        # Scrollable content
        scroll_frame = ctk.CTkScrollableFrame(self)
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # Guide content
        guide = self._get_guide_content()

        ctk.CTkTextbox(
            scroll_frame,
            wrap="word",
            font=ctk.CTkFont(size=12)
        ).pack(fill="both", expand=True)

        # Insert guide text
        textbox = scroll_frame.winfo_children()[0]
        textbox.insert("1.0", guide)
        textbox.configure(state="disabled")

        # Close button
        ctk.CTkButton(
            self,
            text="Close",
            command=self.destroy,
            height=40
        ).pack(pady=20)

    def _get_guide_content(self) -> str:
        """Get detailed setup guide."""
        if self.provider == "gdrive":
            return """
Google Drive OAuth2 Setup Guide

Step 1: Go to Google Cloud Console
- Visit: https://console.cloud.google.com/
- Sign in with your Google account

Step 2: Create or Select Project
- Click on project dropdown at the top
- Click "New Project" or select existing project
- Give it a name (e.g., "FileSync")

Step 3: Enable Google Drive API
- In the left sidebar, go to "APIs & Services" > "Library"
- Search for "Google Drive API"
- Click on it and click "Enable"

Step 4: Create OAuth 2.0 Credentials
- Go to "APIs & Services" > "Credentials"
- Click "Create Credentials" > "OAuth client ID"
- If prompted, configure OAuth consent screen:
  * Choose "External" user type
  * Fill in app name and your email
  * Add scopes: ../auth/drive.file
  * Add test users if needed
- Choose "Desktop app" as application type
- Give it a name (e.g., "FileSync Desktop")
- Click "Create"

Step 5: Configure Redirect URI
- In OAuth 2.0 Client IDs list, click on your client
- Under "Authorized redirect URIs", add:
  http://localhost:8080
- Click "Save"

Step 6: Get Credentials
- Click "Download JSON" or copy:
  * Client ID
  * Client Secret
- Paste these into FileSync

Security Notes:
- Keep credentials secure
- Don't share Client Secret
- Review app permissions periodically
- Use OAuth consent screen to limit access
"""
        elif self.provider == "onedrive":
            return """
OneDrive OAuth2 Setup Guide

Step 1: Go to Azure Portal
- Visit: https://portal.azure.com/
- Sign in with Microsoft account

Step 2: Register Application
- Go to "Azure Active Directory"
- Click "App registrations" in left menu
- Click "New registration"
- Enter name (e.g., "FileSync")
- Choose "Accounts in any organizational directory and personal Microsoft accounts"
- Add redirect URI:
  * Platform: Web
  * URI: http://localhost:8080
- Click "Register"

Step 3: Copy Application ID
- On the Overview page, copy:
  * Application (client) ID
- This is your Client ID

Step 4: Create Client Secret
- Go to "Certificates & secrets"
- Click "New client secret"
- Enter description (e.g., "FileSync Desktop")
- Choose expiration period
- Click "Add"
- Copy the secret VALUE immediately (you won't see it again)
- This is your Client Secret

Step 5: Configure API Permissions
- Go to "API permissions"
- Click "Add a permission"
- Choose "Microsoft Graph"
- Choose "Delegated permissions"
- Add these scopes:
  * Files.ReadWrite.All
  * offline_access
- Click "Add permissions"
- Click "Grant admin consent" if available

Step 6: Enter Credentials
- Paste Application ID as Client ID
- Paste secret as Client Secret in FileSync

Important Notes:
- Client secrets expire - set reminders
- Use least privilege principle
- Review permissions regularly
- Store credentials securely
"""
        elif self.provider == "box":
            return """
Box OAuth2 Setup Guide

Step 1: Go to Box Developers Console
- Visit: https://app.box.com/developers/console
- Sign in with Box account
- If prompted, enable 2-factor authentication

Step 2: Create Custom App
- Click "Create New App"
- Choose "Custom App"
- Choose "User Authentication (OAuth 2.0)"
- Give it a name (e.g., "FileSync")
- Click "Create App"

Step 3: Configure OAuth 2.0
- In app configuration, go to "Configuration" tab
- Under "OAuth 2.0 Redirect URI", add:
  http://localhost:8080
- Click "Save Changes"

Step 4: Set Application Scopes
- Scroll to "Application Scopes"
- Check required permissions:
  * Read and write all files and folders
  * Manage users
- Click "Save Changes"

Step 5: Get Credentials
- At the top of Configuration tab:
  * Copy "Client ID"
  * Copy "Client Secret"
- These are your OAuth credentials

Step 6: Enable App
- At the top right, ensure app is enabled
- Authorization Status should be "Enabled"

Step 7: Enter in FileSync
- Paste Client ID and Client Secret
- Click "Authorize"

Security Best Practices:
- Regularly rotate client secrets
- Review app permissions
- Monitor OAuth token usage
- Use Box's security features
"""
        else:
            return f"Setup guide for {self.provider} coming soon."
