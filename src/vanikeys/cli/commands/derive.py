"""
'vanikeys derive' command - Derive private key locally from seed + path.
"""

import sys
import getpass
from pathlib import Path

import click

from vanikeys.cli.storage import SeedStorage
from vanikeys.cli.api_client import VaniKeysAPIClient
from vanikeys.crypto.derivation import (
    seed_to_root_keypair,
    derive_child_keypair,
    public_key_to_bytes,
    private_key_to_bytes,
)
from vanikeys.crypto.fingerprint import (
    compute_ssh_fingerprint,
    ssh_public_key_to_authorized_keys_format,
)
from vanikeys.crypto.proofs import verify_order_proof


@click.command()
@click.argument("order_id")
@click.option(
    "--output",
    "-o",
    required=True,
    type=click.Path(),
    help="Output path for private key (e.g., ~/.ssh/mykey)",
)
@click.option(
    "--api-url",
    default=None,
    help="VaniKeys API URL (default: production)",
)
@click.option(
    "--skip-verify",
    is_flag=True,
    help="Skip proof verification (NOT RECOMMENDED)",
)
@click.option(
    "--force",
    is_flag=True,
    help="Overwrite existing key file",
)
def derive_command(order_id, output, api_url, skip_verify, force):
    """Derive your private key locally from seed + path.

    This generates your Ed25519 private key ON YOUR MACHINE using:
    - Your secret seed (never leaves your machine)
    - The derivation path VaniKeys found

    The server NEVER sees your private key!

    \b
    Example:
        vanikeys derive ord_abc123xyz --output ~/.ssh/dev_key

    \b
    This creates:
        ~/.ssh/dev_key      (private key, 0600 permissions)
        ~/.ssh/dev_key.pub  (public key, OpenSSH format)
    """
    storage = SeedStorage()

    # Check initialization
    if not storage.exists():
        click.echo("❌ Not initialized. Run 'vanikeys init' first.")
        sys.exit(1)

    output_path = Path(output).expanduser()
    output_pub_path = output_path.with_suffix(output_path.suffix + ".pub")

    # Check existing files
    if output_path.exists() and not force:
        click.echo(f"❌ File already exists: {output_path}")
        click.echo("   Use --force to overwrite")
        sys.exit(1)

    click.echo("🔑 Deriving your private key locally...")
    click.echo(f"   Order ID: {order_id}")
    click.echo()

    try:
        # Fetch order details
        click.echo("📡 Fetching order details...")
        with VaniKeysAPIClient(base_url=api_url) as client:
            status = client.get_order_status(order_id)
            proof_data = client.get_order_proof(order_id)

        if status.status != "FOUND":
            click.echo(f"❌ Order not complete. Status: {status.status}")
            sys.exit(1)

        click.echo(f"   ✓ Order found")
        click.echo(f"   Pattern: {status.pattern}")
        click.echo(f"   Path: {proof_data['derivation_proof']['path_index']}")
        click.echo()

        # Verify proof (unless skipped)
        if not skip_verify:
            click.echo("🔐 Verifying cryptographic proof...")
            root_public_key_bytes = storage.get_root_public_key()

            result = verify_order_proof(proof_data, root_public_key_bytes)

            if not result["valid"]:
                click.echo("❌ Proof verification FAILED!")
                click.echo()
                click.echo("⚠️  Verification failures:")
                for check, passed in result["checks"].items():
                    status_icon = "✓" if passed else "✗"
                    click.echo(f"   {status_icon} {check}")
                click.echo()
                click.echo("🚨 REFUSING to derive key with invalid proof!")
                click.echo("   Run 'vanikeys verify' for details.")
                sys.exit(1)

            click.echo("   ✓ Proof valid")
            click.echo()
        else:
            click.echo("⚠️  SKIPPING proof verification (not recommended)")
            click.echo()

        # Get password
        click.echo("🔒 Enter password to decrypt your seed:")
        password = getpass.getpass("   Password: ")

        # Load seed
        click.echo("📂 Loading encrypted seed...")
        try:
            seed, _ = storage.load_seed(password)
            click.echo("   ✓ Seed decrypted")
        except ValueError as e:
            click.echo(f"❌ Failed to decrypt seed: {e}")
            sys.exit(1)

        # Derive root keypair
        click.echo("🌱 Deriving root keypair from seed...")
        root_private_key, root_public_key = seed_to_root_keypair(seed)
        click.echo("   ✓ Root keypair derived")

        # Derive child keypair
        path_index = proof_data["derivation_proof"]["path_index"]
        click.echo(f"🔀 Deriving child key at path {path_index}...")
        child_private_key, child_public_key = derive_child_keypair(
            seed, root_private_key, root_public_key, path_index
        )
        click.echo("   ✓ Child keypair derived")

        # Verify fingerprint matches
        child_public_bytes = public_key_to_bytes(child_public_key)
        fingerprint = compute_ssh_fingerprint(child_public_bytes)
        expected_fingerprint = proof_data["fingerprint"]

        if fingerprint != expected_fingerprint:
            click.echo("❌ CRITICAL ERROR: Fingerprint mismatch!")
            click.echo(f"   Expected: {expected_fingerprint}")
            click.echo(f"   Got: {fingerprint}")
            click.echo()
            click.echo("🚨 This should never happen. Possible causes:")
            click.echo("   • Wrong seed (did you use --force?)")
            click.echo("   • Data corruption")
            click.echo("   • Software bug")
            sys.exit(1)

        click.echo(f"   ✓ Fingerprint matches: {fingerprint}")
        click.echo()

        # Write private key
        click.echo("💾 Writing private key...")
        private_key_bytes = private_key_to_bytes(child_private_key)

        # Create parent directory if needed
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write private key with restrictive permissions
        with open(output_path, "wb") as f:
            f.write(private_key_bytes)
        output_path.chmod(0o600)
        click.echo(f"   ✓ Private key: {output_path} (0600)")

        # Write public key
        public_key_openssh = ssh_public_key_to_authorized_keys_format(
            child_public_bytes, comment=f"VaniKeys {order_id}"
        )
        with open(output_pub_path, "w") as f:
            f.write(public_key_openssh)
        output_pub_path.chmod(0o644)
        click.echo(f"   ✓ Public key: {output_pub_path} (0644)")

        # Success!
        click.echo()
        click.echo("✅ Key derivation complete!")
        click.echo()
        click.echo("📋 Your vanity SSH key:")
        click.echo(f"   Fingerprint: {fingerprint}")
        click.echo(f"   Pattern: {status.pattern}")
        click.echo(f"   Private key: {output_path}")
        click.echo(f"   Public key: {output_pub_path}")
        click.echo()
        click.echo("🔒 Security reminder:")
        click.echo("   • Your private key was generated ON YOUR MACHINE")
        click.echo("   • VaniKeys NEVER saw your private key")
        click.echo("   • The server only knew the derivation path")
        click.echo()
        click.echo("💡 Use your key:")
        click.echo(f"   ssh-add {output_path}")
        click.echo(f"   ssh-keygen -lf {output_pub_path}  # Verify fingerprint")

    except Exception as e:
        click.echo(f"❌ Derivation failed: {e}", err=True)
        sys.exit(1)
