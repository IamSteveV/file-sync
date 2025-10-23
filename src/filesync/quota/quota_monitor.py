"""Cloud storage quota monitoring."""

import json
import time
from pathlib import Path
from typing import Dict, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class QuotaInfo:
    """Storage quota information for a provider."""
    provider: str
    total_bytes: int
    used_bytes: int
    available_bytes: int
    last_updated: float

    @property
    def used_percentage(self) -> float:
        """Calculate used percentage."""
        if self.total_bytes == 0:
            return 0.0
        return (self.used_bytes / self.total_bytes) * 100

    @property
    def is_warning(self) -> bool:
        """Check if usage is in warning range (>80%)."""
        return self.used_percentage >= 80

    @property
    def is_critical(self) -> bool:
        """Check if usage is critical (>95%)."""
        return self.used_percentage >= 95

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict) -> 'QuotaInfo':
        """Create from dictionary."""
        return QuotaInfo(**data)


class QuotaMonitor:
    """Monitors storage quotas across providers."""

    def __init__(self, config_path: Path, providers: Dict):
        """
        Initialize quota monitor.

        Args:
            config_path: Path to quota cache file
            providers: Dictionary of provider instances
        """
        self.config_path = config_path
        self.providers = providers
        self.quotas: Dict[str, QuotaInfo] = {}

        self._load_cache()

    def _load_cache(self):
        """Load cached quota information."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    data = json.load(f)

                self.quotas = {
                    provider: QuotaInfo.from_dict(quota_data)
                    for provider, quota_data in data.get('quotas', {}).items()
                }
            except Exception as e:
                print(f"Error loading quota cache: {e}")
                self.quotas = {}

    def _save_cache(self):
        """Save quota information to cache."""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)

            data = {
                'quotas': {
                    provider: quota.to_dict()
                    for provider, quota in self.quotas.items()
                },
                'last_updated': time.time()
            }

            with open(self.config_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving quota cache: {e}")

    def update_quota(self, provider_name: str) -> Optional[QuotaInfo]:
        """
        Update quota information for a provider.

        Args:
            provider_name: Name of the provider

        Returns:
            Updated quota info or None if failed
        """
        provider = self.providers.get(provider_name)

        if not provider:
            return None

        try:
            # Get quota from provider
            # This is a placeholder - actual implementation depends on provider API
            quota_data = self._fetch_quota_from_provider(provider, provider_name)

            if quota_data:
                quota_info = QuotaInfo(
                    provider=provider_name,
                    total_bytes=quota_data['total'],
                    used_bytes=quota_data['used'],
                    available_bytes=quota_data['available'],
                    last_updated=time.time()
                )

                self.quotas[provider_name] = quota_info
                self._save_cache()

                return quota_info

        except Exception as e:
            print(f"Error updating quota for {provider_name}: {e}")

        return None

    def _fetch_quota_from_provider(self, provider, provider_name: str) -> Optional[Dict]:
        """
        Fetch quota from provider API.

        This is a placeholder implementation. Real implementation would
        call the actual provider API methods.
        """
        # For local provider, calculate actual usage
        if provider_name == 'local':
            try:
                import shutil
                stats = shutil.disk_usage(provider.base_path)
                return {
                    'total': stats.total,
                    'used': stats.used,
                    'available': stats.free
                }
            except:
                pass

        # For cloud providers, this would make API calls
        # For now, return None (not implemented)
        return None

    def update_all_quotas(self) -> Dict[str, QuotaInfo]:
        """
        Update quotas for all configured providers.

        Returns:
            Dictionary of updated quotas
        """
        for provider_name in self.providers.keys():
            self.update_quota(provider_name)

        return self.quotas

    def get_quota(self, provider_name: str) -> Optional[QuotaInfo]:
        """Get cached quota for a provider."""
        return self.quotas.get(provider_name)

    def get_all_quotas(self) -> Dict[str, QuotaInfo]:
        """Get all cached quotas."""
        return self.quotas

    def get_warnings(self) -> List[QuotaInfo]:
        """Get quotas in warning state (>80% used)."""
        return [
            quota for quota in self.quotas.values()
            if quota.is_warning and not quota.is_critical
        ]

    def get_critical(self) -> List[QuotaInfo]:
        """Get quotas in critical state (>95% used)."""
        return [
            quota for quota in self.quotas.values()
            if quota.is_critical
        ]

    def is_quota_stale(self, provider_name: str, max_age_hours: int = 1) -> bool:
        """
        Check if quota data is stale.

        Args:
            provider_name: Provider name
            max_age_hours: Maximum age in hours before considering stale

        Returns:
            True if quota data is stale or missing
        """
        quota = self.quotas.get(provider_name)

        if not quota:
            return True

        age_seconds = time.time() - quota.last_updated
        age_hours = age_seconds / 3600

        return age_hours > max_age_hours

    def format_bytes(self, bytes_value: int) -> str:
        """Format bytes as human-readable string."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.1f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.1f} PB"

    def get_summary(self) -> Dict:
        """Get summary of all quotas."""
        total_capacity = sum(q.total_bytes for q in self.quotas.values())
        total_used = sum(q.used_bytes for q in self.quotas.values())
        total_available = sum(q.available_bytes for q in self.quotas.values())

        return {
            'total_providers': len(self.quotas),
            'total_capacity': total_capacity,
            'total_used': total_used,
            'total_available': total_available,
            'total_used_percentage': (total_used / total_capacity * 100) if total_capacity > 0 else 0,
            'warnings': len(self.get_warnings()),
            'critical': len(self.get_critical())
        }


def calculate_storage_needs(manifest, tier_config) -> Dict[str, int]:
    """
    Calculate storage needs based on manifest and tier configuration.

    Args:
        manifest: ManifestManager instance
        tier_config: Tier configuration

    Returns:
        Dictionary mapping provider to required bytes
    """
    # This would analyze the manifest and calculate how much storage
    # each provider needs based on tier requirements
    # Placeholder implementation
    return {}
