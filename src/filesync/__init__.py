"""
Cloud Storage Deduplication System

A cross-platform, provider-agnostic file synchronization and deduplication
system with importance-based tiering and client-side encryption.
"""

__version__ = "0.1.0"
__author__ = "FileSync Team"

from .core.manifest import ManifestManager
from .core.deduplication import DeduplicationEngine
from .core.sync import SyncEngine
from .models.tier import Tier, TierConfig
from .models.manifest_entry import ManifestEntry

__all__ = [
    "ManifestManager",
    "DeduplicationEngine",
    "SyncEngine",
    "Tier",
    "TierConfig",
    "ManifestEntry",
]
