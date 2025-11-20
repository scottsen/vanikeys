# VaniKeys

> 🎰 Crypto slot machine meets vanity key generation - Pull for your perfect key!

**Status:** Active Development (Genesis: 2025-11-17)
**Current Phase:** Gamification Design
**Sessions:** descending-star-1117, fecuwo-1117

## Overview

VaniKeys generates cryptographic key pairs with customized public key patterns. Instead of random addresses like `did:key:z6MkrXYz...`, generate recognizable identifiers like `did:key:z6MkLAB42...` or Ethereum addresses like `0xDEADBEEF...`.

**Now with gamification**: Buy VaniTokens, pull for patterns like a slot machine, and see if you hit the jackpot!

## 🎰 The Gamification Approach

**Traditional vanity generation** (boring): Wait 3 minutes for your key.

**VaniKeys** (exciting): Each pull costs tokens, shows odds, and reveals what you got - even partial matches!

### Key Features

**🎲 VaniPull System**
- Buy VaniTokens for pulls (like gacha games)
- Each pull = instant key generation + pattern matching
- Visible odds ("1 in 4.2 billion!")
- Dramatic reveal animations

**🎯 Multi-Substring Matching**
- Want "GO BE AWE SOME"? We'll find: `did:key:z3468-GO-BE-5643-AWE-3596-SOME-2566`
- Fuzzy matching: 0→O, 1→I, 3→E (configurable)
- Sequential patterns with any characters between
- **"Kind of what you wanted?"** - Shows ALL matches found, even partial

**💰 Two Payment Models**
1. **Gacha Mode**: Gamble! 100 tokens/pull, no guarantee, might get lucky
2. **Guaranteed Mode**: Pay 15% premium over raw odds, guaranteed exact match

**Example:**
```
You want: "GO BE AWE SOME"
Pull #1: did:key:z6Mk3468-GO-5643-MISS-3596-MISS-2566
         ✅ GO (1/4) - 25% match

Pull #2: did:key:z6Mk8765-GO-1234-BE-9876-MISS-3456
         ✅ GO, ✅ BE (2/4) - 50% match

Pull #3: did:key:z6Mk3468-GO-5643-BE-7890-AWE-1234-SOME
         ✨ JACKPOT! All 4 substrings matched! ✨
```

**📊 Complete Transparency**
- See exact probabilities for your pattern
- Understand token costs upfront
- Track your pull history
- Fair odds (provably fair, open source)

**See [`docs/GAMIFICATION_DESIGN.md`](docs/GAMIFICATION_DESIGN.md) for the complete design.**

## The Problem

Cryptographic keys are randomly generated, resulting in meaningless character sequences. This makes it difficult to:
- Identify which organization/lab generated a key
- Recognize legitimate addresses at a glance
- Embed metadata in public identifiers
- Create memorable or branded addresses

## The Solution

**Vanity key generation** through controlled brute-force:
1. Generate key pair
2. Check if public key hash contains desired pattern
3. If no match, repeat until found

While computationally intensive, modern hardware (especially GPUs) can generate millions of keys per second, making even complex patterns achievable.

## Research Findings

### Performance Benchmarks
- **secp256k1 (Bitcoin/Ethereum)**: ~50M keys/sec on GPU, ~5M on laptop GPU
- **Ed25519 (Solana/DIDs)**: ~0.3M keys/sec on M1 CPU (requires full regeneration)
- **Difficulty**: For n-character pattern in base58: `58^n` attempts average

### Key Algorithm Differences

#### secp256k1 (Optimizable)
- Can use incremental offset method
- Draw random private key `u`, compute public key `P`
- Next key: `u+1` → `P+G` (just one EC point addition)
- **Result**: Extremely fast GPU parallelization

#### Ed25519 (Not Optimizable)
- Public key = `H(private_key)[0:32] * G` where `H` is SHA512
- SHA512 is irreversible → must generate full new key each attempt
- **Result**: 100x slower than secp256k1, but still feasible

### Security Considerations
- Vanity generation does NOT weaken key security (same entropy)
- Never use online services (private key exposure risk)
- Split-key vanity allows safe third-party computation
- Generate offline on trusted hardware

## Use Cases

### 1. **DIDs with Embedded Identifiers** (Novel/Unexplored!)
```
did:key:z6MkLAB42...  → Lab 42 generated this
did:key:z6MkACME...   → ACME Corporation identity
did:key:z6MkDEV...    → Development environment key
```

### 2. **Branded Wallet Addresses**
```
0xDEADBEEF...         → Memorable Ethereum address
1ALICE...             → Personalized Bitcoin address
```

### 3. **Recognizable SSH Keys**
```
ED25519 key fingerprint contains "LAB"
→ Easy visual verification in authorized_keys
```

### 4. **Certificate Fingerprints**
```
X.509 cert with fingerprint containing organization code
→ Quick validation without full cert inspection
```

## Architecture (Planned)

```
vanikeys/
├── src/
│   ├── core/           # Core pattern matching engine
│   ├── generators/     # Key type implementations
│   │   ├── ed25519.py
│   │   ├── secp256k1.py
│   │   ├── rsa.py
│   │   └── did.py
│   ├── matchers/       # Pattern matching strategies
│   │   ├── prefix.py
│   │   ├── suffix.py
│   │   ├── contains.py
│   │   └── regex.py
│   ├── performance/    # Optimization & GPU support
│   └── cli/            # Command-line interface
├── docs/
│   ├── ARCHITECTURE.md           # Technical design (680 lines)
│   ├── DEPLOYMENT_PLAN.md        # Production deployment (1,122 lines)
│   ├── GAMIFICATION_DESIGN.md    # Gamification mechanics (NEW!)
│   ├── PERFORMANCE.md
│   └── SECURITY.md
├── examples/
│   ├── bitcoin_vanity.py
│   ├── did_vanity.py
│   └── ssh_vanity.py
└── tests/
```

## Design Principles

1. **Pluggable Backends**: Easy to add new key types
2. **Pattern Flexibility**: Support prefix, suffix, contains, regex
3. **Performance First**: Leverage GPU when available, multi-core CPU fallback
4. **Security Conscious**: Offline-only, clear warnings about key handling
5. **Progress Transparency**: Show difficulty estimates, time remaining, keys/sec
6. **Split-Key Support**: Safe third-party vanity generation (future)

## Example Usage (Planned)

```bash
# Generate DID with "LAB" pattern
vanikeys generate did:key --contains LAB --case-insensitive

# Ethereum address starting with 0xDEAD
vanikeys generate ethereum --prefix DEAD

# Ed25519 SSH key with pattern in fingerprint
vanikeys generate ed25519-ssh --contains 42

# Estimate difficulty
vanikeys estimate --type ethereum --prefix DEADBEEF
# → ~4.2 billion attempts (84 seconds @ 50M keys/sec)
```

## Technology Stack

**Language**: Python (prototyping) → Rust (performance critical paths)
**GPU**: OpenCL/CUDA support via external libraries
**Crypto Libraries**:
- `cryptography` (Ed25519, RSA)
- `eth-keys` (secp256k1/Ethereum)
- `multiformats` (DIDs, multibase, multicodec)

## Competitive Landscape

**Existing Tools**:
- `vanitygen` / `vanitygen-plusplus`: Bitcoin/Ethereum, C++
- `vanity-eth-gpu`: Ethereum GPU generation
- `solana-keygen grind`: Solana CLI vanity

**VaniKeys Differentiation**:
✅ **First DID-focused vanity generator**
✅ **Gamified experience** - Turn key generation into fun, addictive pulls
✅ **Multi-substring matching** - "GO BE AWE SOME" with fuzzy matching
✅ **Dual payment models** - Gamble (gacha) or guarantee (utility)
✅ **Complete transparency** - Visible odds, fair pricing, open source
✅ Unified interface for multiple key types
✅ Modern Python API + Rust performance
✅ Comprehensive pattern matching (prefix/suffix/contains/regex/multi-substring)

## Roadmap

### Phase 1: Foundation ✅ COMPLETE
- [x] Project setup and architecture
- [x] Ed25519 key generation (Python)
- [x] Basic pattern matching (prefix/contains/suffix/regex)
- [x] CLI interface with difficulty estimation
- [x] DID vanity generation
- [x] Comprehensive documentation (~2,800 lines)
- [x] Production deployment plan

### Phase 2: Gamification (Current - Week 1-6)
**Week 1-2: Core Mechanics**
- [ ] Multi-substring matcher with fuzzy matching (0→O, 1→I, etc)
- [ ] Probability calculator for complex patterns
- [ ] VaniPull engine (gacha + guaranteed modes)
- [ ] Token economy backend (PostgreSQL)
- [ ] User accounts and authentication

**Week 3-4: Frontend UI**
- [ ] Pattern submission form with odds display
- [ ] Pull animation (slot machine style)
- [ ] "What You Got" results display
- [ ] Token purchase flow (Stripe)
- [ ] Pull history and analytics

**Week 5-6: Polish & Launch**
- [ ] Sound effects and animations
- [ ] Free daily pulls system
- [ ] Social sharing features
- [ ] Load testing and security audit
- [ ] Production launch 🚀

### Phase 3: Performance & Features (Month 2-3)
- [ ] Multi-core CPU parallelization
- [ ] secp256k1 support (Bitcoin/Ethereum)
- [ ] Split-key vanity generation
- [ ] Leaderboards and achievements
- [ ] Referral system
- [ ] Bulk pulls (10x, 100x)

### Phase 4: Scale (Month 4-6)
- [ ] Rust implementation for hot paths
- [ ] GPU support investigation
- [ ] Mobile app (iOS/Android)
- [ ] API for third-party integrations
- [ ] White-label enterprise offering

## Documentation

### Core Documentation

- **[README.md](README.md)** - This file, project overview
- **[CHANGELOG.md](CHANGELOG.md)** - Project evolution history (Phase 1 → Strategic Expansion)
- **[QUICKSTART.md](QUICKSTART.md)** - Getting started guide (280 lines)
- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - Technical design (680 lines)
- **[DEPLOYMENT_PLAN.md](docs/DEPLOYMENT_PLAN.md)** - Production deployment (1,122 lines)
- **[GAMIFICATION_DESIGN.md](docs/GAMIFICATION_DESIGN.md)** - Gamification mechanics (12,500 words)
- **[PHASE2_IMPLEMENTATION_PLAN.md](docs/PHASE2_IMPLEMENTATION_PLAN.md)** - 6-week implementation roadmap
- **[CHANGELIST.md](docs/CHANGELIST.md)** - Complete file changelist for Phase 2

### Compute Infrastructure Documentation

- **[COMPUTE_OPTIONS_COMPARISON.md](docs/COMPUTE_OPTIONS_COMPARISON.md)** ⭐ Quick comparison of all compute options
- **[SERVERLESS_GPU_OPTIONS.md](docs/SERVERLESS_GPU_OPTIONS.md)** - RunPod, Modal, AWS Batch (RECOMMENDED for MVP)
- **[DIGITALOCEAN_GPU_DEPLOYMENT.md](docs/DIGITALOCEAN_GPU_DEPLOYMENT.md)** - DigitalOcean GPU/CPU droplets (for scale)
- **[LLM_INTEGRATION_GUIDE.md](docs/LLM_INTEGRATION_GUIDE.md)** - AI features using open-source LLMs (Together.ai, Hugging Face)

### Quick Links

```bash
# View project in TIA
tia project show vanikeys

# Search VaniKeys-related work
tia search all "vanikeys"

# Explore topics
tia beth explore "vanity-keys"
tia beth explore "gamification"
```

---

## 🚀 Strategic Expansions (2025-11-17)

**VaniKeys has evolved from "consumer vanity keys" into THREE major business opportunities:**

### 1. 🏢 Organizational Key Management

**The Insight**: Embedded patterns aren't just "vanity" - they're **functional metadata** that makes keys self-describing.

**Enterprise Use Cases:**
- **Universities**: DIDs with embedded institution-year-student ID → `STANFORD-2025-042`
- **Enterprises**: SSH keys with embedded dept-employee-role → `ACME-ENG-001234`
- **Research Labs**: Signing keys with embedded lab-PI-project → `CHEMLAB-CHEN-PROTEIN-042`
- **Certificate Authorities**: Certs with embedded env-date-serial → `PROD-API-2025-11-17-042`

**Benefits:**
- **Self-describing**: Keys identify themselves (no database lookup)
- **Audit trails**: Logs are human-readable
- **Key rotation**: Track by pattern (year, cohort, etc.)
- **Compliance**: SOC2/ISO27001 audit evidence

**Revenue Model**: $50K-$500K per organization for pattern reservation + private registry

**Documentation**: [ORGANIZATIONAL_KEY_MANAGEMENT.md](docs/ORGANIZATIONAL_KEY_MANAGEMENT.md)

---

### 2. 🗂️ VaniKeys Directory Service (VDS)

**The Insight**: Embedded pattern = **QR-code-like directory pointer**

**How It Works:**
```
Public Key: did:key:...STANFORD-2025-042...

Function 1: Human-readable identifier
  → "Stanford DID from 2025 cohort, student 042"

Function 2: Directory lookup
  → https://registry.stanford.edu/did/042
  → Returns rich metadata, verification status, credentials
```

**Like DNS for Public Keys:**
- Pattern → Registry URL → Metadata
- Public registry (free tier)
- Private registries (enterprise)
- Revocation checking
- QR code integration

**Revenue Model**:
- **Consumer**: Free public registry, $5-10/month premium profiles
- **Enterprise**: $10K-$100K/year private registry hosting
- **DaaS** (Directory-as-a-Service): $500/month - $50K/month SaaS tiers

**Documentation**: [VANIKEYS_DIRECTORY_SERVICE.md](docs/VANIKEYS_DIRECTORY_SERVICE.md)

---

### 3. 🏪 Pattern Marketplace

**The Insight**: Some patterns are inherently more valuable - **pre-generate and sell them**

**Pattern Categories** (270K+ pre-generated):
1. **Common Names**: ALICE, BOB, CEO, VIP ($10-$5K each)
2. **What3Words-Style**: SWIFT-GOLD-TIGER (50K combos, $25-500 each)
3. **Org Hierarchies**: STANFORD-CS, GOOGLE-SRE ($10K-$500K reservations)
4. **Professional Titles**: DR-SMITH, CEO-JONES ($100-$2K each)
5. **Number Blocks**: VIP-001, 2025-042 ($50-$1K each)
6. **Geographic**: NYC, SF, LONDON ($200-$5K each)
7. **Dates**: 2025-11-17, JAN-2025 ($50-$2K each)
8. **BIP39 Combos**: OCEAN-SUNSET-VOYAGE (8.6B combos, $25-500 each)
9. **Industry**: TRADER, ENGINEER, DOCTOR ($100-$500 each)
10. **Status**: FOUNDER-001, PLATINUM-MEMBER ($200-$1K each)

**Marketplace Models:**
- **Dutch Auction**: Price discovery (drops 10%/day until sold)
- **Fixed Price Tiers**: Ultra-premium to common
- **Bulk Sales**: Sequential number blocks for enterprises
- **Secondary Market**: Resale with 10% marketplace fee

**Revenue Potential**:
- **Pattern Sales**: $9.4M Year 1 (30% of 270K patterns)
- **Enterprise Reservations**: $17.5M Year 1
- **Secondary Market**: Growing recurring revenue (10% fees)
- **3-Year Total**: $54M+

**Documentation**: [PATTERN_MARKETPLACE_DESIGN.md](docs/PATTERN_MARKETPLACE_DESIGN.md)

---

## 💰 Combined Business Model

### Consumer Track (Original Plan)
- Gacha gamification: $600K-$3.6M Year 1
- Public registry: Free + premium ($5-10/month)
- Pattern purchases: $10-$500 one-time

### Enterprise Track (NEW - Much Bigger)
- Pattern reservations: $50K-$500K per org
- Private registries: $10K-$100K/year
- Batch key generation: Included in contracts
- Professional services: $150-$300/hour

### Marketplace Track (NEW - Massive)
- Premium pattern sales: $9.4M Year 1
- Enterprise bulk sales: $17.5M Year 1
- Secondary market fees: 10% of all resales
- Total: $27M+ Year 1

**Combined Year 1 Revenue**: $28M-$31M (Consumer $1M + Enterprise $27M-$30M)

---

## 🎯 Strategic Priority

**Original Plan**: Consumer gacha (6 weeks to launch, $600K-$3.6M)

**New Opportunity**: Enterprise + Marketplace ($28M-$31M Year 1)

**Recommended Hybrid Approach:**
1. **Phase 1**: Consumer launch (awareness, validation) - 6 weeks
2. **Phase 2**: Enterprise pilots (2-3 universities/companies) - 12 weeks
3. **Phase 3**: Pattern marketplace (pre-generate, auction ultra-premium) - 8 weeks
4. **Phase 4**: Enterprise scale (10-20 customers, $1M-$5M ARR) - 6+ months

**This could be a $50M+ business instead of $3.6M!**

---

## Quick Start (Developers)

### Phase 1 (CLI - Available Now)

```bash
# Install
cd ~/src/projects/vanikeys
pip install -e .

# Generate vanity key
vanikeys generate --pattern LAB --case-insensitive

# Estimate difficulty
vanikeys estimate --pattern DEADBEEF --type did:key
```

### Phase 2 (Web App - In Development)

```bash
# Setup development environment
docker-compose up -d postgres redis

# Run migrations
alembic upgrade head

# Start web server
python -m vanikeys.web.app

# Start worker (separate terminal)
python -m vanikeys.workers.guaranteed_worker
```

**Implementation Status**: Week 1-2 (Core backend)
**See**: [PHASE2_IMPLEMENTATION_PLAN.md](docs/PHASE2_IMPLEMENTATION_PLAN.md)

## References

### Academic
- ["On the Consideration of Vanity Address Generation via Identity-Based Signatures"](https://arxiv.org/abs/2507.12670) (2025)

### Tools
- [vanitygen-plusplus](https://github.com/10gic/vanitygen-plusplus) - Multi-crypto vanity generator
- [VanitySearch](https://github.com/JeanLucPons/VanitySearch) - Fast Bitcoin address finder
- [vanity-eth-gpu](https://github.com/cenut/vanity-eth-gpu) - GPU-accelerated Ethereum

### Standards
- [W3C DID Core 1.1](https://www.w3.org/TR/did-1.1/)
- [Multiformats](https://multiformats.io/)

## License

TBD (likely MIT or Apache 2.0)

---

**Created**: 2025-11-17
**Session**: descending-star-1117
**TIA Project**: `project://software/vanikeys`
