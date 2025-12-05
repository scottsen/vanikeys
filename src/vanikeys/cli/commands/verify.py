"""
'vanikeys verify' command - Verify cryptographic proofs.
"""

import sys
import click

from vanikeys.cli.storage import SeedStorage
from vanikeys.cli.api_client import VaniKeysAPIClient
from vanikeys.crypto.proofs import verify_order_proof_passwordless


@click.command()
@click.argument("order_id")
@click.option(
    "--api-url",
    default=None,
    help="VaniKeys API URL (default: production)",
)
def verify_command(order_id, api_url):
    """Verify cryptographic proof for an order.

    This checks that:
    1. The derivation proof is valid (root key + path = child key)
    2. The child key fingerprint matches the pattern
    3. The proof hasn't been tampered with

    You should ALWAYS verify before deriving your private key!

    \b
    Example:
        vanikeys verify ord_abc123xyz
    """
    storage = SeedStorage()

    # Check initialization
    if not storage.exists():
        click.echo("❌ Not initialized. Run 'vanikeys init' first.")
        sys.exit(1)

    # Get root public key
    root_public_key_bytes = storage.get_root_public_key()
    if not root_public_key_bytes:
        click.echo("❌ Could not load root public key")
        sys.exit(1)

    click.echo("🔍 Verifying cryptographic proof...")
    click.echo(f"   Order ID: {order_id}")
    click.echo()

    try:
        # Fetch proof from server
        click.echo("📡 Fetching proof from server...")
        with VaniKeysAPIClient(base_url=api_url) as client:
            proof_data = client.get_order_proof(order_id)

        click.echo(f"   ✓ Proof received")
        click.echo()

        # Verify proof (passwordless - doesn't require seed)
        click.echo("🔐 Verifying proof...")
        result = verify_order_proof_passwordless(proof_data, root_public_key_bytes)

        if result["valid"]:
            click.echo("✅ Proof is VALID")
            click.echo()
            click.echo("📋 Verified Details:")
            click.echo(f"   Path index: {proof_data['derivation_proof']['path_index']}")
            click.echo(f"   Pattern: {proof_data['pattern']}")
            click.echo(f"   Fingerprint: {result['fingerprint']}")
            click.echo(f"   Match: {result['match']}")
            click.echo()
            click.echo("🔒 Security guarantees:")
            click.echo("   ✓ Derivation path is correct")
            click.echo("   ✓ Child public key matches")
            click.echo("   ✓ Fingerprint matches pattern")
            click.echo("   ✓ Proof hasn't been tampered with")
            click.echo()
            click.echo("💡 Safe to derive your private key:")
            click.echo(f"   vanikeys derive {order_id} --output ~/.ssh/mykey")

        else:
            click.echo("❌ Proof is INVALID")
            click.echo()
            click.echo("⚠️  Verification failures:")
            for check, passed in result["checks"].items():
                status = "✓" if passed else "✗"
                click.echo(f"   {status} {check}")

            click.echo()
            click.echo("🚨 DO NOT derive this key!")
            click.echo("   The proof verification failed. This could indicate:")
            click.echo("   • Server error or data corruption")
            click.echo("   • Attempted fraud or tampering")
            click.echo("   • Man-in-the-middle attack")
            click.echo()
            click.echo("   Contact support: support@vanikeys.dev")
            sys.exit(1)

    except Exception as e:
        click.echo(f"❌ Verification failed: {e}", err=True)
        sys.exit(1)
