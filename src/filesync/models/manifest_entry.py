"""Manifest entry model representing a tracked file."""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Optional, Dict, Any
from .tier import Tier


@dataclass
class FileLocation:
    """Represents a file's location on a storage provider."""

    provider: str  # gdrive, onedrive, box, proton, local
    path: str  # Full path on the provider
    uploaded_at: datetime
    verified: bool = False
    last_verified: Optional[datetime] = None
    size: Optional[int] = None  # Actual size on provider (may differ if compressed)
    checksum: Optional[str] = None  # Provider's checksum if available

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "provider": self.provider,
            "path": self.path,
            "uploaded_at": self.uploaded_at.isoformat(),
            "verified": self.verified,
            "last_verified": (
                self.last_verified.isoformat() if self.last_verified else None
            ),
            "size": self.size,
            "checksum": self.checksum,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FileLocation":
        """Create from dictionary."""
        return cls(
            provider=data["provider"],
            path=data["path"],
            uploaded_at=datetime.fromisoformat(data["uploaded_at"]),
            verified=data.get("verified", False),
            last_verified=(
                datetime.fromisoformat(data["last_verified"])
                if data.get("last_verified")
                else None
            ),
            size=data.get("size"),
            checksum=data.get("checksum"),
        )


@dataclass
class ManifestEntry:
    """
    Represents a file tracked in the manifest.

    This is the single source of truth for all file metadata,
    locations, and deduplication information.
    """

    content_hash: str  # SHA-256 hash of the file content
    file_name: str  # Original filename
    size: int  # File size in bytes
    mime_type: str  # MIME type
    tier: Tier  # Importance tier
    tags: List[str] = field(default_factory=list)  # User-defined tags
    encrypted: bool = False  # Whether the file is encrypted
    encryption_key_id: Optional[str] = None  # Reference to encryption key
    locations: List[FileLocation] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    modified_at: datetime = field(default_factory=datetime.utcnow)
    importance_reason: Optional[str] = None  # Why this tier was assigned
    original_path: Optional[str] = None  # Original path when first tracked
    metadata: Dict[str, Any] = field(default_factory=dict)  # Additional metadata

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "content_hash": self.content_hash,
            "file_name": self.file_name,
            "size": self.size,
            "mime_type": self.mime_type,
            "tier": int(self.tier),
            "tags": self.tags,
            "encrypted": self.encrypted,
            "encryption_key_id": self.encryption_key_id,
            "locations": [loc.to_dict() for loc in self.locations],
            "created_at": self.created_at.isoformat(),
            "modified_at": self.modified_at.isoformat(),
            "importance_reason": self.importance_reason,
            "original_path": self.original_path,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ManifestEntry":
        """Create from dictionary."""
        return cls(
            content_hash=data["content_hash"],
            file_name=data["file_name"],
            size=data["size"],
            mime_type=data["mime_type"],
            tier=Tier(data["tier"]),
            tags=data.get("tags", []),
            encrypted=data.get("encrypted", False),
            encryption_key_id=data.get("encryption_key_id"),
            locations=[
                FileLocation.from_dict(loc) for loc in data.get("locations", [])
            ],
            created_at=datetime.fromisoformat(data["created_at"]),
            modified_at=datetime.fromisoformat(data["modified_at"]),
            importance_reason=data.get("importance_reason"),
            original_path=data.get("original_path"),
            metadata=data.get("metadata", {}),
        )

    def add_location(self, location: FileLocation) -> None:
        """Add a new location for this file."""
        # Check if location already exists
        for existing in self.locations:
            if existing.provider == location.provider and existing.path == location.path:
                # Update existing location
                existing.uploaded_at = location.uploaded_at
                existing.verified = location.verified
                existing.last_verified = location.last_verified
                existing.size = location.size
                existing.checksum = location.checksum
                return

        self.locations.append(location)
        self.modified_at = datetime.utcnow()

    def remove_location(self, provider: str, path: str) -> bool:
        """Remove a location. Returns True if found and removed."""
        original_len = len(self.locations)
        self.locations = [
            loc for loc in self.locations
            if not (loc.provider == provider and loc.path == path)
        ]
        if len(self.locations) < original_len:
            self.modified_at = datetime.utcnow()
            return True
        return False

    def get_providers(self) -> List[str]:
        """Get list of unique providers where this file is stored."""
        return list(set(loc.provider for loc in self.locations))

    def has_provider(self, provider: str) -> bool:
        """Check if file exists on a specific provider."""
        return any(loc.provider == provider for loc in self.locations)

    def get_location_on_provider(self, provider: str) -> Optional[FileLocation]:
        """Get the first location on a specific provider."""
        for loc in self.locations:
            if loc.provider == provider:
                return loc
        return None

    def is_verified(self) -> bool:
        """Check if all locations are verified."""
        return all(loc.verified for loc in self.locations)

    def needs_verification(self, days: int) -> bool:
        """
        Check if any location needs verification based on age.

        Args:
            days: Number of days since last verification

        Returns:
            True if any location needs verification
        """
        if days <= 0:
            return False

        now = datetime.utcnow()
        for loc in self.locations:
            if not loc.verified or loc.last_verified is None:
                return True

            days_since_verified = (now - loc.last_verified).days
            if days_since_verified >= days:
                return True

        return False

    def add_tag(self, tag: str) -> None:
        """Add a tag if it doesn't already exist."""
        tag = tag.lower().strip()
        if tag and tag not in self.tags:
            self.tags.append(tag)
            self.modified_at = datetime.utcnow()

    def remove_tag(self, tag: str) -> bool:
        """Remove a tag. Returns True if found and removed."""
        tag = tag.lower().strip()
        if tag in self.tags:
            self.tags.remove(tag)
            self.modified_at = datetime.utcnow()
            return True
        return False

    def has_tag(self, tag: str) -> bool:
        """Check if entry has a specific tag."""
        return tag.lower().strip() in self.tags

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"ManifestEntry(hash={self.content_hash[:16]}..., "
            f"name={self.file_name}, tier={self.tier.name}, "
            f"locations={len(self.locations)})"
        )
