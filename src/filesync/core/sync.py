"""Sync engine for cross-provider file synchronization."""

import tempfile
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from ..models.manifest_entry import ManifestEntry, FileLocation
from ..models.tier import Tier, get_tier_config
from ..providers.base import StorageProvider
from ..encryption.crypto import Encryptor, key_manager
from .manifest import ManifestManager
from .deduplication import DeduplicationEngine
from .redundancy import RedundancyManager


class SyncResult:
    """Result of a sync operation."""

    def __init__(self):
        self.success = False
        self.uploaded: List[str] = []
        self.downloaded: List[str] = []
        self.errors: List[Dict[str, str]] = []
        self.duplicates_found: int = 0
        self.bytes_uploaded: int = 0
        self.bytes_downloaded: int = 0

    def add_error(self, operation: str, file: str, error: str):
        """Add an error to the result."""
        self.errors.append({"operation": operation, "file": file, "error": error})

    def __repr__(self):
        return (
            f"SyncResult(uploaded={len(self.uploaded)}, "
            f"downloaded={len(self.downloaded)}, "
            f"errors={len(self.errors)}, "
            f"duplicates={self.duplicates_found})"
        )


class SyncEngine:
    """
    Sync engine that coordinates file operations across providers.

    Handles:
    - Uploading files to multiple providers based on tier
    - Downloading files from optimal provider
    - Deduplication
    - Encryption/decryption
    - Redundancy validation
    """

    def __init__(
        self,
        manifest: ManifestManager,
        providers: Dict[str, StorageProvider],
        temp_dir: Optional[Path] = None,
    ):
        """
        Initialize the sync engine.

        Args:
            manifest: Manifest manager
            providers: Dictionary of provider name -> provider instance
            temp_dir: Temporary directory for encrypted files
        """
        self.manifest = manifest
        self.providers = providers
        self.temp_dir = Path(temp_dir) if temp_dir else Path(tempfile.gettempdir())
        self.temp_dir.mkdir(parents=True, exist_ok=True)

        self.dedup = DeduplicationEngine()
        self.redundancy = RedundancyManager()

    def add_file(
        self,
        file_path: str | Path,
        tier: Tier,
        tags: Optional[List[str]] = None,
        importance_reason: Optional[str] = None,
        encrypt: bool = False,
    ) -> Tuple[bool, Optional[ManifestEntry], SyncResult]:
        """
        Add a file to the system.

        This will:
        1. Calculate content hash
        2. Check for duplicates
        3. Encrypt if required
        4. Upload to required providers based on tier
        5. Update manifest

        Args:
            file_path: Path to the file
            tier: Importance tier
            tags: Optional list of tags
            importance_reason: Reason for tier assignment
            encrypt: Whether to encrypt the file

        Returns:
            Tuple of (success, manifest_entry, sync_result)
        """
        result = SyncResult()
        file_path = Path(file_path)

        if not file_path.exists():
            result.add_error("add_file", str(file_path), "File not found")
            return False, None, result

        try:
            # Calculate hash and get file info
            content_hash = self.dedup.calculate_hash(file_path)
            size, mime_type = self.dedup.get_file_info(file_path)

            # Check for duplicates
            existing = self.manifest.get_entry(content_hash)
            if existing:
                result.duplicates_found = 1

                # Merge with existing entry
                existing = self.dedup.merge_entries(
                    existing, file_path.name, tier, tags or []
                )

                # Check if we need to add more copies for redundancy
                plan = self.redundancy.analyze_entry(existing)
                if not plan.is_compliant:
                    # Need to add more copies
                    self._ensure_redundancy(existing, file_path, encrypt, result)

                self.manifest.update_entry(existing)
                result.success = True
                return True, existing, result

            # Create new manifest entry
            entry = ManifestEntry(
                content_hash=content_hash,
                file_name=file_path.name,
                size=size,
                mime_type=mime_type,
                tier=tier,
                tags=tags or [],
                encrypted=encrypt,
                importance_reason=importance_reason,
                original_path=str(file_path.absolute()),
            )

            # Determine which providers to upload to
            config = get_tier_config(tier)

            # Force encryption if required by tier
            if config.require_encryption:
                encrypt = True
                entry.encrypted = True

            # Upload to required providers
            success = self._upload_to_providers(entry, file_path, encrypt, result)

            if success:
                # Add to manifest
                self.manifest.add_entry(entry)
                result.success = True
                return True, entry, result
            else:
                result.add_error("add_file", str(file_path), "Failed to upload")
                return False, None, result

        except Exception as e:
            result.add_error("add_file", str(file_path), str(e))
            return False, None, result

    def _upload_to_providers(
        self,
        entry: ManifestEntry,
        file_path: Path,
        encrypt: bool,
        result: SyncResult,
    ) -> bool:
        """Upload a file to the required providers based on tier."""
        config = get_tier_config(entry.tier)

        # Get available providers
        available = [name for name, prov in self.providers.items() if prov.is_authenticated()]

        # Get suggested providers
        suggested = self.redundancy.suggest_providers(
            entry, available, config.min_providers
        )

        # Ensure we have enough providers
        if len(suggested) < config.min_providers:
            result.add_error(
                "upload",
                entry.file_name,
                f"Not enough providers available (need {config.min_providers}, have {len(suggested)})",
            )
            return False

        # Prepare file for upload (encrypt if needed)
        if encrypt:
            upload_path = self._encrypt_file(file_path, entry, result)
            if not upload_path:
                return False
        else:
            upload_path = file_path

        # Upload to each provider
        uploaded = 0
        for provider_name in suggested:
            provider = self.providers[provider_name]

            # Generate remote path
            remote_path = self._generate_remote_path(entry, provider_name)

            # Upload
            upload_result = provider.upload(upload_path, remote_path)

            if upload_result.success:
                # Add location to entry
                location = FileLocation(
                    provider=provider_name,
                    path=remote_path,
                    uploaded_at=datetime.utcnow(),
                    verified=True,
                    last_verified=datetime.utcnow(),
                    size=upload_result.size,
                    checksum=upload_result.checksum,
                )
                entry.add_location(location)

                result.uploaded.append(f"{provider_name}:{remote_path}")
                result.bytes_uploaded += upload_result.size
                uploaded += 1

                # Stop if we have enough copies
                if uploaded >= config.min_copies:
                    break
            else:
                result.add_error("upload", entry.file_name, upload_result.error or "Unknown error")

        # Clean up encrypted temp file
        if encrypt and upload_path != file_path:
            upload_path.unlink(missing_ok=True)

        # Check if we uploaded enough copies
        if uploaded < config.min_copies:
            result.add_error(
                "upload",
                entry.file_name,
                f"Only uploaded {uploaded} of {config.min_copies} required copies",
            )
            return False

        return True

    def _ensure_redundancy(
        self,
        entry: ManifestEntry,
        file_path: Path,
        encrypt: bool,
        result: SyncResult,
    ) -> bool:
        """Ensure an entry meets its redundancy requirements."""
        plan = self.redundancy.analyze_entry(entry)

        if plan.is_compliant:
            return True

        # Get providers we need to add
        config = get_tier_config(entry.tier)
        available = [name for name, prov in self.providers.items() if prov.is_authenticated()]
        suggested = self.redundancy.suggest_providers(
            entry, available, plan.missing_providers + plan.missing_copies
        )

        # Upload to additional providers
        for provider_name in suggested:
            if len(entry.locations) >= config.min_copies:
                break

            provider = self.providers[provider_name]
            remote_path = self._generate_remote_path(entry, provider_name)

            # Prepare file (encrypt if needed and not already encrypted)
            if encrypt and not entry.encrypted:
                upload_path = self._encrypt_file(file_path, entry, result)
                if not upload_path:
                    continue
            else:
                upload_path = file_path

            # Upload
            upload_result = provider.upload(upload_path, remote_path)

            if upload_result.success:
                location = FileLocation(
                    provider=provider_name,
                    path=remote_path,
                    uploaded_at=datetime.utcnow(),
                    verified=True,
                    last_verified=datetime.utcnow(),
                    size=upload_result.size,
                    checksum=upload_result.checksum,
                )
                entry.add_location(location)
                result.uploaded.append(f"{provider_name}:{remote_path}")
                result.bytes_uploaded += upload_result.size

            # Clean up temp file
            if encrypt and upload_path != file_path:
                upload_path.unlink(missing_ok=True)

        return len(entry.locations) >= config.min_copies

    def get_file(
        self, content_hash: str, output_path: str | Path
    ) -> Tuple[bool, SyncResult]:
        """
        Download a file from the best available provider.

        Args:
            content_hash: Content hash of the file
            output_path: Where to save the file

        Returns:
            Tuple of (success, sync_result)
        """
        result = SyncResult()
        output_path = Path(output_path)

        # Get entry from manifest
        entry = self.manifest.get_entry(content_hash)
        if not entry:
            result.add_error("get_file", content_hash, "File not found in manifest")
            return False, result

        # Try each location until one succeeds
        for location in entry.locations:
            provider = self.providers.get(location.provider)
            if not provider or not provider.is_authenticated():
                continue

            # Download to temp file if encrypted
            if entry.encrypted:
                temp_path = self.temp_dir / f"{content_hash}.enc"
                download_result = provider.download(location.path, temp_path)

                if download_result.success:
                    # Decrypt to final destination
                    try:
                        encryptor = key_manager.create_encryptor()
                        encryptor.decrypt_file(temp_path, output_path)
                        temp_path.unlink(missing_ok=True)

                        result.downloaded.append(str(output_path))
                        result.bytes_downloaded += entry.size
                        result.success = True
                        return True, result
                    except Exception as e:
                        result.add_error("decrypt", entry.file_name, str(e))
                        temp_path.unlink(missing_ok=True)
            else:
                download_result = provider.download(location.path, output_path)

                if download_result.success:
                    result.downloaded.append(str(output_path))
                    result.bytes_downloaded += download_result.size
                    result.success = True
                    return True, result

        result.add_error("get_file", entry.file_name, "Failed to download from any provider")
        return False, result

    def _encrypt_file(
        self, file_path: Path, entry: ManifestEntry, result: SyncResult
    ) -> Optional[Path]:
        """Encrypt a file and return path to encrypted file."""
        try:
            if not key_manager.has_passphrase():
                result.add_error("encrypt", str(file_path), "No encryption passphrase set")
                return None

            encryptor = key_manager.create_encryptor()
            temp_path = self.temp_dir / f"{entry.content_hash}.enc"

            key_id, _ = encryptor.encrypt_file(file_path, temp_path)
            entry.encryption_key_id = key_id

            return temp_path

        except Exception as e:
            result.add_error("encrypt", str(file_path), str(e))
            return None

    def _generate_remote_path(self, entry: ManifestEntry, provider_name: str) -> str:
        """Generate a remote path for a file on a provider."""
        # Organize by tier
        tier_name = entry.tier.name.lower()

        # Add extension
        if entry.encrypted:
            filename = f"{entry.file_name}.enc"
        else:
            filename = entry.file_name

        # Include hash prefix for uniqueness
        hash_prefix = entry.content_hash.split(":")[-1][:8]

        return f"/{tier_name}/{hash_prefix}/{filename}"

    def verify_all_locations(self) -> Dict[str, any]:
        """
        Verify all file locations by checking hashes.

        Returns:
            Verification report
        """
        report = {
            "total_locations": 0,
            "verified": 0,
            "failed": 0,
            "errors": [],
        }

        for entry in self.manifest.get_all_entries():
            for location in entry.locations:
                report["total_locations"] += 1

                provider = self.providers.get(location.provider)
                if not provider or not provider.is_authenticated():
                    report["failed"] += 1
                    report["errors"].append(
                        f"{location.provider}:{location.path} - Provider not available"
                    )
                    continue

                # Download and verify hash
                temp_path = self.temp_dir / f"verify_{entry.content_hash}"

                try:
                    download_result = provider.download(location.path, temp_path)

                    if download_result.success:
                        # Calculate hash
                        actual_hash = self.dedup.calculate_hash(temp_path)

                        if entry.encrypted:
                            # For encrypted files, verify decryption works
                            try:
                                encryptor = key_manager.create_encryptor()
                                decrypted_path = temp_path.with_suffix(".dec")
                                encryptor.decrypt_file(temp_path, decrypted_path)
                                actual_hash = self.dedup.calculate_hash(decrypted_path)
                                decrypted_path.unlink(missing_ok=True)
                            except Exception as e:
                                report["failed"] += 1
                                report["errors"].append(
                                    f"{location.provider}:{location.path} - Decryption failed: {e}"
                                )
                                temp_path.unlink(missing_ok=True)
                                continue

                        if actual_hash == entry.content_hash:
                            location.verified = True
                            location.last_verified = datetime.utcnow()
                            report["verified"] += 1
                        else:
                            report["failed"] += 1
                            report["errors"].append(
                                f"{location.provider}:{location.path} - Hash mismatch"
                            )

                        temp_path.unlink(missing_ok=True)
                    else:
                        report["failed"] += 1
                        report["errors"].append(
                            f"{location.provider}:{location.path} - Download failed"
                        )

                except Exception as e:
                    report["failed"] += 1
                    report["errors"].append(
                        f"{location.provider}:{location.path} - {str(e)}"
                    )
                    temp_path.unlink(missing_ok=True)

            # Update entry in manifest
            self.manifest.update_entry(entry)

        return report
