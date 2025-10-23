"""Manifest manager for tracking all files in the system."""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from ..models.manifest_entry import ManifestEntry, FileLocation
from ..models.tier import Tier, validate_tier_requirements


class ManifestManager:
    """
    Manages the manifest database - the single source of truth for all files.

    The manifest tracks:
    - Content hashes for deduplication
    - File metadata and tags
    - Storage locations across providers
    - Importance tiers
    - Encryption status
    """

    def __init__(self, db_path: str | Path):
        """
        Initialize the manifest manager.

        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn: Optional[sqlite3.Connection] = None
        self._initialize_db()

    def _initialize_db(self) -> None:
        """Create the database schema if it doesn't exist."""
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row

        # Create manifest entries table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS manifest_entries (
                content_hash TEXT PRIMARY KEY,
                file_name TEXT NOT NULL,
                size INTEGER NOT NULL,
                mime_type TEXT NOT NULL,
                tier INTEGER NOT NULL,
                tags TEXT,  -- JSON array
                encrypted INTEGER NOT NULL DEFAULT 0,
                encryption_key_id TEXT,
                created_at TEXT NOT NULL,
                modified_at TEXT NOT NULL,
                importance_reason TEXT,
                original_path TEXT,
                metadata TEXT  -- JSON object
            )
        """)

        # Create locations table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS file_locations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content_hash TEXT NOT NULL,
                provider TEXT NOT NULL,
                path TEXT NOT NULL,
                uploaded_at TEXT NOT NULL,
                verified INTEGER NOT NULL DEFAULT 0,
                last_verified TEXT,
                size INTEGER,
                checksum TEXT,
                FOREIGN KEY (content_hash) REFERENCES manifest_entries(content_hash)
                    ON DELETE CASCADE,
                UNIQUE(content_hash, provider, path)
            )
        """)

        # Create indexes for faster lookups
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_file_name ON manifest_entries(file_name)"
        )
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_tier ON manifest_entries(tier)"
        )
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_provider ON file_locations(provider)"
        )
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_verified ON file_locations(verified)"
        )

        self.conn.commit()

    def close(self) -> None:
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def add_entry(self, entry: ManifestEntry) -> bool:
        """
        Add a new manifest entry.

        Args:
            entry: The manifest entry to add

        Returns:
            True if added successfully, False if already exists
        """
        if self.get_entry(entry.content_hash):
            return False

        self.conn.execute(
            """
            INSERT INTO manifest_entries (
                content_hash, file_name, size, mime_type, tier, tags,
                encrypted, encryption_key_id, created_at, modified_at,
                importance_reason, original_path, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                entry.content_hash,
                entry.file_name,
                entry.size,
                entry.mime_type,
                int(entry.tier),
                json.dumps(entry.tags),
                int(entry.encrypted),
                entry.encryption_key_id,
                entry.created_at.isoformat(),
                entry.modified_at.isoformat(),
                entry.importance_reason,
                entry.original_path,
                json.dumps(entry.metadata),
            ),
        )

        # Add locations
        for loc in entry.locations:
            self._add_location(entry.content_hash, loc)

        self.conn.commit()
        return True

    def update_entry(self, entry: ManifestEntry) -> bool:
        """
        Update an existing manifest entry.

        Args:
            entry: The manifest entry with updated data

        Returns:
            True if updated successfully, False if not found
        """
        cursor = self.conn.execute(
            """
            UPDATE manifest_entries
            SET file_name = ?, size = ?, mime_type = ?, tier = ?, tags = ?,
                encrypted = ?, encryption_key_id = ?, modified_at = ?,
                importance_reason = ?, original_path = ?, metadata = ?
            WHERE content_hash = ?
            """,
            (
                entry.file_name,
                entry.size,
                entry.mime_type,
                int(entry.tier),
                json.dumps(entry.tags),
                int(entry.encrypted),
                entry.encryption_key_id,
                datetime.utcnow().isoformat(),
                entry.importance_reason,
                entry.original_path,
                json.dumps(entry.metadata),
                entry.content_hash,
            ),
        )

        if cursor.rowcount == 0:
            return False

        # Update locations - remove all and re-add
        self.conn.execute(
            "DELETE FROM file_locations WHERE content_hash = ?", (entry.content_hash,)
        )
        for loc in entry.locations:
            self._add_location(entry.content_hash, loc)

        self.conn.commit()
        return True

    def get_entry(self, content_hash: str) -> Optional[ManifestEntry]:
        """
        Get a manifest entry by content hash.

        Args:
            content_hash: The SHA-256 hash of the file

        Returns:
            The manifest entry or None if not found
        """
        row = self.conn.execute(
            "SELECT * FROM manifest_entries WHERE content_hash = ?", (content_hash,)
        ).fetchone()

        if not row:
            return None

        # Get locations
        location_rows = self.conn.execute(
            "SELECT * FROM file_locations WHERE content_hash = ?", (content_hash,)
        ).fetchall()

        locations = [self._location_from_row(row) for row in location_rows]

        return ManifestEntry(
            content_hash=row["content_hash"],
            file_name=row["file_name"],
            size=row["size"],
            mime_type=row["mime_type"],
            tier=Tier(row["tier"]),
            tags=json.loads(row["tags"]),
            encrypted=bool(row["encrypted"]),
            encryption_key_id=row["encryption_key_id"],
            locations=locations,
            created_at=datetime.fromisoformat(row["created_at"]),
            modified_at=datetime.fromisoformat(row["modified_at"]),
            importance_reason=row["importance_reason"],
            original_path=row["original_path"],
            metadata=json.loads(row["metadata"]) if row["metadata"] else {},
        )

    def get_entries_by_filename(self, filename: str) -> List[ManifestEntry]:
        """Get all entries with a specific filename (may have multiple due to duplicates)."""
        rows = self.conn.execute(
            "SELECT content_hash FROM manifest_entries WHERE file_name = ?",
            (filename,),
        ).fetchall()

        return [self.get_entry(row["content_hash"]) for row in rows]

    def get_entries_by_tier(self, tier: Tier) -> List[ManifestEntry]:
        """Get all entries with a specific tier."""
        rows = self.conn.execute(
            "SELECT content_hash FROM manifest_entries WHERE tier = ?", (int(tier),)
        ).fetchall()

        return [self.get_entry(row["content_hash"]) for row in rows]

    def get_entries_by_tag(self, tag: str) -> List[ManifestEntry]:
        """Get all entries with a specific tag."""
        # SQLite JSON functions for better querying
        # For now, we'll do a simple LIKE search
        tag_pattern = f'%"{tag}"%'
        rows = self.conn.execute(
            "SELECT content_hash FROM manifest_entries WHERE tags LIKE ?",
            (tag_pattern,),
        ).fetchall()

        return [self.get_entry(row["content_hash"]) for row in rows]

    def get_all_entries(self) -> List[ManifestEntry]:
        """Get all manifest entries."""
        rows = self.conn.execute("SELECT content_hash FROM manifest_entries").fetchall()
        return [self.get_entry(row["content_hash"]) for row in rows]

    def delete_entry(self, content_hash: str) -> bool:
        """
        Delete a manifest entry and all its locations.

        Args:
            content_hash: The content hash of the entry to delete

        Returns:
            True if deleted, False if not found
        """
        cursor = self.conn.execute(
            "DELETE FROM manifest_entries WHERE content_hash = ?", (content_hash,)
        )
        self.conn.commit()
        return cursor.rowcount > 0

    def get_entries_needing_verification(self, days: int) -> List[ManifestEntry]:
        """Get entries that need verification based on their tier configuration."""
        entries = []
        for tier in Tier:
            tier_entries = self.get_entries_by_tier(tier)
            for entry in tier_entries:
                if entry.needs_verification(days):
                    entries.append(entry)
        return entries

    def validate_all_entries(self) -> Dict[str, List[str]]:
        """
        Validate all entries against their tier requirements.

        Returns:
            Dictionary mapping content_hash to list of validation errors
        """
        results = {}
        for entry in self.get_all_entries():
            errors = validate_tier_requirements(
                entry.tier,
                [loc.to_dict() for loc in entry.locations],
                entry.encrypted,
            )
            if errors:
                results[entry.content_hash] = errors
        return results

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the manifest."""
        stats = {}

        # Total entries
        stats["total_files"] = self.conn.execute(
            "SELECT COUNT(*) as count FROM manifest_entries"
        ).fetchone()["count"]

        # Total size
        stats["total_size"] = self.conn.execute(
            "SELECT SUM(size) as total FROM manifest_entries"
        ).fetchone()["total"] or 0

        # By tier
        stats["by_tier"] = {}
        for tier in Tier:
            count = self.conn.execute(
                "SELECT COUNT(*) as count FROM manifest_entries WHERE tier = ?",
                (int(tier),),
            ).fetchone()["count"]
            stats["by_tier"][tier.name] = count

        # By provider
        stats["by_provider"] = {}
        provider_rows = self.conn.execute(
            "SELECT provider, COUNT(*) as count FROM file_locations GROUP BY provider"
        ).fetchall()
        for row in provider_rows:
            stats["by_provider"][row["provider"]] = row["count"]

        # Encrypted files
        stats["encrypted_files"] = self.conn.execute(
            "SELECT COUNT(*) as count FROM manifest_entries WHERE encrypted = 1"
        ).fetchone()["count"]

        return stats

    def _add_location(self, content_hash: str, location: FileLocation) -> None:
        """Add a location to the database."""
        self.conn.execute(
            """
            INSERT OR REPLACE INTO file_locations (
                content_hash, provider, path, uploaded_at, verified,
                last_verified, size, checksum
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                content_hash,
                location.provider,
                location.path,
                location.uploaded_at.isoformat(),
                int(location.verified),
                (
                    location.last_verified.isoformat()
                    if location.last_verified
                    else None
                ),
                location.size,
                location.checksum,
            ),
        )

    def _location_from_row(self, row: sqlite3.Row) -> FileLocation:
        """Create a FileLocation from a database row."""
        return FileLocation(
            provider=row["provider"],
            path=row["path"],
            uploaded_at=datetime.fromisoformat(row["uploaded_at"]),
            verified=bool(row["verified"]),
            last_verified=(
                datetime.fromisoformat(row["last_verified"])
                if row["last_verified"]
                else None
            ),
            size=row["size"],
            checksum=row["checksum"],
        )

    def export_to_json(self, output_path: str | Path) -> None:
        """Export the entire manifest to a JSON file."""
        entries = self.get_all_entries()
        data = {
            "version": "1.0",
            "exported_at": datetime.utcnow().isoformat(),
            "entries": [entry.to_dict() for entry in entries],
        }

        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)

    def import_from_json(self, input_path: str | Path) -> int:
        """
        Import manifest entries from a JSON file.

        Returns:
            Number of entries imported
        """
        with open(input_path, "r") as f:
            data = json.load(f)

        count = 0
        for entry_data in data.get("entries", []):
            entry = ManifestEntry.from_dict(entry_data)
            if self.add_entry(entry):
                count += 1

        return count
