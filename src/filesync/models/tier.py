"""Importance tier models and configuration."""

from dataclasses import dataclass
from enum import IntEnum
from typing import List, Optional


class Tier(IntEnum):
    """File importance tiers."""

    CRITICAL = 0  # Irreplaceable + sensitive or business-critical
    IMPORTANT = 1  # Valuable but eventually replaceable
    STANDARD = 2  # Reference materials, non-sensitive media
    ARCHIVE = 3  # Cold storage, duplicates, low-value


@dataclass
class TierConfig:
    """Configuration for a specific tier."""

    tier: Tier
    name: str
    description: str
    min_copies: int
    min_providers: int
    require_offline: bool = False
    require_encryption: bool = False
    require_proton: bool = False
    allowed_providers: Optional[List[str]] = None
    verification_days: int = 0

    def __post_init__(self):
        """Validate configuration."""
        if self.min_copies < 1:
            raise ValueError("min_copies must be at least 1")
        if self.min_providers < 1:
            raise ValueError("min_providers must be at least 1")
        if self.min_providers > self.min_copies:
            raise ValueError("min_providers cannot exceed min_copies")
        if self.verification_days < 0:
            raise ValueError("verification_days cannot be negative")


# Default tier configurations
DEFAULT_TIER_CONFIGS = {
    Tier.CRITICAL: TierConfig(
        tier=Tier.CRITICAL,
        name="Critical",
        description="Irreplaceable + sensitive or business-critical",
        min_copies=3,
        min_providers=2,
        require_offline=True,
        require_encryption=True,
        require_proton=True,
        allowed_providers=["proton", "gdrive", "box", "onedrive", "local"],
        verification_days=7,
    ),
    Tier.IMPORTANT: TierConfig(
        tier=Tier.IMPORTANT,
        name="Important",
        description="Valuable but eventually replaceable",
        min_copies=2,
        min_providers=2,
        require_encryption=False,
        allowed_providers=["gdrive", "box", "onedrive", "proton", "local"],
        verification_days=14,
    ),
    Tier.STANDARD: TierConfig(
        tier=Tier.STANDARD,
        name="Standard",
        description="Reference PDFs, downloads, non-sensitive media",
        min_copies=1,
        min_providers=1,
        require_encryption=False,
        allowed_providers=["gdrive", "box", "onedrive", "proton", "local"],
        verification_days=30,
    ),
    Tier.ARCHIVE: TierConfig(
        tier=Tier.ARCHIVE,
        name="Archive",
        description="Cold storage, duplicates, low-value",
        min_copies=1,
        min_providers=1,
        require_encryption=False,
        allowed_providers=["gdrive", "box", "onedrive", "local"],
        verification_days=0,
    ),
}


def get_tier_config(tier: Tier) -> TierConfig:
    """Get the configuration for a specific tier."""
    return DEFAULT_TIER_CONFIGS[tier]


def validate_tier_requirements(tier: Tier, locations: List[dict], encrypted: bool) -> List[str]:
    """
    Validate that a file meets the requirements for its tier.

    Args:
        tier: The file's importance tier
        locations: List of location dictionaries
        encrypted: Whether the file is encrypted

    Returns:
        List of validation errors (empty if valid)
    """
    config = get_tier_config(tier)
    errors = []

    # Check number of copies
    if len(locations) < config.min_copies:
        errors.append(
            f"Tier {config.name} requires {config.min_copies} copies, "
            f"but only {len(locations)} exist"
        )

    # Check number of providers
    providers = set(loc.get("provider") for loc in locations)
    if len(providers) < config.min_providers:
        errors.append(
            f"Tier {config.name} requires {config.min_providers} providers, "
            f"but only {len(providers)} are used"
        )

    # Check encryption requirement
    if config.require_encryption and not encrypted:
        errors.append(f"Tier {config.name} requires encryption")

    # Check Proton requirement
    if config.require_proton:
        has_proton = any(loc.get("provider") == "proton" for loc in locations)
        if not has_proton:
            errors.append(f"Tier {config.name} requires a copy on Proton Drive")

    # Check offline requirement
    if config.require_offline:
        has_local = any(loc.get("provider") == "local" for loc in locations)
        if not has_local:
            errors.append(f"Tier {config.name} requires an offline copy")

    # Check allowed providers
    if config.allowed_providers:
        for provider in providers:
            if provider not in config.allowed_providers:
                errors.append(
                    f"Provider '{provider}' is not allowed for tier {config.name}"
                )

    return errors
