"""Main CLI interface for FileSync."""

import click
import json
from pathlib import Path
from typing import Optional
from ..core.manifest import ManifestManager
from ..core.deduplication import DeduplicationEngine
from ..core.sync import SyncEngine
from ..core.redundancy import RedundancyManager
from ..core.lifecycle import LifecycleManager
from ..models.tier import Tier, DEFAULT_TIER_CONFIGS
from ..providers.local import LocalProvider
from ..encryption.crypto import key_manager


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """
    FileSync - Cloud Storage Deduplication System

    A cross-platform file synchronization and deduplication system with
    importance-based tiering and client-side encryption.
    """
    pass


@cli.command()
@click.option(
    "--manifest-path",
    default="~/.filesync/manifest.db",
    help="Path to manifest database",
)
@click.option(
    "--local-path",
    default="~/filesync-offline",
    help="Path for local/offline storage",
)
def init(manifest_path: str, local_path: str):
    """Initialize FileSync in the current directory."""
    manifest_path = Path(manifest_path).expanduser()
    local_path = Path(local_path).expanduser()

    # Create directories
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    local_path.mkdir(parents=True, exist_ok=True)

    # Initialize manifest
    with ManifestManager(manifest_path) as manifest:
        click.echo(f"✓ Initialized manifest at {manifest_path}")

    # Create config template
    config_path = manifest_path.parent / "config.yaml"
    if not config_path.exists():
        config_template = """# FileSync Configuration

storage:
  manifest_path: {manifest}
  cache_path: {cache}
  temp_path: {temp}

providers:
  local:
    enabled: true
    path: {local}

  gdrive:
    enabled: false
    credentials_file: ~/.filesync/gdrive-creds.json
    root_folder: /FileSync

  onedrive:
    enabled: false
    credentials_file: ~/.filesync/onedrive-creds.json
    root_folder: /FileSync

  box:
    enabled: false
    credentials_file: ~/.filesync/box-creds.json
    root_folder: /FileSync

  proton:
    enabled: false
    credentials_file: ~/.filesync/proton-creds.json
    root_folder: /FileSync

encryption:
  enabled: true
  algorithm: AES-256-GCM
"""
        config_path.write_text(
            config_template.format(
                manifest=str(manifest_path),
                cache=str(manifest_path.parent / "cache"),
                temp=str(manifest_path.parent / "temp"),
                local=str(local_path),
            )
        )
        click.echo(f"✓ Created config at {config_path}")

    click.echo("\n✨ FileSync initialized successfully!")
    click.echo(f"\nManifest: {manifest_path}")
    click.echo(f"Local storage: {local_path}")
    click.echo(f"Config: {config_path}")


@cli.command()
@click.argument("file-path", type=click.Path(exists=True))
@click.option(
    "--tier",
    type=click.Choice(["0", "1", "2", "3"]),
    default="2",
    help="Importance tier (0=Critical, 1=Important, 2=Standard, 3=Archive)",
)
@click.option("--tags", help="Comma-separated tags")
@click.option("--encrypt", is_flag=True, help="Encrypt the file")
@click.option("--reason", help="Reason for tier assignment")
@click.option(
    "--manifest-path",
    default="~/.filesync/manifest.db",
    help="Path to manifest database",
)
def add(
    file_path: str,
    tier: str,
    tags: Optional[str],
    encrypt: bool,
    reason: Optional[str],
    manifest_path: str,
):
    """Add a file to FileSync."""
    manifest_path = Path(manifest_path).expanduser()

    if not manifest_path.exists():
        click.echo("❌ Manifest not found. Run 'filesync init' first.", err=True)
        return

    # Parse tier
    tier_value = Tier(int(tier))

    # Parse tags
    tag_list = [t.strip() for t in tags.split(",")] if tags else []

    # Set up passphrase if encryption is required
    if encrypt or tier_value == Tier.CRITICAL:
        passphrase = click.prompt(
            "Enter encryption passphrase", hide_input=True, confirmation_prompt=True
        )
        key_manager.set_master_passphrase(passphrase)
        encrypt = True

    # Initialize components
    with ManifestManager(manifest_path) as manifest:
        local_provider = LocalProvider(
            manifest_path.parent.parent / "filesync-offline"
        )
        providers = {"local": local_provider}

        sync = SyncEngine(manifest, providers)

        # Add file
        click.echo(f"Adding {file_path}...")
        success, entry, result = sync.add_file(
            file_path, tier_value, tag_list, reason, encrypt
        )

        if success:
            click.echo(f"✓ File added successfully!")
            click.echo(f"  Hash: {entry.content_hash}")
            click.echo(f"  Tier: {entry.tier.name}")
            click.echo(f"  Locations: {len(entry.locations)}")
            if result.duplicates_found:
                click.echo(f"  ⚠ Duplicate detected - merged with existing entry")
        else:
            click.echo(f"❌ Failed to add file", err=True)
            for error in result.errors:
                click.echo(f"  {error}", err=True)


@cli.command()
@click.option(
    "--manifest-path",
    default="~/.filesync/manifest.db",
    help="Path to manifest database",
)
def status(manifest_path: str):
    """Show FileSync status."""
    manifest_path = Path(manifest_path).expanduser()

    if not manifest_path.exists():
        click.echo("❌ Manifest not found. Run 'filesync init' first.", err=True)
        return

    with ManifestManager(manifest_path) as manifest:
        stats = manifest.get_statistics()

        click.echo("\n📊 FileSync Status\n")
        click.echo(f"Total files: {stats['total_files']}")
        click.echo(f"Total size: {_format_bytes(stats['total_size'])}")
        click.echo(f"Encrypted: {stats['encrypted_files']}")

        click.echo("\n📁 By Tier:")
        for tier_name, count in stats["by_tier"].items():
            click.echo(f"  {tier_name}: {count}")

        click.echo("\n☁️  By Provider:")
        for provider, count in stats["by_provider"].items():
            click.echo(f"  {provider}: {count}")


@cli.command()
@click.option(
    "--manifest-path",
    default="~/.filesync/manifest.db",
    help="Path to manifest database",
)
@click.option("--tier", help="Filter by tier (0-3)")
@click.option("--tag", help="Filter by tag")
def list(manifest_path: str, tier: Optional[str], tag: Optional[str]):
    """List all files in FileSync."""
    manifest_path = Path(manifest_path).expanduser()

    if not manifest_path.exists():
        click.echo("❌ Manifest not found.", err=True)
        return

    with ManifestManager(manifest_path) as manifest:
        # Get entries
        if tier:
            entries = manifest.get_entries_by_tier(Tier(int(tier)))
        elif tag:
            entries = manifest.get_entries_by_tag(tag)
        else:
            entries = manifest.get_all_entries()

        click.echo(f"\nFound {len(entries)} files:\n")

        for entry in entries:
            encrypted_flag = "🔒" if entry.encrypted else "  "
            click.echo(
                f"{encrypted_flag} {entry.file_name} ({entry.tier.name}) - "
                f"{len(entry.locations)} copies"
            )
            click.echo(f"   Hash: {entry.content_hash[:24]}...")
            if entry.tags:
                click.echo(f"   Tags: {', '.join(entry.tags)}")


@cli.command()
@click.option(
    "--manifest-path",
    default="~/.filesync/manifest.db",
    help="Path to manifest database",
)
def validate(manifest_path: str):
    """Validate redundancy for all files."""
    manifest_path = Path(manifest_path).expanduser()

    if not manifest_path.exists():
        click.echo("❌ Manifest not found.", err=True)
        return

    with ManifestManager(manifest_path) as manifest:
        redundancy = RedundancyManager()

        click.echo("🔍 Validating redundancy...\n")

        entries = manifest.get_all_entries()
        non_compliant = redundancy.get_non_compliant_entries(entries)

        if not non_compliant:
            click.echo("✓ All files meet their tier requirements!")
            return

        click.echo(f"⚠  {len(non_compliant)} files need attention:\n")

        for plan in non_compliant:
            entry = plan.entry
            click.echo(f"• {entry.file_name} ({entry.tier.name})")
            click.echo(f"  Current: {plan.current_copies} copies on {len(plan.current_providers)} providers")
            click.echo(f"  Required: {plan.required_copies} copies on {plan.required_providers} providers")
            click.echo(f"  Actions needed: {', '.join(plan.actions)}\n")


@cli.command()
@click.option(
    "--manifest-path",
    default="~/.filesync/manifest.db",
    help="Path to manifest database",
)
@click.option("--dry-run", is_flag=True, help="Show what would be done without making changes")
def apply_policies(manifest_path: str, dry_run: bool):
    """Apply lifecycle policies to all files."""
    manifest_path = Path(manifest_path).expanduser()

    if not manifest_path.exists():
        click.echo("❌ Manifest not found.", err=True)
        return

    with ManifestManager(manifest_path) as manifest:
        lifecycle = LifecycleManager()

        entries = manifest.get_all_entries()

        click.echo(f"🔄 Applying policies to {len(entries)} files...\n")

        report = lifecycle.apply_policies(entries, dry_run=dry_run)

        click.echo(f"Policies evaluated: {report['policies_evaluated']}")
        click.echo(f"Entries modified: {report['entries_modified']}")

        if report["actions"]:
            click.echo("\n📋 Actions:\n")
            for action in report["actions"]:
                if "error" in action:
                    click.echo(f"  ❌ {action['policy']}: {action['file']} - {action['error']}")
                else:
                    click.echo(
                        f"  • {action['file']}: {action['old_tier']} → {action['new_tier']}"
                    )

        if dry_run:
            click.echo("\n(Dry run - no changes made)")


@cli.command()
@click.option(
    "--manifest-path",
    default="~/.filesync/manifest.db",
    help="Path to manifest database",
)
def tiers(manifest_path: str):
    """Show tier configuration."""
    click.echo("\n📊 Importance Tiers\n")

    for tier in Tier:
        config = DEFAULT_TIER_CONFIGS[tier]
        click.echo(f"{tier.value}. {config.name} - {config.description}")
        click.echo(f"   Copies: {config.min_copies} across {config.min_providers} providers")
        if config.require_encryption:
            click.echo(f"   🔒 Encryption required")
        if config.require_proton:
            click.echo(f"   ☁️  Proton Drive required")
        if config.require_offline:
            click.echo(f"   💾 Offline copy required")
        click.echo()


def _format_bytes(size: int) -> str:
    """Format bytes as human-readable string."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} PB"


if __name__ == "__main__":
    cli()
