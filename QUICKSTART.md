# VaniKeys Quickstart Guide

Get started with VaniKeys in 5 minutes.

## Installation

```bash
cd ~/src/projects/vanikeys
pip install -r requirements.txt
```

## Basic Usage

### 1. Generate a Vanity DID

```bash
cd src
python3 -m vanikeys.cli.main generate LAB --type did:key --match contains
```

This will generate a DID like:
```
did:key:z6MkmCzJDpBWLaBwnk3h1...
               ^^^
```

### 2. Check Difficulty First

```bash
python3 -m vanikeys.cli.main estimate DEAD --match prefix
```

Output:
```
Pattern: 'DEAD'
Average Attempts: 11,316,496
Difficulty: MODERATE
Est. Time: 37 seconds @ 300K keys/sec
```

### 3. Use Multiple CPU Cores

```bash
python3 -m vanikeys.cli.main generate ABC \
    --type did:key \
    --match contains \
    --workers 4
```

### 4. Save to File

```bash
python3 -m vanikeys.cli.main generate MYCOMPANY \
    --type did:key \
    --match contains \
    --output my-vanity-key.pem
```

## Programmatic Usage

```python
from vanikeys.generators.ed25519 import Ed25519DIDGenerator
from vanikeys.matchers.simple import ContainsMatcher
from vanikeys.core.engine import VanityEngine

# Setup
generator = Ed25519DIDGenerator()
matcher = ContainsMatcher("LAB", case_sensitive=False)
engine = VanityEngine(generator, matcher)

# Generate!
keypair, metrics = engine.generate()

print(f"Found: {keypair.address}")
print(f"Attempts: {metrics.attempts:,}")
print(f"Rate: {metrics.formatted_rate}")
```

## CLI Commands

### `info` - Show supported features
```bash
python3 -m vanikeys.cli.main info
```

### `table` - Show difficulty reference table
```bash
python3 -m vanikeys.cli.main table
```

Output:
```
Vanity Pattern Difficulty (Base58 Prefix)
======================================================================
Length   Attempts         @ 300K/s        @ 50M/s (GPU)
----------------------------------------------------------------------
1        58               0:00:00         0:00:00
2        3,364            0:00:00.011213  0:00:00.000067
3        195,112          0:00:00.650373  0:00:00.003902
4        11,316,496       0:00:37.721653  0:00:00.226329
...
```

### `estimate` - Estimate difficulty
```bash
python3 -m vanikeys.cli.main estimate PATTERN --match <type>
```

### `generate` - Generate vanity key
```bash
python3 -m vanikeys.cli.main generate PATTERN [options]
```

**Options:**
- `--type <ed25519|did:key>` - Key type (default: ed25519)
- `--match <prefix|suffix|contains|regex>` - Match mode (default: contains)
- `--case-sensitive` / `--case-insensitive` - Case sensitivity (default: insensitive)
- `--workers N` - Number of CPU cores to use (default: 1)
- `--max-attempts N` - Stop after N attempts
- `--timeout SECONDS` - Stop after timeout
- `--output FILE` - Save to file
- `--format <pem|json|hex|did|did_document>` - Output format

## Pattern Matching Modes

### Prefix
Pattern must appear at the **start** of the address.
```bash
python3 -m vanikeys.cli.main generate DEAD --match prefix
# Result: DEADbeef123...
```

### Suffix
Pattern must appear at the **end** of the address.
```bash
python3 -m vanikeys.cli.main generate BEEF --match suffix
# Result: ...abc123BEEF
```

### Contains
Pattern can appear **anywhere** in the address (easiest).
```bash
python3 -m vanikeys.cli.main generate LAB --match contains
# Result: ...xyz7LABmnop...
```

### Regex
Use regular expressions for complex patterns.
```bash
python3 -m vanikeys.cli.main generate "^[0-9]{4}" --match regex
# Result: 1234abc...
```

## Performance Tips

1. **Use `contains` instead of `prefix`** - Much faster for same pattern
   - Prefix "DEAD" = 11M attempts
   - Contains "DEAD" = ~200K attempts

2. **Case-insensitive matching** - More results match
   - `--case-insensitive` doubles your chances

3. **Multi-core generation** - Linear speedup
   - `--workers 4` on 4-core CPU = 4x faster

4. **Keep patterns short** - Difficulty grows exponentially
   - 3 chars: instant
   - 4 chars: seconds
   - 5 chars: minutes
   - 6+ chars: hours/days

## Difficulty Guide

| Pattern Length | Prefix Attempts | Contains Attempts | Time (300K/s) |
|----------------|-----------------|-------------------|---------------|
| 2 chars        | 3,364           | 68                | Instant       |
| 3 chars        | 195,112         | 4,064             | <1 sec        |
| 4 chars        | 11,316,496      | 236,178           | 37 sec        |
| 5 chars        | 656,356,768     | 13,702,299        | 36 min        |
| 6 chars        | 38B             | 794B              | 35 hours      |

## Security Best Practices

✅ **DO:**
- Generate keys on your local machine
- Use VaniKeys directly from source
- Store private keys encrypted
- Use hardware wallets for high-value keys

❌ **DON'T:**
- Use online vanity generation services
- Share your private keys
- Trust third parties with key generation
- Store private keys in plaintext

## Examples

See `examples/basic_usage.py` for comprehensive programmatic examples.

## Troubleshooting

### Pattern not found quickly?
- Check difficulty estimate first
- Use shorter pattern or `contains` mode
- Enable `--case-insensitive`
- Add more workers

### Import errors?
```bash
pip install -r requirements.txt
```

### Slow generation?
- Ed25519 is ~300K keys/sec (normal)
- Use `--workers` to parallelize
- Consider shorter patterns

## Next Steps

- Read [ARCHITECTURE.md](docs/ARCHITECTURE.md) for technical details
- Explore [examples/](examples/) for code samples
- Check [README.md](README.md) for roadmap and features
- Add secp256k1 support for Ethereum/Bitcoin
- Implement GPU acceleration (Phase 2)

---

**Quick Reference:**
```bash
# Show help
python3 -m vanikeys.cli.main --help

# Generate vanity DID with "LAB"
python3 -m vanikeys.cli.main generate LAB --type did:key

# Estimate difficulty
python3 -m vanikeys.cli.main estimate PATTERN

# Show difficulty table
python3 -m vanikeys.cli.main table
```
