# VaniKeys Architecture

**Version**: 0.1.0
**Status**: Design Phase
**Last Updated**: 2025-11-17

## System Overview

VaniKeys is a modular vanity cryptographic key generation framework designed for flexibility, performance, and security. The architecture supports multiple key types, pattern matching strategies, and optimization backends.

## Core Design Principles

1. **Separation of Concerns**: Key generation, pattern matching, and output formatting are independent
2. **Pluggable Backends**: Easy to add new key types without modifying core engine
3. **Performance Hierarchy**: Start with Python, optimize hot paths with Rust, add GPU for extreme cases
4. **Security First**: Keys never leave user's machine, clear warnings about key handling
5. **Observable Progress**: Real-time feedback on generation speed, difficulty, and ETA

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        CLI Interface                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   generate   │  │   estimate   │  │   validate   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                     Core Engine                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │         Pattern Matching Coordinator                 │    │
│  │  • Difficulty calculation                           │    │
│  │  • Progress tracking                                │    │
│  │  • Worker pool management                           │    │
│  └─────────────────────────────────────────────────────┘    │
└──────────────────────┬──────────────────┬────────────────────┘
                       │                  │
         ┌─────────────▼─────┐  ┌────────▼─────────┐
         │  Key Generators    │  │  Pattern Matchers │
         │                    │  │                    │
         │  • Ed25519         │  │  • Prefix         │
         │  • secp256k1       │  │  • Suffix         │
         │  • RSA             │  │  • Contains       │
         │  • DID             │  │  • Regex          │
         └────────────────────┘  └───────────────────┘
                       │
         ┌─────────────▼──────────────┐
         │  Performance Backends       │
         │                             │
         │  • Python (baseline)        │
         │  • Rust (hot paths)         │
         │  • GPU (future: CUDA/OpenCL)│
         └─────────────────────────────┘
```

## Module Details

### 1. CLI Interface (`src/cli/`)

**Responsibilities**:
- Parse command-line arguments
- Validate user inputs
- Display progress and results
- Handle output formats (PEM, JSON, etc.)

**Commands**:
```bash
vanikeys generate <type> --pattern <pattern> [options]
vanikeys estimate <type> --pattern <pattern>
vanikeys validate <type> --key <keyfile>
```

**Key Files**:
- `cli/main.py` - Entry point and argument parsing
- `cli/commands/generate.py` - Generation command handler
- `cli/commands/estimate.py` - Difficulty estimation
- `cli/display.py` - Progress bars and formatted output

### 2. Core Engine (`src/core/`)

**Responsibilities**:
- Coordinate key generation and matching
- Manage worker pools (multi-core)
- Track performance metrics
- Calculate difficulty estimates

**Key Classes**:

```python
class VanityEngine:
    """Main coordination engine"""

    def __init__(self, generator: KeyGenerator, matcher: PatternMatcher):
        self.generator = generator
        self.matcher = matcher
        self.workers = []

    def generate(self, pattern: str, num_workers: int = None) -> KeyPair:
        """Generate key matching pattern using worker pool"""
        pass

    def estimate_difficulty(self, pattern: str) -> DifficultyEstimate:
        """Calculate expected attempts and time"""
        pass

class DifficultyEstimate:
    """Encapsulates difficulty metrics"""
    average_attempts: int
    estimated_time: timedelta
    keyspace_size: int
    confidence_interval: tuple[int, int]
```

**Key Files**:
- `core/engine.py` - Main coordination engine
- `core/worker.py` - Worker thread/process implementation
- `core/difficulty.py` - Difficulty calculation
- `core/metrics.py` - Performance tracking

### 3. Key Generators (`src/generators/`)

**Responsibilities**:
- Generate cryptographic key pairs
- Extract public key representation (address, DID, hash, etc.)
- Support multiple encoding formats

**Interface**:

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class KeyPair:
    private_key: bytes
    public_key: bytes
    address: str  # Human-readable representation
    metadata: dict  # Algorithm-specific info

class KeyGenerator(ABC):
    """Base class for all key generators"""

    @abstractmethod
    def generate(self) -> KeyPair:
        """Generate a new key pair"""
        pass

    @abstractmethod
    def get_searchable_string(self, keypair: KeyPair) -> str:
        """Extract the string to pattern match against"""
        pass

    @abstractmethod
    def export(self, keypair: KeyPair, format: str) -> str:
        """Export key in specified format (PEM, JSON, etc.)"""
        pass

    @property
    @abstractmethod
    def keys_per_second(self) -> float:
        """Benchmark generation rate"""
        pass
```

**Implementations**:

#### Ed25519Generator (`generators/ed25519.py`)
```python
class Ed25519Generator(KeyGenerator):
    """Ed25519 key generation (Solana, DIDs)"""

    def generate(self) -> KeyPair:
        private = Ed25519PrivateKey.generate()
        public = private.public_key()
        # Extract bytes and encode

    def get_searchable_string(self, keypair: KeyPair) -> str:
        # Return base58-encoded public key or DID string

    # ~300K keys/sec on CPU (no offset optimization possible)
```

#### Secp256k1Generator (`generators/secp256k1.py`)
```python
class Secp256k1Generator(KeyGenerator):
    """secp256k1 for Bitcoin/Ethereum"""

    def generate(self) -> KeyPair:
        # Standard secp256k1 generation

    def generate_incremental(self, start_key: bytes, offset: int) -> KeyPair:
        # Optimized: compute start + offset*G
        # Enables massive GPU parallelization

    # ~50M keys/sec on GPU, 5M on laptop GPU
```

#### DIDGenerator (`generators/did.py`)
```python
class DIDGenerator(KeyGenerator):
    """Wrapper for DID-specific vanity generation"""

    def __init__(self, method: str = "key", curve: str = "ed25519"):
        # Support did:key, did:web, etc.

    def get_searchable_string(self, keypair: KeyPair) -> str:
        # Return full DID string: did:key:z6Mk...
```

### 4. Pattern Matchers (`src/matchers/`)

**Responsibilities**:
- Define pattern matching logic
- Calculate search space size
- Support case sensitivity options

**Interface**:

```python
class PatternMatcher(ABC):
    """Base class for pattern matching"""

    @abstractmethod
    def matches(self, candidate: str, pattern: str) -> bool:
        """Check if candidate matches pattern"""
        pass

    @abstractmethod
    def calculate_difficulty(self, pattern: str, alphabet_size: int) -> int:
        """Calculate expected number of attempts"""
        pass

class PrefixMatcher(PatternMatcher):
    """Match pattern at start of string"""
    def calculate_difficulty(self, pattern: str, alphabet_size: int) -> int:
        return alphabet_size ** len(pattern)

class ContainsMatcher(PatternMatcher):
    """Match pattern anywhere in string"""
    def calculate_difficulty(self, pattern: str, alphabet_size: int) -> int:
        # More complex: depends on string length
        # Approximation: alphabet_size ** (len(pattern) - 1)

class RegexMatcher(PatternMatcher):
    """Match using regular expression"""
    def calculate_difficulty(self, pattern: str, alphabet_size: int) -> int:
        # Very approximate: analyze regex complexity
```

### 5. Performance Backends (`src/performance/`)

**Responsibilities**:
- Provide optimized implementations
- GPU acceleration (future)
- Benchmarking utilities

**Strategy**:

1. **Phase 1: Python baseline**
   - Pure Python with `multiprocessing`
   - Easy to develop and debug
   - Sufficient for moderate difficulty patterns

2. **Phase 2: Rust optimization**
   - Rewrite hot paths in Rust
   - Expose via PyO3 bindings
   - 10-100x speedup for CPU-bound operations

3. **Phase 3: GPU acceleration**
   - CUDA/OpenCL implementations
   - Only for secp256k1 (offset method)
   - 1000x+ speedup for extreme vanity

## Data Flow

### Generation Flow

```
1. User invokes CLI
   ↓
2. CLI validates inputs and creates VanityEngine
   ↓
3. Engine calculates difficulty estimate
   ↓
4. Engine spawns worker pool
   ↓
5. Each worker:
   a. Generate key pair
   b. Extract searchable string
   c. Check pattern match
   d. If match → return key, else repeat
   ↓
6. First worker to find match signals others to stop
   ↓
7. Engine returns matched key to CLI
   ↓
8. CLI exports key in requested format
```

### Estimation Flow

```
1. User requests difficulty estimate
   ↓
2. CLI creates matcher and generator
   ↓
3. Matcher calculates search space size
   ↓
4. Generator provides keys/sec benchmark
   ↓
5. Calculate: time = search_space / keys_per_sec
   ↓
6. Display estimate with confidence interval
```

## Configuration

### Config File (`~/.vanikeys/config.yaml`)

```yaml
performance:
  workers: auto  # or integer
  backend: python  # python, rust, gpu

output:
  default_format: pem
  save_directory: ~/.vanikeys/keys

security:
  warn_online: true
  require_offline: false

benchmarks:
  ed25519_keys_per_sec: 300000
  secp256k1_keys_per_sec: 5000000
```

## Security Considerations

1. **Key Generation**:
   - Use cryptographically secure RNG
   - Never compromise key entropy
   - Vanity process doesn't weaken keys

2. **Key Storage**:
   - Never write private keys to disk by default
   - If saving, use encrypted storage
   - Clear memory after use

3. **Third-Party Generation**:
   - Support split-key vanity (future)
   - Third party generates partial key
   - User combines with own secret
   - Third party never sees final private key

4. **Warnings**:
   - Prominent notice about never using online services
   - Explain why offline generation is critical
   - Recommend hardware verification

## Performance Targets

### Phase 1 (Python)
- Ed25519: 300K keys/sec (single core), 2M keys/sec (8 cores)
- secp256k1: 50K keys/sec (single core), 400K keys/sec (8 cores)

### Phase 2 (Rust)
- Ed25519: 2M keys/sec (single core), 16M keys/sec (8 cores)
- secp256k1: 500K keys/sec (single core), 4M keys/sec (8 cores)

### Phase 3 (GPU)
- secp256k1: 50M+ keys/sec (consumer GPU)
- Ed25519: Limited improvement (SHA512 bottleneck)

## Difficulty Examples

**Base58 alphabet (58 characters):**

| Pattern Length | Prefix Difficulty | Avg Time (300K/s) | Avg Time (50M/s GPU) |
|----------------|-------------------|-------------------|----------------------|
| 3 chars        | 195K              | 0.6 sec           | 4 ms                 |
| 4 chars        | 11M               | 37 sec            | 220 ms               |
| 5 chars        | 656M              | 36 min            | 13 sec               |
| 6 chars        | 38B               | 35 hours          | 12 min               |
| 7 chars        | 2.2T              | 85 days           | 12 hours             |

**Implications**:
- 3-4 chars: Easy, instant on any hardware
- 5-6 chars: Reasonable with multi-core or GPU
- 7+ chars: GPU essential, or wait days/weeks

## Testing Strategy

1. **Unit Tests**:
   - Each generator produces valid keys
   - Each matcher correctly identifies patterns
   - Difficulty calculations are accurate

2. **Integration Tests**:
   - End-to-end generation flow
   - Multi-worker coordination
   - Output format validation

3. **Performance Tests**:
   - Benchmark each generator
   - Verify linear scaling with workers
   - Measure memory usage

4. **Security Tests**:
   - Key entropy verification
   - No key reuse across runs
   - Private key zeroization

## Future Enhancements

1. **Split-Key Vanity**:
   - Allow safe third-party generation
   - User provides public commitment
   - Third party finds vanity offset
   - User combines to get final key

2. **Web UI**:
   - Browser-based generation (keys never leave browser)
   - WebAssembly for performance
   - Visual difficulty estimator

3. **Hardware Wallet Integration**:
   - Generate seed phrases with vanity addresses
   - Support for BIP32/BIP44 derivation paths

4. **Distributed Generation**:
   - Split search space across multiple machines
   - Coordination server (doesn't see keys)
   - Useful for extreme vanity (10+ chars)

## References

- [Ed25519 for DIDs](https://w3c-ccg.github.io/did-method-key/)
- [secp256k1 Specification](https://www.secg.org/sec2-v2.pdf)
- [Vanitygen Source](https://github.com/samr7/vanitygen) - Reference implementation
- [Split-key Vanity](https://en.bitcoin.it/wiki/Split-key_vanity_address) - Bitcoin Wiki

---

**Document Status**: Living document, updated as implementation progresses
**Next Review**: After Phase 1 implementation complete
