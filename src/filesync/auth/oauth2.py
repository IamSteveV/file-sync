"""OAuth2 authentication manager for cloud providers."""

import json
import webbrowser
from pathlib import Path
from typing import Optional, Dict, Any
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading


class OAuth2Manager:
    """Manages OAuth2 authentication flows for cloud providers."""

    def __init__(self, credentials_dir: Path):
        """
        Initialize OAuth2 manager.

        Args:
            credentials_dir: Directory to store OAuth2 credentials
        """
        self.credentials_dir = Path(credentials_dir)
        self.credentials_dir.mkdir(parents=True, exist_ok=True)
        self.redirect_port = 8080
        self.auth_code: Optional[str] = None
        self.auth_server: Optional[HTTPServer] = None

    def get_credentials_path(self, provider: str) -> Path:
        """Get path to credentials file for a provider."""
        return self.credentials_dir / f"{provider}-credentials.json"

    def has_credentials(self, provider: str) -> bool:
        """Check if credentials exist for a provider."""
        return self.get_credentials_path(provider).exists()

    def load_credentials(self, provider: str) -> Optional[Dict[str, Any]]:
        """Load credentials for a provider."""
        creds_path = self.get_credentials_path(provider)
        if creds_path.exists():
            with open(creds_path) as f:
                return json.load(f)
        return None

    def save_credentials(self, provider: str, credentials: Dict[str, Any]) -> None:
        """Save credentials for a provider."""
        creds_path = self.get_credentials_path(provider)
        with open(creds_path, "w") as f:
            json.dump(credentials, f, indent=2)

    def delete_credentials(self, provider: str) -> bool:
        """Delete credentials for a provider."""
        creds_path = self.get_credentials_path(provider)
        if creds_path.exists():
            creds_path.unlink()
            return True
        return False

    def start_oauth_flow(self, provider: str, client_id: str,
                        client_secret: str, scopes: list) -> Optional[str]:
        """
        Start OAuth2 authorization flow.

        Args:
            provider: Provider name (gdrive, onedrive, box)
            client_id: OAuth2 client ID
            client_secret: OAuth2 client secret
            scopes: List of OAuth2 scopes

        Returns:
            Authorization URL or None if failed
        """
        if provider == "gdrive":
            return self._start_google_oauth(client_id, scopes)
        elif provider == "onedrive":
            return self._start_onedrive_oauth(client_id, scopes)
        elif provider == "box":
            return self._start_box_oauth(client_id)
        else:
            return None

    def _start_google_oauth(self, client_id: str, scopes: list) -> str:
        """Start Google Drive OAuth2 flow."""
        redirect_uri = f"http://localhost:{self.redirect_port}"
        scope_str = " ".join(scopes)

        auth_url = (
            f"https://accounts.google.com/o/oauth2/v2/auth"
            f"?client_id={client_id}"
            f"&redirect_uri={redirect_uri}"
            f"&response_type=code"
            f"&scope={scope_str}"
            f"&access_type=offline"
            f"&prompt=consent"
        )
        return auth_url

    def _start_onedrive_oauth(self, client_id: str, scopes: list) -> str:
        """Start OneDrive OAuth2 flow."""
        redirect_uri = f"http://localhost:{self.redirect_port}"
        scope_str = " ".join(scopes)

        auth_url = (
            f"https://login.microsoftonline.com/common/oauth2/v2.0/authorize"
            f"?client_id={client_id}"
            f"&redirect_uri={redirect_uri}"
            f"&response_type=code"
            f"&scope={scope_str}"
            f"&response_mode=query"
        )
        return auth_url

    def _start_box_oauth(self, client_id: str) -> str:
        """Start Box OAuth2 flow."""
        redirect_uri = f"http://localhost:{self.redirect_port}"

        auth_url = (
            f"https://account.box.com/api/oauth2/authorize"
            f"?client_id={client_id}"
            f"&redirect_uri={redirect_uri}"
            f"&response_type=code"
        )
        return auth_url

    def wait_for_callback(self, timeout: int = 120) -> Optional[str]:
        """
        Start local server and wait for OAuth2 callback.

        Args:
            timeout: Timeout in seconds

        Returns:
            Authorization code or None if timeout/error
        """
        self.auth_code = None

        # Create handler class with access to this instance
        manager = self

        class CallbackHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                # Parse query parameters
                query = urlparse(self.path).query
                params = parse_qs(query)

                if "code" in params:
                    manager.auth_code = params["code"][0]

                    # Send success response
                    self.send_response(200)
                    self.send_header("Content-type", "text/html")
                    self.end_headers()
                    self.wfile.write(b"""
                        <html>
                        <head><title>Authorization Successful</title></head>
                        <body>
                        <h1>Authorization Successful!</h1>
                        <p>You can close this window and return to FileSync.</p>
                        <script>window.close();</script>
                        </body>
                        </html>
                    """)
                else:
                    # Error response
                    self.send_response(400)
                    self.send_header("Content-type", "text/html")
                    self.end_headers()
                    self.wfile.write(b"""
                        <html>
                        <head><title>Authorization Failed</title></head>
                        <body>
                        <h1>Authorization Failed</h1>
                        <p>Please try again.</p>
                        </body>
                        </html>
                    """)

            def log_message(self, format, *args):
                # Suppress log messages
                pass

        # Start server
        try:
            self.auth_server = HTTPServer(("localhost", self.redirect_port), CallbackHandler)

            # Run server in thread with timeout
            def run_server():
                self.auth_server.timeout = timeout
                self.auth_server.handle_request()

            server_thread = threading.Thread(target=run_server, daemon=True)
            server_thread.start()
            server_thread.join(timeout=timeout)

            return self.auth_code

        except Exception as e:
            print(f"OAuth callback server error: {e}")
            return None

        finally:
            if self.auth_server:
                try:
                    self.auth_server.server_close()
                except:
                    pass

    def exchange_code_for_token(self, provider: str, code: str,
                               client_id: str, client_secret: str) -> Optional[Dict[str, Any]]:
        """
        Exchange authorization code for access token.

        Args:
            provider: Provider name
            code: Authorization code
            client_id: OAuth2 client ID
            client_secret: OAuth2 client secret

        Returns:
            Token data or None if failed
        """
        # This is a simplified implementation
        # In production, use requests library to make actual API calls

        redirect_uri = f"http://localhost:{self.redirect_port}"

        if provider == "gdrive":
            token_url = "https://oauth2.googleapis.com/token"
        elif provider == "onedrive":
            token_url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
        elif provider == "box":
            token_url = "https://api.box.com/oauth2/token"
        else:
            return None

        # Token data structure (simplified)
        token_data = {
            "provider": provider,
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "redirect_uri": redirect_uri,
            "token_url": token_url,
            "status": "pending_exchange",  # In real impl, make API call here
        }

        return token_data

    def complete_oauth_flow(self, provider: str, client_id: str,
                           client_secret: str, scopes: list) -> bool:
        """
        Complete full OAuth2 flow: authorize and exchange token.

        Args:
            provider: Provider name
            client_id: OAuth2 client ID
            client_secret: OAuth2 client secret
            scopes: List of OAuth2 scopes

        Returns:
            True if successful
        """
        # Start OAuth flow
        auth_url = self.start_oauth_flow(provider, client_id, client_secret, scopes)
        if not auth_url:
            return False

        # Open browser
        webbrowser.open(auth_url)

        # Wait for callback
        auth_code = self.wait_for_callback()
        if not auth_code:
            return False

        # Exchange code for token
        token_data = self.exchange_code_for_token(
            provider, auth_code, client_id, client_secret
        )
        if not token_data:
            return False

        # Save credentials
        self.save_credentials(provider, token_data)
        return True


# Default OAuth2 scopes for each provider
DEFAULT_SCOPES = {
    "gdrive": [
        "https://www.googleapis.com/auth/drive.file",
        "https://www.googleapis.com/auth/drive.metadata.readonly",
    ],
    "onedrive": [
        "Files.ReadWrite.All",
        "offline_access",
    ],
    "box": [
        "root_readwrite",
    ],
}
