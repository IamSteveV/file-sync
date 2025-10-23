"""Redundancy and tier management."""

from dataclasses import dataclass
from typing import List, Dict, Set, Optional
from ..models.tier import Tier, TierConfig, get_tier_config, validate_tier_requirements
from ..models.manifest_entry import ManifestEntry, FileLocation


@dataclass
class RedundancyPlan:
    """Plan for achieving required redundancy for a file."""

    entry: ManifestEntry
    current_providers: Set[str]
    required_providers: int
    current_copies: int
    required_copies: int
    needs_encryption: bool
    needs_proton: bool
    needs_offline: bool
    actions: List[str]  # List of actions to take

    @property
    def is_compliant(self) -> bool:
        """Check if current state meets requirements."""
        return len(self.actions) == 0

    @property
    def missing_copies(self) -> int:
        """Number of additional copies needed."""
        return max(0, self.required_copies - self.current_copies)

    @property
    def missing_providers(self) -> int:
        """Number of additional providers needed."""
        return max(0, self.required_providers - len(self.current_providers))


class RedundancyManager:
    """
    Manages redundancy requirements based on importance tiers.

    Ensures files meet the 3-2-1 backup strategy:
    - 3 copies of data
    - 2 different storage media/providers
    - 1 offsite/offline backup
    """

    def __init__(self):
        """Initialize the redundancy manager."""
        pass

    def analyze_entry(self, entry: ManifestEntry) -> RedundancyPlan:
        """
        Analyze a manifest entry and create a redundancy plan.

        Args:
            entry: Manifest entry to analyze

        Returns:
            RedundancyPlan with required actions
        """
        config = get_tier_config(entry.tier)

        current_providers = set(entry.get_providers())
        current_copies = len(entry.locations)

        actions = []

        # Check encryption
        needs_encryption = config.require_encryption and not entry.encrypted
        if needs_encryption:
            actions.append("encrypt_file")

        # Check Proton requirement
        needs_proton = config.require_proton and not entry.has_provider("proton")
        if needs_proton:
            actions.append("add_proton_copy")

        # Check offline requirement
        needs_offline = config.require_offline and not entry.has_provider("local")
        if needs_offline:
            actions.append("add_offline_copy")

        # Check provider count
        if len(current_providers) < config.min_providers:
            missing = config.min_providers - len(current_providers)
            for i in range(missing):
                actions.append(f"add_provider_{i+1}")

        # Check copy count (considering the providers we'll add)
        future_copies = current_copies + len(
            [a for a in actions if a.startswith("add_")]
        )
        if future_copies < config.min_copies:
            missing = config.min_copies - future_copies
            for i in range(missing):
                actions.append(f"add_copy_{i+1}")

        return RedundancyPlan(
            entry=entry,
            current_providers=current_providers,
            required_providers=config.min_providers,
            current_copies=current_copies,
            required_copies=config.min_copies,
            needs_encryption=needs_encryption,
            needs_proton=needs_proton,
            needs_offline=needs_offline,
            actions=actions,
        )

    def get_non_compliant_entries(
        self, entries: List[ManifestEntry]
    ) -> List[RedundancyPlan]:
        """
        Find all entries that don't meet their tier requirements.

        Args:
            entries: List of manifest entries to check

        Returns:
            List of non-compliant redundancy plans
        """
        non_compliant = []

        for entry in entries:
            plan = self.analyze_entry(entry)
            if not plan.is_compliant:
                non_compliant.append(plan)

        return non_compliant

    def suggest_providers(
        self,
        entry: ManifestEntry,
        available_providers: List[str],
        count: int = 1,
    ) -> List[str]:
        """
        Suggest providers for additional copies.

        Args:
            entry: Manifest entry
            available_providers: List of available provider names
            count: Number of providers to suggest

        Returns:
            List of suggested provider names
        """
        config = get_tier_config(entry.tier)
        current_providers = set(entry.get_providers())

        # Filter by allowed providers
        if config.allowed_providers:
            available = [
                p for p in available_providers if p in config.allowed_providers
            ]
        else:
            available = available_providers

        # Remove providers already in use
        available = [p for p in available if p not in current_providers]

        # Prioritize based on tier requirements
        prioritized = []

        # Tier 0: Prefer Proton first, then others
        if entry.tier == Tier.CRITICAL:
            if "proton" in available and "proton" not in current_providers:
                prioritized.append("proton")
            prioritized.extend([p for p in available if p not in ["proton", "local"]])
            if "local" in available:
                prioritized.append("local")

        # Tier 1: Prefer reliable providers
        elif entry.tier == Tier.IMPORTANT:
            # Prefer major providers
            for p in ["gdrive", "onedrive", "box", "proton"]:
                if p in available:
                    prioritized.append(p)
            if "local" in available:
                prioritized.append("local")

        # Tier 2 & 3: Use cheapest/fastest
        else:
            prioritized = available

        # Remove duplicates while preserving order
        seen = set()
        result = []
        for p in prioritized:
            if p not in seen:
                seen.add(p)
                result.append(p)

        return result[:count]

    def calculate_redundancy_score(self, entry: ManifestEntry) -> float:
        """
        Calculate a redundancy score (0.0 to 1.0) for an entry.

        Args:
            entry: Manifest entry

        Returns:
            Score from 0.0 (no redundancy) to 1.0 (meets all requirements)
        """
        config = get_tier_config(entry.tier)
        score = 0.0
        max_score = 5.0  # Maximum possible points

        # Provider count (1 point)
        provider_ratio = len(entry.get_providers()) / config.min_providers
        score += min(1.0, provider_ratio)

        # Copy count (1 point)
        copy_ratio = len(entry.locations) / config.min_copies
        score += min(1.0, copy_ratio)

        # Encryption (1 point)
        if config.require_encryption:
            score += 1.0 if entry.encrypted else 0.0
        else:
            score += 1.0  # Not required, so full points

        # Proton requirement (1 point)
        if config.require_proton:
            score += 1.0 if entry.has_provider("proton") else 0.0
        else:
            score += 1.0

        # Offline requirement (1 point)
        if config.require_offline:
            score += 1.0 if entry.has_provider("local") else 0.0
        else:
            score += 1.0

        return score / max_score

    def prioritize_sync(self, plans: List[RedundancyPlan]) -> List[RedundancyPlan]:
        """
        Prioritize redundancy plans by importance and risk.

        Args:
            plans: List of redundancy plans

        Returns:
            Sorted list with highest priority first
        """

        def priority_key(plan: RedundancyPlan) -> tuple:
            # Sort by:
            # 1. Tier (lower number = higher priority)
            # 2. Number of current copies (fewer = higher priority)
            # 3. Number of actions needed (more = higher priority)
            return (
                int(plan.entry.tier),
                plan.current_copies,
                -len(plan.actions),
            )

        return sorted(plans, key=priority_key)

    def validate_redundancy(
        self, entry: ManifestEntry
    ) -> Dict[str, bool | List[str]]:
        """
        Validate redundancy for an entry.

        Args:
            entry: Manifest entry to validate

        Returns:
            Dictionary with validation results
        """
        config = get_tier_config(entry.tier)
        errors = validate_tier_requirements(
            entry.tier, [loc.to_dict() for loc in entry.locations], entry.encrypted
        )

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "score": self.calculate_redundancy_score(entry),
            "compliant": len(errors) == 0,
        }

    def generate_redundancy_report(
        self, entries: List[ManifestEntry]
    ) -> Dict[str, any]:
        """
        Generate a comprehensive redundancy report.

        Args:
            entries: List of manifest entries

        Returns:
            Report dictionary
        """
        report = {
            "total_files": len(entries),
            "by_tier": {},
            "compliant": 0,
            "non_compliant": 0,
            "average_score": 0.0,
            "critical_issues": [],
            "recommendations": [],
        }

        total_score = 0.0

        for tier in Tier:
            tier_entries = [e for e in entries if e.tier == tier]
            tier_compliant = 0
            tier_non_compliant = 0

            for entry in tier_entries:
                plan = self.analyze_entry(entry)
                score = self.calculate_redundancy_score(entry)
                total_score += score

                if plan.is_compliant:
                    tier_compliant += 1
                    report["compliant"] += 1
                else:
                    tier_non_compliant += 1
                    report["non_compliant"] += 1

                    # Flag critical issues (Tier 0 with < 2 copies)
                    if entry.tier == Tier.CRITICAL and len(entry.locations) < 2:
                        report["critical_issues"].append(
                            {
                                "file": entry.file_name,
                                "hash": entry.content_hash,
                                "copies": len(entry.locations),
                                "reason": "Critical file with insufficient redundancy",
                            }
                        )

            report["by_tier"][tier.name] = {
                "total": len(tier_entries),
                "compliant": tier_compliant,
                "non_compliant": tier_non_compliant,
                "compliance_rate": (
                    tier_compliant / len(tier_entries) if tier_entries else 1.0
                ),
            }

        if entries:
            report["average_score"] = total_score / len(entries)

        # Generate recommendations
        if report["non_compliant"] > 0:
            report["recommendations"].append(
                f"{report['non_compliant']} files need attention to meet tier requirements"
            )

        if report["critical_issues"]:
            report["recommendations"].append(
                f"{len(report['critical_issues'])} critical files need immediate backup"
            )

        return report
