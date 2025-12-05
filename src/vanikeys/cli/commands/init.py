"""
'vanikeys init' command - Initialize seed and configuration.
"""

import sys
import click
import getpass

from vanikeys.crypto.derivation import (
    generate_master_seed,
    seed_to_root_keypair,
    public_key_to_bytes,
)
from vanikeys.cli.storage import SeedStorage


@click.command()
@click.option(
    "--storage-dir",
    type=click.Path(),
    default=None,
    help="Custom storage directory (default: ~/.vanikeys)",
)
@click.option(
    "--force",
    is_flag=True,
    help="Overwrite existing seed (dangerous!)",
)
def init_command(storage_dir, force):
    """Initialize your VaniKeys seed.

    This creates a cryptographically secure random seed, encrypts it with
    your password, and stores it locally. Your seed NEVER leaves your machine.

    \b
    What gets created:
    - ~/.vanikeys/seed.enc - Your encrypted seed
    - ~/.vanikeys/config.json - Configuration

    \b
    Security:
    - Seed is 32 random bytes (256-bit security)
    - Encrypted with PBKDF2 + Fernet (AES-128)
    - 600,000 KDF iterations (OWASP 2023 recommendation)
    - File permissions: 0600 (owner read/write only)
    """
    storage = SeedStorage(storage_dir)

    # Check if already initialized
    if storage.exists() and not force:
        click.echo("❌ Seed already exists at: " + str(storage.seed_file))
        click.echo(
            "   Use --force to overwrite "
            "(you will lose access to existing keys!)"
        )
        sys.exit(1)

    click.echo("🔐 VaniKeys Initialization")
    click.echo("=" * 50)
    click.echo()

    if force:
        click.echo("⚠️  WARNING: Overwriting existing seed!")
        click.echo("   You will lose access to keys derived from the old seed.")
        if not click.confirm("   Continue?", default=False):
            click.echo("Cancelled.")
            sys.exit(0)
        click.echo()

    # Generate seed
    click.echo("🎲 Generating cryptographically secure random seed...")
    seed = generate_master_seed()
    click.echo(f"   ✓ Generated 32-byte seed")

    # Derive root keypair
    click.echo("🔑 Deriving root keypair...")
    root_private_key, root_public_key = seed_to_root_keypair(seed)
    root_public_key_bytes = public_key_to_bytes(root_public_key)
    click.echo(f"   ✓ Root public key: {root_public_key_bytes.hex()[:16]}...")

    # Get password
    click.echo()
    click.echo("🔒 Choose a strong password to encrypt your seed:")
    click.echo("   (This password is required to use your keys)")

    while True:
        password = getpass.getpass("   Password: ")
        if len(password) < 8:
            click.echo("   ❌ Password must be at least 8 characters")
            continue

        password_confirm = getpass.getpass("   Confirm password: ")
        if password != password_confirm:
            click.echo("   ❌ Passwords don't match, try again")
            continue

        break

    # Save encrypted seed
    click.echo()
    click.echo("💾 Encrypting and saving seed...")
    storage.save_seed(seed, password, root_public_key_bytes)
    click.echo(f"   ✓ Saved to: {storage.seed_file}")

    # Save config
    config = {
        "version": "0.2.0",
        "root_public_key": root_public_key_bytes.hex(),
    }
    storage.save_config(config)

    # Success message
    click.echo()
    click.echo("✅ Initialization complete!")
    click.echo()
    click.echo("📋 Important:")
    click.echo(f"   • Seed location: {storage.seed_file}")
    click.echo("   • Your seed is encrypted and ONLY stored locally")
    click.echo("   • BACK UP YOUR SEED to avoid losing access to your keys")
    click.echo(f"   • Root public key: {root_public_key_bytes.hex()}")
    click.echo()
    click.echo("💡 Next steps:")
    click.echo("   1. Back up your seed: cp ~/.vanikeys/seed.enc ~/backup/")
    click.echo("   2. Order a vanity key: vanikeys order ssh --pattern dev123")
