"""Base storage provider interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any


@dataclass
class FileInfo:
    """Information about a file on a storage provider."""

    path: str
    name: str
    size: int
    modified_at: datetime
    is_directory: bool = False
    mime_type: Optional[str] = None
    checksum: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class QuotaInfo:
    """Storage quota information."""

    total_bytes: int
    used_bytes: int
    available_bytes: int

    @property
    def usage_percent(self) -> float:
        """Calculate usage percentage."""
        if self.total_bytes == 0:
            return 0.0
        return (self.used_bytes / self.total_bytes) * 100


@dataclass
class UploadResult:
    """Result of an upload operation."""

    success: bool
    remote_path: str
    size: int
    checksum: Optional[str] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class DownloadResult:
    """Result of a download operation."""

    success: bool
    local_path: str
    size: int
    checksum: Optional[str] = None
    error: Optional[str] = None


@dataclass
class DeleteResult:
    """Result of a delete operation."""

    success: bool
    path: str
    error: Optional[str] = None


class StorageProvider(ABC):
    """
    Abstract base class for storage providers.

    All storage providers (Google Drive, OneDrive, Box, Proton) must
    implement this interface to ensure consistent behavior.
    """

    def __init__(self, name: str):
        """
        Initialize the storage provider.

        Args:
            name: Name of the provider (gdrive, onedrive, box, proton, local)
        """
        self.name = name
        self._authenticated = False

    @abstractmethod
    def authenticate(self, credentials: Dict[str, Any]) -> bool:
        """
        Authenticate with the storage provider.

        Args:
            credentials: Provider-specific credentials

        Returns:
            True if authentication successful
        """
        pass

    @abstractmethod
    def upload(
        self,
        local_path: str | Path,
        remote_path: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> UploadResult:
        """
        Upload a file to the storage provider.

        Args:
            local_path: Path to the local file
            remote_path: Destination path on the provider
            metadata: Optional metadata to attach to the file

        Returns:
            UploadResult with status and details
        """
        pass

    @abstractmethod
    def download(self, remote_path: str, local_path: str | Path) -> DownloadResult:
        """
        Download a file from the storage provider.

        Args:
            remote_path: Path to the file on the provider
            local_path: Destination path for the downloaded file

        Returns:
            DownloadResult with status and details
        """
        pass

    @abstractmethod
    def delete(self, remote_path: str) -> DeleteResult:
        """
        Delete a file from the storage provider.

        Args:
            remote_path: Path to the file on the provider

        Returns:
            DeleteResult with status
        """
        pass

    @abstractmethod
    def list(self, remote_path: str, recursive: bool = False) -> List[FileInfo]:
        """
        List files in a directory on the storage provider.

        Args:
            remote_path: Path to the directory
            recursive: If True, list files recursively

        Returns:
            List of FileInfo objects
        """
        pass

    @abstractmethod
    def get_metadata(self, remote_path: str) -> Optional[FileInfo]:
        """
        Get metadata for a specific file.

        Args:
            remote_path: Path to the file on the provider

        Returns:
            FileInfo object or None if not found
        """
        pass

    @abstractmethod
    def get_quota(self) -> QuotaInfo:
        """
        Get storage quota information.

        Returns:
            QuotaInfo with quota details
        """
        pass

    @abstractmethod
    def exists(self, remote_path: str) -> bool:
        """
        Check if a file or directory exists.

        Args:
            remote_path: Path to check

        Returns:
            True if exists
        """
        pass

    def is_authenticated(self) -> bool:
        """Check if the provider is authenticated."""
        return self._authenticated

    def create_directory(self, remote_path: str) -> bool:
        """
        Create a directory on the storage provider.

        Default implementation - providers can override.

        Args:
            remote_path: Path to the directory to create

        Returns:
            True if created successfully
        """
        # Default: not supported
        return False

    def move(self, old_path: str, new_path: str) -> bool:
        """
        Move/rename a file on the storage provider.

        Default implementation - providers can override.

        Args:
            old_path: Current path
            new_path: New path

        Returns:
            True if moved successfully
        """
        # Default: not supported
        return False

    def copy(self, source_path: str, dest_path: str) -> bool:
        """
        Copy a file on the storage provider.

        Default implementation - providers can override.

        Args:
            source_path: Source path
            dest_path: Destination path

        Returns:
            True if copied successfully
        """
        # Default: not supported
        return False

    def validate_path(self, path: str) -> bool:
        """
        Validate that a path is valid for this provider.

        Args:
            path: Path to validate

        Returns:
            True if valid
        """
        # Basic validation - no empty paths
        if not path or not path.strip():
            return False

        # Provider-specific validation can override this
        return True

    def __repr__(self) -> str:
        """String representation."""
        auth_status = "authenticated" if self._authenticated else "not authenticated"
        return f"{self.__class__.__name__}(name={self.name}, {auth_status})"
