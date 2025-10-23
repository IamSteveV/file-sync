"""Content-based deduplication engine."""

import hashlib
import mimetypes
from pathlib import Path
from typing import Optional, Tuple
from ..models.manifest_entry import ManifestEntry
from ..models.tier import Tier


class DeduplicationEngine:
    """
    Handles content-based deduplication using SHA-256 hashing.

    Files with identical content will have the same hash, enabling
    efficient duplicate detection across all storage providers.
    """

    CHUNK_SIZE = 65536  # 64KB chunks for hashing large files

    @staticmethod
    def calculate_hash(file_path: str | Path) -> str:
        """
        Calculate SHA-256 hash of a file.

        Args:
            file_path: Path to the file

        Returns:
            SHA-256 hash as hex string with 'sha256:' prefix
        """
        sha256 = hashlib.sha256()
        path = Path(file_path)

        with open(path, "rb") as f:
            while chunk := f.read(DeduplicationEngine.CHUNK_SIZE):
                sha256.update(chunk)

        return f"sha256:{sha256.hexdigest()}"

    @staticmethod
    def calculate_hash_from_bytes(data: bytes) -> str:
        """
        Calculate SHA-256 hash from bytes.

        Args:
            data: File content as bytes

        Returns:
            SHA-256 hash as hex string with 'sha256:' prefix
        """
        sha256 = hashlib.sha256(data)
        return f"sha256:{sha256.hexdigest()}"

    @staticmethod
    def get_file_info(file_path: str | Path) -> Tuple[int, str]:
        """
        Get file size and MIME type.

        Args:
            file_path: Path to the file

        Returns:
            Tuple of (size in bytes, MIME type)
        """
        path = Path(file_path)
        size = path.stat().st_size

        # Guess MIME type
        mime_type, _ = mimetypes.guess_type(str(path))
        if not mime_type:
            mime_type = "application/octet-stream"

        return size, mime_type

    @staticmethod
    def is_duplicate(content_hash: str, manifest_entries: list) -> bool:
        """
        Check if a file with this hash already exists in the manifest.

        Args:
            content_hash: The content hash to check
            manifest_entries: List of existing manifest entries

        Returns:
            True if duplicate found
        """
        return any(entry.content_hash == content_hash for entry in manifest_entries)

    @staticmethod
    def find_duplicate(content_hash: str, manifest_entries: list) -> Optional[ManifestEntry]:
        """
        Find a duplicate file in the manifest.

        Args:
            content_hash: The content hash to search for
            manifest_entries: List of existing manifest entries

        Returns:
            The duplicate entry if found, None otherwise
        """
        for entry in manifest_entries:
            if entry.content_hash == content_hash:
                return entry
        return None

    @staticmethod
    def should_keep_duplicate(
        existing: ManifestEntry, new_tier: Tier, new_tags: list
    ) -> bool:
        """
        Determine if a duplicate should be kept as a separate entry.

        In most cases, duplicates should be merged into a single entry
        with multiple locations. However, in some cases (different tiers,
        different tags), we might want to track them separately.

        Args:
            existing: Existing manifest entry
            new_tier: Tier of the new file
            new_tags: Tags of the new file

        Returns:
            True if duplicate should be kept as separate entry
        """
        # For now, always merge duplicates
        # Future: Allow keeping separate entries for different use cases
        return False

    @staticmethod
    def merge_entries(
        existing: ManifestEntry, new_filename: str, new_tier: Tier, new_tags: list
    ) -> ManifestEntry:
        """
        Merge a duplicate into an existing entry.

        Updates the entry with:
        - Higher tier (if new tier is higher)
        - Combined tags
        - Updated filename if more descriptive

        Args:
            existing: Existing manifest entry
            new_filename: Filename of the new duplicate
            new_tier: Tier of the new duplicate
            new_tags: Tags of the new duplicate

        Returns:
            Updated manifest entry
        """
        # Upgrade to higher tier if needed
        if new_tier < existing.tier:  # Lower number = higher importance
            existing.tier = new_tier

        # Merge tags
        for tag in new_tags:
            existing.add_tag(tag)

        # Update filename if new one is more descriptive (longer)
        if len(new_filename) > len(existing.file_name):
            existing.file_name = new_filename

        return existing

    @staticmethod
    def detect_near_duplicates(file_path: str | Path, threshold: float = 0.95) -> list:
        """
        Detect near-duplicate files using perceptual hashing (for images).

        This is a placeholder for future implementation using libraries like
        imagehash for detecting similar images (different crops, edits, etc.)

        Args:
            file_path: Path to the file
            threshold: Similarity threshold (0.0 to 1.0)

        Returns:
            List of similar file hashes
        """
        # TODO: Implement perceptual hashing for images
        # - Use pHash, dHash, or aHash for image similarity
        # - Compare against existing images in manifest
        # - Return list of similar files above threshold
        return []

    @staticmethod
    def quick_hash(file_path: str | Path, sample_size: int = 1024 * 1024) -> str:
        """
        Calculate a quick hash by sampling parts of the file.

        Useful for quickly identifying potential duplicates before
        calculating full hash. Samples first, middle, and last portions.

        Args:
            file_path: Path to the file
            sample_size: Size of each sample in bytes

        Returns:
            Quick hash as hex string
        """
        path = Path(file_path)
        size = path.stat().st_size

        sha256 = hashlib.sha256()

        with open(path, "rb") as f:
            # First chunk
            sha256.update(f.read(min(sample_size, size)))

            # Middle chunk
            if size > sample_size * 2:
                f.seek(size // 2)
                sha256.update(f.read(sample_size))

            # Last chunk
            if size > sample_size:
                f.seek(max(0, size - sample_size))
                sha256.update(f.read(sample_size))

        return f"quick:{sha256.hexdigest()}"

    @staticmethod
    def verify_hash(file_path: str | Path, expected_hash: str) -> bool:
        """
        Verify that a file matches the expected hash.

        Args:
            file_path: Path to the file
            expected_hash: Expected SHA-256 hash

        Returns:
            True if hash matches
        """
        actual_hash = DeduplicationEngine.calculate_hash(file_path)
        return actual_hash == expected_hash

    @staticmethod
    def analyze_file(file_path: str | Path) -> dict:
        """
        Analyze a file and return comprehensive information.

        Args:
            file_path: Path to the file

        Returns:
            Dictionary with file analysis results
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        if not path.is_file():
            raise ValueError(f"Not a file: {path}")

        # Calculate hashes
        content_hash = DeduplicationEngine.calculate_hash(path)
        quick_hash = DeduplicationEngine.quick_hash(path)

        # Get file info
        size, mime_type = DeduplicationEngine.get_file_info(path)

        # Get file stats
        stat = path.stat()

        return {
            "path": str(path.absolute()),
            "filename": path.name,
            "size": size,
            "mime_type": mime_type,
            "content_hash": content_hash,
            "quick_hash": quick_hash,
            "created_at": stat.st_ctime,
            "modified_at": stat.st_mtime,
            "is_image": mime_type.startswith("image/"),
            "is_video": mime_type.startswith("video/"),
            "is_document": mime_type.startswith("application/"),
        }
