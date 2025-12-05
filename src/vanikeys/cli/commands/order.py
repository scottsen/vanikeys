"""
'vanikeys order' and 'vanikeys status' commands.
"""

import sys
import time
import click

from vanikeys.cli.storage import SeedStorage
from vanikeys.cli.api_client import VaniKeysAPIClient
from vanikeys.crypto.matching import estimate_pattern_difficulty, validate_pattern


@click.command()
@click.argument("key_type", type=click.Choice(["ssh"], case_sensitive=False))
@click.option(
    "--pattern",
    "-p",
    required=True,
    help="Vanity pattern to search for (e.g., 'dev123')",
)
@click.option(
    "--api-url",
    default=None,
    help="VaniKeys API URL (default: production)",
)
@click.option(
    "--wait/--no-wait",
    default=True,
    help="Wait for order completion (default: yes)",
)
def order_command(key_type, pattern, api_url, wait):
    """Order a vanity SSH key.

    \b
    Example:
        vanikeys order ssh --pattern dev123

    \b
    The pattern will be searched for in the SSH fingerprint:
        SHA256:dev123xxxxxxxxxxxxxxxxxxxxxxxxx

    \b
    Pattern rules:
        - Case insensitive
        - Base64 characters only: [A-Za-z0-9+/]
        - Longer patterns = harder/more expensive
    """
    storage = SeedStorage()

    # Check initialization
    if not storage.exists():
        click.echo("❌ Not initialized. Run 'vanikeys init' first.")
        sys.exit(1)

    # Validate pattern
    validation = validate_pattern(pattern)
    if validation["errors"]:
        click.echo("❌ Invalid pattern:")
        for error in validation["errors"]:
            click.echo(f"   • {error}")
        sys.exit(1)

    if validation["warnings"]:
        click.echo("⚠️  Pattern warnings:")
        for warning in validation["warnings"]:
            click.echo(f"   • {warning}")
        if not click.confirm("Continue?", default=True):
            sys.exit(0)
        click.echo()

    # Get root public key
    root_public_key_bytes = storage.get_root_public_key()
    if not root_public_key_bytes:
        click.echo("❌ Could not load root public key")
        sys.exit(1)

    root_public_key_hex = root_public_key_bytes.hex()

    # Estimate difficulty
    click.echo("📊 Estimating pattern difficulty...")
    difficulty = estimate_pattern_difficulty(pattern)
    click.echo(f"   Pattern: {pattern}")
    click.echo(f"   Difficulty: {difficulty['difficulty_class']}")
    click.echo(f"   Expected attempts: {difficulty['expected_attempts']:,}")
    click.echo(f"   Estimated time: {difficulty['estimated_duration']}")
    click.echo(f"   Estimated cost: ${difficulty['estimated_cost']:.2f}")
    click.echo()

    if not click.confirm("Create order?", default=True):
        click.echo("Cancelled.")
        sys.exit(0)

    # Create order
    click.echo("📡 Creating order...")
    try:
        with VaniKeysAPIClient(base_url=api_url) as client:
            response = client.create_order(
                pattern=pattern,
                root_public_key=root_public_key_hex,
                key_type=key_type,
            )

        click.echo(f"   ✓ Order created: {response.order_id}")
        click.echo()
        click.echo("📋 Order Details:")
        click.echo(f"   Order ID: {response.order_id}")
        click.echo(f"   Pattern: {response.pattern}")
        click.echo(f"   Difficulty: {response.difficulty}")
        click.echo(f"   Estimated time: {response.estimated_time}")
        click.echo(f"   Cost: ${response.cost_usd:.2f}")
        click.echo(f"   Status: {response.status}")
        click.echo()

        if wait:
            click.echo("⏳ Waiting for order completion...")
            click.echo("   (Press Ctrl+C to stop waiting)")
            _wait_for_order(client, response.order_id)
        else:
            click.echo("💡 Check status with:")
            click.echo(f"   vanikeys status {response.order_id}")

    except Exception as e:
        click.echo(f"❌ Order failed: {e}", err=True)
        sys.exit(1)


@click.command()
@click.argument("order_id")
@click.option(
    "--api-url",
    default=None,
    help="VaniKeys API URL (default: production)",
)
@click.option(
    "--wait/--no-wait",
    default=False,
    help="Wait for order completion",
)
def status_command(order_id, api_url, wait):
    """Check order status.

    \b
    Example:
        vanikeys status ord_abc123xyz
    """
    try:
        with VaniKeysAPIClient(base_url=api_url) as client:
            status = client.get_order_status(order_id)

        click.echo("📋 Order Status:")
        click.echo(f"   Order ID: {status.order_id}")
        click.echo(f"   Pattern: {status.pattern}")
        click.echo(f"   Status: {status.status}")

        if status.progress:
            tested = status.progress.get("paths_tested", 0)
            total = status.progress.get("estimated_total", 0)
            if total > 0:
                pct = (tested / total) * 100
                click.echo(f"   Progress: {tested:,} / {total:,} paths ({pct:.1f}%)")
            else:
                click.echo(f"   Paths tested: {tested:,}")

        if status.result:
            click.echo()
            click.echo("✅ Match found!")
            click.echo(f"   Path: {status.result['path']}")
            click.echo(f"   Fingerprint: {status.result['fingerprint']}")
            click.echo(f"   Public key: {status.result['public_key'][:50]}...")
            click.echo()
            click.echo("💡 Next steps:")
            click.echo(f"   1. Verify proof: vanikeys verify {order_id}")
            click.echo(
                f"   2. Derive key: vanikeys derive {order_id} "
                "--output ~/.ssh/mykey"
            )

        elif status.status == "FAILED":
            click.echo()
            click.echo("❌ Order failed")

        elif wait:
            click.echo()
            click.echo("⏳ Waiting for completion...")
            _wait_for_order(client, order_id)

    except Exception as e:
        click.echo(f"❌ Status check failed: {e}", err=True)
        sys.exit(1)


def _wait_for_order(client: VaniKeysAPIClient, order_id: str, poll_interval: int = 5):
    """Poll order status until completion.

    Args:
        client: API client
        order_id: Order ID to poll
        poll_interval: Seconds between polls
    """
    last_tested = 0

    try:
        while True:
            time.sleep(poll_interval)

            status = client.get_order_status(order_id)

            if status.progress:
                tested = status.progress.get("paths_tested", 0)
                if tested > last_tested:
                    click.echo(f"   • Tested {tested:,} paths...")
                    last_tested = tested

            if status.status == "FOUND":
                click.echo()
                click.echo("✅ Match found!")
                click.echo(f"   Path: {status.result['path']}")
                click.echo(f"   Fingerprint: {status.result['fingerprint']}")
                click.echo()
                click.echo("💡 Next steps:")
                click.echo(f"   1. Verify proof: vanikeys verify {order_id}")
                click.echo(
                    f"   2. Derive key: vanikeys derive {order_id} "
                    "--output ~/.ssh/mykey"
                )
                break

            elif status.status == "FAILED":
                click.echo()
                click.echo("❌ Order failed")
                sys.exit(1)

    except KeyboardInterrupt:
        click.echo()
        click.echo("⏸️  Stopped waiting (order continues running)")
        click.echo(f"   Check status: vanikeys status {order_id}")
