"""Authentication module for cloud providers."""

from .oauth2 import OAuth2Manager, DEFAULT_SCOPES

__all__ = ["OAuth2Manager", "DEFAULT_SCOPES"]
