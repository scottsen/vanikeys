"""
VaniKeys CLI - Client tool for zero-knowledge vanity SSH key generation.

Commands:
    init    - Initialize your seed (encrypted, stored locally)
    order   - Order a vanity SSH key
    status  - Check order status
    verify  - Verify cryptographic proof
    derive  - Derive private key locally from seed + path
"""

import sys
from typing import NoReturn

import click

from vanikeys.cli.commands.init import init_command
from vanikeys.cli.commands.order import order_command, status_command
from vanikeys.cli.commands.verify import verify_command
from vanikeys.cli.commands.derive import derive_command


@click.group()
@click.version_option(version="0.2.0", prog_name="vanikeys")
def cli() -> None:
    """VaniKeys - Zero-knowledge vanity SSH key generation.

    Your private keys never leave your machine.
    """
    pass


# Register commands
cli.add_command(init_command, name="init")
cli.add_command(order_command, name="order")
cli.add_command(status_command, name="status")
cli.add_command(verify_command, name="verify")
cli.add_command(derive_command, name="derive")


def main() -> NoReturn:
    """Main entry point for the CLI."""
    try:
        cli()
        sys.exit(0)
    except KeyboardInterrupt:
        click.echo("\n\nInterrupted by user", err=True)
        sys.exit(130)
    except Exception as e:
        click.echo(f"\n❌ Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
