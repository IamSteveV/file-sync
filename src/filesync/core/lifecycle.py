"""Automated lifecycle management and policies."""

from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List, Callable, Optional
from ..models.manifest_entry import ManifestEntry
from ..models.tier import Tier


@dataclass
class Policy:
    """A lifecycle policy rule."""

    name: str
    description: str
    condition: Callable[[ManifestEntry], bool]
    action: Callable[[ManifestEntry], ManifestEntry]
    enabled: bool = True


class LifecycleManager:
    """
    Manages automated lifecycle policies for files.

    Handles:
    - Tier promotion (increase importance)
    - Tier demotion (decrease importance)
    - Archival rules
    - Deletion rules
    - Tag-based automation
    """

    def __init__(self):
        """Initialize lifecycle manager."""
        self.policies: List[Policy] = []
        self._register_default_policies()

    def _register_default_policies(self):
        """Register default lifecycle policies."""

        # Promotion policies
        self.add_policy(
            Policy(
                name="promote_legal_documents",
                description="Promote files tagged as legal to Critical tier",
                condition=lambda e: any(
                    tag in e.tags for tag in ["legal", "tax", "contract", "passport"]
                )
                and e.tier != Tier.CRITICAL,
                action=lambda e: self._set_tier(
                    e, Tier.CRITICAL, "Contains legal/sensitive tags"
                ),
            )
        )

        self.add_policy(
            Policy(
                name="promote_active_work",
                description="Promote recently modified work files to Important",
                condition=lambda e: "work" in e.tags
                and self._days_since_modified(e) < 30
                and e.tier > Tier.IMPORTANT,
                action=lambda e: self._set_tier(
                    e, Tier.IMPORTANT, "Recently modified work file"
                ),
            )
        )

        # Demotion policies
        self.add_policy(
            Policy(
                name="demote_old_standard",
                description="Demote old Standard files to Archive",
                condition=lambda e: e.tier == Tier.STANDARD
                and self._days_since_modified(e) > 365
                and "permanent" not in e.tags,
                action=lambda e: self._set_tier(
                    e, Tier.ARCHIVE, "Not accessed in over a year"
                ),
            )
        )

        self.add_policy(
            Policy(
                name="demote_completed_projects",
                description="Demote completed project files after 90 days",
                condition=lambda e: "completed" in e.tags
                and e.tier == Tier.IMPORTANT
                and self._days_since_modified(e) > 90,
                action=lambda e: self._set_tier(
                    e, Tier.STANDARD, "Project marked as completed"
                ),
            )
        )

        # Tag-based automation
        self.add_policy(
            Policy(
                name="tag_duplicates",
                description="Auto-tag files marked as duplicates",
                condition=lambda e: "duplicate" in e.file_name.lower()
                and "duplicate" not in e.tags,
                action=lambda e: self._add_tag(e, "duplicate"),
            )
        )

        self.add_policy(
            Policy(
                name="tag_images",
                description="Auto-tag image files",
                condition=lambda e: e.mime_type.startswith("image/")
                and "image" not in e.tags,
                action=lambda e: self._add_tag(e, "image"),
            )
        )

    def add_policy(self, policy: Policy):
        """Add a custom policy."""
        self.policies.append(policy)

    def remove_policy(self, name: str) -> bool:
        """Remove a policy by name."""
        original_len = len(self.policies)
        self.policies = [p for p in self.policies if p.name != name]
        return len(self.policies) < original_len

    def enable_policy(self, name: str) -> bool:
        """Enable a policy by name."""
        for policy in self.policies:
            if policy.name == name:
                policy.enabled = True
                return True
        return False

    def disable_policy(self, name: str) -> bool:
        """Disable a policy by name."""
        for policy in self.policies:
            if policy.name == name:
                policy.enabled = False
                return True
        return False

    def apply_policies(
        self, entries: List[ManifestEntry], dry_run: bool = False
    ) -> dict:
        """
        Apply all enabled policies to a list of entries.

        Args:
            entries: List of manifest entries
            dry_run: If True, don't actually modify entries

        Returns:
            Report of actions taken
        """
        report = {
            "total_entries": len(entries),
            "policies_evaluated": len([p for p in self.policies if p.enabled]),
            "entries_modified": 0,
            "actions": [],
        }

        for entry in entries:
            original_tier = entry.tier
            original_tags = entry.tags.copy()
            modified = False

            for policy in self.policies:
                if not policy.enabled:
                    continue

                try:
                    if policy.condition(entry):
                        if not dry_run:
                            entry = policy.action(entry)

                        # Check if entry was modified
                        if entry.tier != original_tier or entry.tags != original_tags:
                            modified = True
                            report["actions"].append(
                                {
                                    "policy": policy.name,
                                    "file": entry.file_name,
                                    "hash": entry.content_hash,
                                    "old_tier": original_tier.name,
                                    "new_tier": entry.tier.name,
                                    "tags": entry.tags,
                                }
                            )

                except Exception as e:
                    report["actions"].append(
                        {
                            "policy": policy.name,
                            "file": entry.file_name,
                            "error": str(e),
                        }
                    )

            if modified:
                report["entries_modified"] += 1

        return report

    def suggest_policies(self, entry: ManifestEntry) -> List[str]:
        """
        Suggest policy actions for a specific entry.

        Args:
            entry: Manifest entry

        Returns:
            List of suggested actions
        """
        suggestions = []

        # Check for tier mismatches based on tags
        if any(tag in entry.tags for tag in ["legal", "tax", "contract"]):
            if entry.tier != Tier.CRITICAL:
                suggestions.append(
                    f"Consider promoting to Critical tier (currently {entry.tier.name})"
                )

        # Check for encryption requirements
        if entry.tier == Tier.CRITICAL and not entry.encrypted:
            suggestions.append("Critical files should be encrypted")

        # Check for redundancy
        if entry.tier == Tier.CRITICAL and len(entry.locations) < 3:
            suggestions.append(
                f"Critical files need 3 copies (currently has {len(entry.locations)})"
            )

        # Check for old files
        days_old = self._days_since_modified(entry)
        if days_old > 730 and entry.tier > Tier.ARCHIVE:
            suggestions.append(
                f"File not modified in {days_old} days, consider archiving"
            )

        return suggestions

    def _set_tier(
        self, entry: ManifestEntry, tier: Tier, reason: str
    ) -> ManifestEntry:
        """Set entry tier with reason."""
        entry.tier = tier
        entry.importance_reason = reason
        return entry

    def _add_tag(self, entry: ManifestEntry, tag: str) -> ManifestEntry:
        """Add a tag to entry."""
        entry.add_tag(tag)
        return entry

    def _days_since_modified(self, entry: ManifestEntry) -> int:
        """Calculate days since entry was last modified."""
        now = datetime.utcnow()
        delta = now - entry.modified_at
        return delta.days

    def _days_since_created(self, entry: ManifestEntry) -> int:
        """Calculate days since entry was created."""
        now = datetime.utcnow()
        delta = now - entry.created_at
        return delta.days

    def get_policy_report(self) -> dict:
        """Get a report of all policies."""
        return {
            "total_policies": len(self.policies),
            "enabled": len([p for p in self.policies if p.enabled]),
            "disabled": len([p for p in self.policies if not p.enabled]),
            "policies": [
                {
                    "name": p.name,
                    "description": p.description,
                    "enabled": p.enabled,
                }
                for p in self.policies
            ],
        }
