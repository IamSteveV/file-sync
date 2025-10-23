"""Local file system storage provider."""

import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from .base import (
    StorageProvider,
    FileInfo,
    QuotaInfo,
    UploadResult,
    DownloadResult,
    DeleteResult,
)


class LocalProvider(StorageProvider):
    """
    Local file system storage provider.

    Used for offline backups and local caching.
    """

    def __init__(self, root_path: str | Path):
        """
        Initialize the local provider.

        Args:
            root_path: Root directory for storing files
        """
        super().__init__("local")
        self.root_path = Path(root_path).absolute()
        self.root_path.mkdir(parents=True, exist_ok=True)
        self._authenticated = True  # Local FS is always "authenticated"

    def authenticate(self, credentials: Dict[str, Any]) -> bool:
        """Local FS doesn't need authentication."""
        self._authenticated = True
        return True

    def upload(
        self,
        local_path: str | Path,
        remote_path: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> UploadResult:
        """Copy a file to the local storage."""
        try:
            source = Path(local_path)
            dest = self._resolve_path(remote_path)

            # Create parent directories
            dest.parent.mkdir(parents=True, exist_ok=True)

            # Copy file
            shutil.copy2(source, dest)

            size = dest.stat().st_size

            return UploadResult(
                success=True,
                remote_path=remote_path,
                size=size,
                checksum=None,  # Could calculate if needed
            )

        except Exception as e:
            return UploadResult(
                success=False, remote_path=remote_path, size=0, error=str(e)
            )

    def download(self, remote_path: str, local_path: str | Path) -> DownloadResult:
        """Copy a file from local storage to another location."""
        try:
            source = self._resolve_path(remote_path)
            dest = Path(local_path)

            if not source.exists():
                return DownloadResult(
                    success=False,
                    local_path=str(local_path),
                    size=0,
                    error="File not found",
                )

            # Create parent directories
            dest.parent.mkdir(parents=True, exist_ok=True)

            # Copy file
            shutil.copy2(source, dest)

            size = dest.stat().st_size

            return DownloadResult(
                success=True, local_path=str(local_path), size=size, checksum=None
            )

        except Exception as e:
            return DownloadResult(
                success=False, local_path=str(local_path), size=0, error=str(e)
            )

    def delete(self, remote_path: str) -> DeleteResult:
        """Delete a file from local storage."""
        try:
            path = self._resolve_path(remote_path)

            if not path.exists():
                return DeleteResult(
                    success=False, path=remote_path, error="File not found"
                )

            if path.is_file():
                path.unlink()
            elif path.is_dir():
                shutil.rmtree(path)

            return DeleteResult(success=True, path=remote_path)

        except Exception as e:
            return DeleteResult(success=False, path=remote_path, error=str(e))

    def list(self, remote_path: str, recursive: bool = False) -> List[FileInfo]:
        """List files in a directory."""
        try:
            path = self._resolve_path(remote_path)

            if not path.exists():
                return []

            if not path.is_dir():
                # Return single file info
                return [self._file_info(path)]

            files = []

            if recursive:
                for item in path.rglob("*"):
                    files.append(self._file_info(item))
            else:
                for item in path.iterdir():
                    files.append(self._file_info(item))

            return files

        except Exception:
            return []

    def get_metadata(self, remote_path: str) -> Optional[FileInfo]:
        """Get metadata for a specific file."""
        try:
            path = self._resolve_path(remote_path)
            if not path.exists():
                return None
            return self._file_info(path)
        except Exception:
            return None

    def get_quota(self) -> QuotaInfo:
        """Get storage quota information for the file system."""
        try:
            stat = shutil.disk_usage(self.root_path)
            return QuotaInfo(
                total_bytes=stat.total,
                used_bytes=stat.used,
                available_bytes=stat.free,
            )
        except Exception:
            return QuotaInfo(total_bytes=0, used_bytes=0, available_bytes=0)

    def exists(self, remote_path: str) -> bool:
        """Check if a file or directory exists."""
        path = self._resolve_path(remote_path)
        return path.exists()

    def create_directory(self, remote_path: str) -> bool:
        """Create a directory."""
        try:
            path = self._resolve_path(remote_path)
            path.mkdir(parents=True, exist_ok=True)
            return True
        except Exception:
            return False

    def move(self, old_path: str, new_path: str) -> bool:
        """Move/rename a file."""
        try:
            old = self._resolve_path(old_path)
            new = self._resolve_path(new_path)

            if not old.exists():
                return False

            new.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(old), str(new))
            return True
        except Exception:
            return False

    def copy(self, source_path: str, dest_path: str) -> bool:
        """Copy a file."""
        try:
            source = self._resolve_path(source_path)
            dest = self._resolve_path(dest_path)

            if not source.exists():
                return False

            dest.parent.mkdir(parents=True, exist_ok=True)

            if source.is_file():
                shutil.copy2(source, dest)
            else:
                shutil.copytree(source, dest)

            return True
        except Exception:
            return False

    def _resolve_path(self, remote_path: str) -> Path:
        """Resolve a remote path to an absolute local path."""
        # Remove leading slash if present
        remote_path = remote_path.lstrip("/")
        return (self.root_path / remote_path).resolve()

    def _file_info(self, path: Path) -> FileInfo:
        """Create FileInfo from a Path object."""
        stat = path.stat()
        relative_path = path.relative_to(self.root_path)

        return FileInfo(
            path=str(relative_path),
            name=path.name,
            size=stat.st_size if path.is_file() else 0,
            modified_at=datetime.fromtimestamp(stat.st_mtime),
            is_directory=path.is_dir(),
        )
