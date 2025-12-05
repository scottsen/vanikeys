"""Main CLI entry point for VaniKeys."""

import click
import sys
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from vanikeys.core.engine import VanityEngine
from vanikeys.core.difficulty import DifficultyCalculator, format_difficulty_table
from vanikeys.core.types import PatternConfig, PatternMatchType, GenerationConfig
from vanikeys.generators.ed25519 import Ed25519Generator, Ed25519DIDGenerator
from vanikeys.matchers.simple import (
    PrefixMatcher,
    SuffixMatcher,
    ContainsMatcher,
    RegexMatcher
)

console = Console()


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """
    VaniKeys - Vanity cryptographic key generation.

    Generate keys with custom patterns in public key hashes/addresses.
    """
    pass


@cli.command()
@click.argument("pattern")
@click.option(
    "--type",
    "key_type",
    type=click.Choice(["ed25519", "did:key"], case_sensitive=False),
    default="ed25519",
    help="Key type to generate"
)
@click.option(
    "--match",
    type=click.Choice(["prefix", "suffix", "contains", "regex"], case_sensitive=False),
    default="contains",
    help="Pattern matching mode"
)
@click.option(
    "--case-sensitive/--case-insensitive",
    default=False,
    help="Case-sensitive pattern matching"
)
@click.option(
    "--workers",
    type=int,
    default=1,
    help="Number of parallel workers (CPU cores)"
)
@click.option(
    "--max-attempts",
    type=int,
    help="Maximum generation attempts (default: unlimited)"
)
@click.option(
    "--timeout",
    type=float,
    help="Timeout in seconds (default: unlimited)"
)
@click.option(
    "--output",
    type=click.Path(),
    help="Save key to file (default: print to stdout)"
)
@click.option(
    "--format",
    "export_format",
    type=click.Choice(["pem", "json", "hex", "did", "did_document"], case_sensitive=False),
    default="pem",
    help="Output format"
)
def generate(
    pattern: str,
    key_type: str,
    match: str,
    case_sensitive: bool,
    workers: int,
    max_attempts: int,
    timeout: float,
    output: str,
    export_format: str
):
    """
    Generate a vanity key matching PATTERN.

    Examples:
        vanikeys generate ABC --type did:key
        vanikeys generate DEAD --match prefix --workers 4
        vanikeys generate "^[0-9]{4}" --match regex
    """
    # Create generator
    if key_type.lower() == "did:key":
        generator = Ed25519DIDGenerator()
    else:
        generator = Ed25519Generator(encoding="base58")

    # Create matcher
    match_type = match.lower()
    if match_type == "prefix":
        matcher = PrefixMatcher(pattern, case_sensitive)
    elif match_type == "suffix":
        matcher = SuffixMatcher(pattern, case_sensitive)
    elif match_type == "contains":
        matcher = ContainsMatcher(pattern, case_sensitive)
    elif match_type == "regex":
        matcher = RegexMatcher(pattern, case_sensitive)

    # Show difficulty estimate
    console.print("\n[bold cyan]Difficulty Estimate[/bold cyan]")
    try:
        calc = DifficultyCalculator("base58")
        pattern_config = PatternConfig(
            pattern=pattern,
            match_type=PatternMatchType[match.upper()],
            case_sensitive=case_sensitive
        )
        difficulty = calc.calculate(pattern_config)

        # Benchmark generator
        console.print("[dim]Benchmarking generator...[/dim]")
        keys_per_sec = generator.benchmark(iterations=100)

        est_time = difficulty.estimated_time(keys_per_sec)

        table = Table(box=box.SIMPLE)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="yellow")

        table.add_row("Pattern", pattern)
        table.add_row("Match Type", match_type)
        table.add_row("Case Sensitive", str(case_sensitive))
        table.add_row("Average Attempts", f"{difficulty.average_attempts:,}")
        table.add_row("Difficulty", difficulty.difficulty_rating.upper())
        table.add_row("Est. Time", str(est_time))
        table.add_row("Generator Rate", f"{keys_per_sec:,.0f} keys/sec")

        console.print(table)
        console.print()

        # Warn if very difficult
        if difficulty.difficulty_rating in ["hard", "extreme"]:
            console.print(
                Panel(
                    f"⚠️  This pattern is [bold red]{difficulty.difficulty_rating}[/bold red] to find!\n"
                    f"Expected time: [yellow]{est_time}[/yellow]\n"
                    "Consider using fewer characters or more workers.",
                    title="Warning",
                    border_style="red"
                )
            )
            console.print()

    except Exception as e:
        console.print(f"[yellow]Could not estimate difficulty: {e}[/yellow]\n")

    # Confirm start
    if not click.confirm("Start generation?", default=True):
        console.print("[red]Cancelled[/red]")
        sys.exit(0)

    console.print("\n[bold green]Generating...[/bold green]\n")

    # Create engine and config
    engine = VanityEngine(generator, matcher)

    config = GenerationConfig(
        key_type=generator.key_type,
        pattern_config=pattern_config,
        num_workers=workers,
        max_attempts=max_attempts,
        timeout_seconds=timeout
    )

    # Generate!
    try:
        keypair, metrics = engine.generate(config, verbose=True)

        console.print("\n\n[bold green]✅ Success![/bold green]\n")

        # Display results
        result_table = Table(box=box.ROUNDED)
        result_table.add_column("Metric", style="cyan")
        result_table.add_column("Value", style="green")

        result_table.add_row("Address/DID", keypair.address)
        result_table.add_row("Attempts", f"{metrics.attempts:,}")
        result_table.add_row("Time", f"{metrics.elapsed_seconds:.2f}s")
        result_table.add_row("Rate", metrics.formatted_rate)
        result_table.add_row("Workers", str(metrics.workers_used))

        console.print(result_table)
        console.print()

        # Export key
        exported = generator.export(keypair, export_format)

        if output:
            # Save to file
            with open(output, 'w') as f:
                f.write(exported)
            console.print(f"[green]✅ Key saved to: {output}[/green]")
        else:
            # Print to stdout
            console.print("\n[bold cyan]Generated Key:[/bold cyan]\n")
            console.print(Panel(exported, border_style="cyan"))

        # Security reminder
        console.print()
        console.print(
            Panel(
                "🔒 [bold red]SECURITY REMINDER[/bold red]\n\n"
                "• This private key was generated on your local machine\n"
                "• Never share your private key with anyone\n"
                "• Never use online vanity generation services\n"
                "• Store private keys securely (encrypted storage recommended)",
                title="Security",
                border_style="red"
            )
        )

    except TimeoutError:
        console.print(f"\n[red]❌ Timeout exceeded after {timeout}s[/red]")
        sys.exit(1)
    except RuntimeError as e:
        console.print(f"\n[red]❌ {e}[/red]")
        sys.exit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️  Generation cancelled by user[/yellow]")
        sys.exit(130)


@cli.command()
@click.argument("pattern")
@click.option(
    "--match",
    type=click.Choice(["prefix", "suffix", "contains", "regex"], case_sensitive=False),
    default="prefix",
    help="Pattern matching mode"
)
@click.option(
    "--alphabet",
    default="base58",
    help="Alphabet for difficulty calculation (base58, hex, base64, custom:N)"
)
def estimate(pattern: str, match: str, alphabet: str):
    """
    Estimate difficulty for finding PATTERN.

    Shows expected attempts, time estimates, and difficulty rating.
    """
    console.print("\n[bold cyan]VaniKeys Difficulty Estimation[/bold cyan]\n")

    # Create calculator
    calc = DifficultyCalculator(alphabet)

    # Create pattern config
    pattern_config = PatternConfig(
        pattern=pattern,
        match_type=PatternMatchType[match.upper()],
        case_sensitive=True
    )

    # Calculate difficulty
    difficulty = calc.calculate(pattern_config)

    # Benchmark rates (typical values)
    ed25519_rate = 300_000  # keys/sec on CPU
    gpu_rate = 50_000_000   # keys/sec on GPU (secp256k1)

    # Create results table
    table = Table(title=f"Pattern: '{pattern}'", box=box.ROUNDED)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="yellow")

    table.add_row("Match Type", match)
    table.add_row("Alphabet Size", str(calc.alphabet_size))
    table.add_row("Average Attempts", f"{difficulty.average_attempts:,}")
    table.add_row("Keyspace Size", f"{difficulty.keyspace_size:,}")
    table.add_row("Difficulty Rating", difficulty.difficulty_rating.upper())

    console.print(table)
    console.print()

    # Time estimates
    time_table = Table(title="Estimated Time", box=box.ROUNDED)
    time_table.add_column("Hardware", style="cyan")
    time_table.add_column("Rate", style="white")
    time_table.add_column("Time", style="yellow")

    ed25519_time = difficulty.estimated_time(ed25519_rate)
    gpu_time = difficulty.estimated_time(gpu_rate)

    time_table.add_row(
        "Ed25519 (CPU)",
        f"{ed25519_rate:,} keys/sec",
        str(ed25519_time)
    )
    time_table.add_row(
        "secp256k1 (GPU)",
        f"{gpu_rate:,} keys/sec",
        str(gpu_time)
    )

    console.print(time_table)


@cli.command()
def table():
    """Show difficulty reference table for various pattern lengths."""
    console.print("\n[bold cyan]VaniKeys Difficulty Reference Table[/bold cyan]\n")
    console.print(format_difficulty_table())
    console.print()


@cli.command()
def info():
    """Show information about VaniKeys and supported key types."""
    console.print("\n[bold cyan]VaniKeys - Vanity Key Generation[/bold cyan]\n")

    console.print(
        "Generate cryptographic keys with custom patterns in public key hashes.\n"
    )

    # Supported key types
    key_table = Table(title="Supported Key Types", box=box.ROUNDED)
    key_table.add_column("Type", style="cyan")
    key_table.add_column("Description", style="white")
    key_table.add_column("Speed", style="yellow")

    key_table.add_row(
        "ed25519",
        "Standard Ed25519 keys (Solana, SSH)",
        "~300K keys/sec (CPU)"
    )
    key_table.add_row(
        "did:key",
        "Decentralized Identifiers using Ed25519",
        "~300K keys/sec (CPU)"
    )

    console.print(key_table)
    console.print()

    # Pattern matching
    pattern_table = Table(title="Pattern Matching Modes", box=box.ROUNDED)
    pattern_table.add_column("Mode", style="cyan")
    pattern_table.add_column("Description", style="white")
    pattern_table.add_column("Example", style="yellow")

    pattern_table.add_row(
        "prefix",
        "Match at start of address",
        "DEAD..."
    )
    pattern_table.add_row(
        "suffix",
        "Match at end of address",
        "...BEEF"
    )
    pattern_table.add_row(
        "contains",
        "Match anywhere in address",
        "...ABC..."
    )
    pattern_table.add_row(
        "regex",
        "Regular expression matching",
        "^[0-9]{4}"
    )

    console.print(pattern_table)
    console.print()

    # Security notice
    console.print(
        Panel(
            "🔒 VaniKeys generates keys locally on your machine.\n"
            "Your private keys never leave your computer.\n"
            "Never use online vanity generation services!",
            title="Security",
            border_style="green"
        )
    )
    console.print()


if __name__ == "__main__":
    cli()
