# VaniKeys - Claude Development Guide

## Project Overview

**VaniKeys** is a cryptographic vanity address generator with gamification features. It generates key pairs with customized patterns in public key hashes/addresses (e.g., `did:key:z6MkLAB42...` or `0xDEADBEEF...`).

**Core Innovation**: Three-pronged approach
1. **Consumer**: Gamified "gacha" style vanity key generation
2. **Enterprise**: Organizational key management with embedded metadata patterns
3. **Marketplace**: Pre-generated premium pattern sales

**Repository**: https://github.com/scottsen/vanikeys
**Branch**: `claude/update-claude-md-01QqGDyrCZzch9iEQcFvvDZC`

## Implementation Status

### ✅ Phase 1: Foundation (Complete)
- Ed25519 key generation with DID support
- Pattern matching: prefix, suffix, contains, regex
- Multi-worker CPU parallelization
- CLI with difficulty estimation and benchmarking
- Rich terminal UI with progress tracking

### 🚧 Phase 2: Gamification (In Progress)
- Multi-substring matching with fuzzy matching (0→O, 1→I, 3→E)
- VaniPull engine (gacha + guaranteed modes)
- Token economy backend (PostgreSQL)
- Web UI with slot-machine style animations
- Payment integration (Stripe)

**See**: `docs/PHASE2_IMPLEMENTATION_PLAN.md` for 6-week roadmap

## Architecture

```
src/vanikeys/
├── cli/              # Click-based CLI interface
│   └── main.py       # Commands: generate, estimate, table, info
├── core/             # Core engine logic
│   ├── engine.py     # VanityEngine: single/multi-threaded generation
│   ├── difficulty.py # Difficulty calculation & estimation
│   └── types.py      # Pydantic models (KeyPair, PatternConfig, etc.)
├── generators/       # Key generation backends
│   ├── base.py       # KeyGenerator abstract base
│   └── ed25519.py    # Ed25519 + Ed25519DIDGenerator
└── matchers/         # Pattern matching strategies
    ├── base.py       # PatternMatcher abstract base
    └── simple.py     # Prefix, Suffix, Contains, Regex matchers
```

## Key Technical Concepts

### Vanity Generation Approach
1. Generate cryptographic key pair
2. Compute public key hash/address
3. Check if searchable string matches pattern
4. Repeat until match found

**Performance**: ~300K keys/sec (Ed25519 CPU), ~50M keys/sec (secp256k1 GPU)

### Pattern Matching
- **Prefix**: Pattern at start (e.g., `DEAD...`)
- **Suffix**: Pattern at end (e.g., `...BEEF`)
- **Contains**: Pattern anywhere (e.g., `...ABC...`)
- **Regex**: Full regex matching (e.g., `^[0-9]{4}`)
- **Multi-substring** (Phase 2): Sequential patterns with gaps (e.g., `GO BE AWE SOME`)

### Difficulty Calculation
- Base58 alphabet (58 chars) for DIDs
- Hex alphabet (16 chars) for Ethereum
- Formula: `58^n` attempts average for n-character pattern
- Ratings: trivial → easy → moderate → hard → extreme

## Development Workflow

### Setup
```bash
# Install in editable mode
pip install -e .

# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Lint
ruff check src/
black src/
mypy src/
```

### Testing the CLI
```bash
# Generate DID with "ABC" pattern
vanikeys generate ABC --type did:key --case-insensitive

# Estimate difficulty
vanikeys estimate DEADBEEF --match prefix

# Show difficulty reference table
vanikeys table

# Show info
vanikeys info
```

### Adding New Key Types
1. Create generator in `src/vanikeys/generators/`
2. Inherit from `KeyGenerator` base class
3. Implement: `generate()`, `get_searchable_string()`, `export()`
4. Add to CLI in `src/vanikeys/cli/main.py`

### Adding New Pattern Matchers
1. Create matcher in `src/vanikeys/matchers/`
2. Inherit from `PatternMatcher` base class
3. Implement: `matches(text: str) -> bool`
4. Add to CLI options

## Important Files

### Core Implementation
- `src/vanikeys/core/engine.py` - Main generation engine (225 lines)
- `src/vanikeys/cli/main.py` - CLI commands (400 lines)
- `src/vanikeys/generators/ed25519.py` - Ed25519 key generation

### Documentation (310KB total)
- `README.md` - Project overview, roadmap, business model
- `QUICKSTART.md` - Getting started guide
- `docs/ARCHITECTURE.md` - Technical design (680 lines)
- `docs/DEPLOYMENT_PLAN.md` - Production deployment (1,122 lines)
- `docs/GAMIFICATION_DESIGN.md` - Gamification mechanics (12,500 words)
- `docs/PHASE2_IMPLEMENTATION_PLAN.md` - 6-week implementation plan

### Strategic Expansions
- `docs/ORGANIZATIONAL_KEY_MANAGEMENT.md` - Enterprise use cases
- `docs/VANIKEYS_DIRECTORY_SERVICE.md` - Registry/directory system
- `docs/PATTERN_MARKETPLACE_DESIGN.md` - Pattern marketplace design

### Infrastructure
- `docs/COMPUTE_OPTIONS_COMPARISON.md` - GPU compute options
- `docs/SERVERLESS_GPU_OPTIONS.md` - RunPod, Modal, AWS Batch
- `docs/DIGITALOCEAN_GPU_DEPLOYMENT.md` - DigitalOcean deployment

## Coding Standards

### Python Style
- **Python**: 3.10+ (type hints required)
- **Formatter**: Black (line length: 100)
- **Linter**: Ruff
- **Type checker**: mypy (strict mode)
- **Testing**: pytest with coverage

### Key Libraries
- `cryptography` - Ed25519, RSA crypto
- `click` - CLI framework
- `rich` - Terminal UI (tables, panels, progress)
- `pydantic` - Data validation and serialization

### Security Principles
- **Offline-only generation** - Keys never leave user's machine
- **No online services** - Warn against third-party vanity services
- **Clear security reminders** - Display warnings about private key handling
- **Split-key support** (future) - Safe third-party computation

## Multi-Worker Parallelization

The engine supports CPU parallelization via multiprocessing:
- Workers run in separate processes
- First worker to find match signals others to stop
- Progress aggregated from all workers
- Configurable via `--workers N` flag

**Implementation**: `src/vanikeys/core/engine.py:_generate_multi_threaded()`

## Testing Strategy

```bash
# Run all tests with coverage
pytest

# Run specific test file
pytest tests/test_engine.py

# Run with verbose output
pytest -v

# Generate coverage report
pytest --cov=vanikeys --cov-report=html
```

## Business Context

**Original Vision**: Consumer gacha gamification ($600K-$3.6M Year 1)
**Strategic Expansion**: Enterprise + Marketplace ($28M-$31M Year 1)

### Revenue Streams
1. **Consumer**: Pattern purchases $10-$500, VaniTokens for gacha pulls
2. **Enterprise**: Pattern reservations $50K-$500K, private registries $10K-$100K/year
3. **Marketplace**: Pre-generated premium patterns, secondary market (10% fees)

### Target Markets
- **DIDs**: Universities, research labs, enterprises (self-describing keys)
- **Blockchain**: Ethereum/Bitcoin branded addresses
- **SSH/TLS**: Recognizable fingerprints for auth/certs

## Common Tasks

### Generate a vanity DID locally
```bash
vanikeys generate LAB --type did:key --workers 4
```

### Benchmark generator performance
```python
from vanikeys.generators.ed25519 import Ed25519DIDGenerator

generator = Ed25519DIDGenerator()
keys_per_sec = generator.benchmark(iterations=1000)
print(f"Rate: {keys_per_sec:,.0f} keys/sec")
```

### Calculate difficulty for pattern
```python
from vanikeys.core.difficulty import DifficultyCalculator
from vanikeys.core.types import PatternConfig, PatternMatchType

calc = DifficultyCalculator("base58")
config = PatternConfig(
    pattern="DEADBEEF",
    match_type=PatternMatchType.PREFIX,
    case_sensitive=False
)
difficulty = calc.calculate(config)
print(f"Average attempts: {difficulty.average_attempts:,}")
print(f"Difficulty: {difficulty.difficulty_rating}")
```

## Git Workflow

**Current Branch**: `claude/update-claude-md-01QqGDyrCZzch9iEQcFvvDZC`

```bash
# Always push to the claude/ branch
git add .
git commit -m "feat: descriptive commit message"
git push -u origin claude/update-claude-md-01QqGDyrCZzch9iEQcFvvDZC

# If push fails with network error, retry with exponential backoff (2s, 4s, 8s, 16s)
```

## Quick Reference

| Command | Purpose |
|---------|---------|
| `vanikeys generate PATTERN` | Generate vanity key |
| `vanikeys estimate PATTERN` | Calculate difficulty |
| `vanikeys table` | Show difficulty reference |
| `vanikeys info` | Show key types and patterns |
| `pytest` | Run test suite |
| `ruff check src/` | Lint code |
| `black src/` | Format code |

---

**Last Updated**: 2025-11-21
**Phase**: 2 (Gamification in progress)
**Status**: Active development
