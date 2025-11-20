# Changelog

All notable changes to VaniKeys will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Planned - Phase 2 Implementation
- VaniPull slot machine mechanics
- Multi-substring pattern matching
- Fuzzy matching rules (0→O, 1→I, 3→E)
- Dual payment models (Gacha + Guaranteed)
- Token economy system
- FastHTML web application
- Stripe payment integration
- See `docs/PHASE2_IMPLEMENTATION_PLAN.md` and `docs/CHANGELIST.md` for details

---

## [0.3.0] - 2025-11-17 - Strategic Expansion

### Added - Business Model Evolution 🚀

**Three major business opportunities identified and documented:**

1. **Organizational Key Management** (`docs/ORGANIZATIONAL_KEY_MANAGEMENT.md` - 22KB)
   - Enterprise B2B opportunity: $1M-$10M+ ARR potential
   - Functional metadata embedding for organizational keys
   - 5 key types documented: SSH, DIDs, Code Signing, TLS/SSL, IoT devices
   - Use cases: Universities, enterprises, research labs, CAs, IoT manufacturers
   - Pattern templates for batch key generation
   - Pricing models: $5K-$500K per organization

2. **Directory Service** (`docs/VANIKEYS_DIRECTORY_SERVICE.md` - 19KB)
   - Infrastructure SaaS: $1M-$10M ARR potential
   - Pattern → Registry lookup system (like DNS for keys)
   - Public registry (FREE tier) + Private registries (Enterprise)
   - Registry API, web interface, verification service
   - Privacy tiers: Public, Verified, Private (self-hosted)
   - Pricing: $10K-$100K annual for enterprise private registries

3. **Pattern Marketplace** (`docs/PATTERN_MARKETPLACE_DESIGN.md` - 24KB)
   - Premium pattern sales: $27M+ Year 1 potential
   - 270,000+ pre-generated patterns across 10 categories
   - What3Words-style patterns: 50,000 combinations (SWIFT-GOLD-TIGER)
   - Organizational hierarchies: STANFORD-CS, MIT-AI ($10K-$500K reservations)
   - Dutch auction + English auction + Fixed price tiers
   - Secondary marketplace with 10% platform fee

**Revenue Impact:**
- Original consumer model: $600K-$3.6M Year 1
- New combined model: **$28M-$31M Year 1** (10x-50x increase!)
- Hybrid approach: Consumer + Enterprise + Marketplace

**Strategic Documents Created:**
- Business analysis: 65KB across 3 comprehensive documents
- Market sizing, pricing models, use cases fully documented
- Integration with W3C DID Documents, X.509 extensions, SSH extensions

### Updated
- `README.md` - Added "Strategic Expansions" section summarizing three opportunities
- Business model now encompasses consumer, enterprise, and marketplace revenue streams

### Session
- Session: drifting-quasar-1117
- Duration: ~60 minutes (strategic expansion portion)
- Type: Strategic business planning

---

## [0.2.0] - 2025-11-17 - Gamification Design

### Added - Phase 2 Planning 🎰

**VaniPull Slot Machine Mechanics:**
- Complete gamification design (`docs/GAMIFICATION_DESIGN.md` - 37KB)
- VaniPull system: Token economy + dual payment models
- Multi-substring matching with fuzzy rules
- "What You Got" UI showing bonus matches
- Near-miss psychology and engagement mechanics
- Social sharing and viral features

**Implementation Roadmap:**
- 6-week implementation plan (`docs/PHASE2_IMPLEMENTATION_PLAN.md` - 27KB)
- 62-file changelist with ~10,000 LOC planned (`docs/CHANGELIST.md` - 31KB)
- Week 1-2: Backend (matchers, probability, token economy)
- Week 3-4: Frontend (FastHTML, VaniPull animation, results UI)
- Week 5-6: Payments (Stripe) + production launch

**Business Model:**
- VaniTokens: $5-$300 packages (primary revenue)
- Guaranteed Mode: 15% premium for exact match delivery
- Enterprise DID Branding: $5K-$50K contracts (future)
- Revenue projections: $72K-$1.44M Year 1 (conservative to optimistic)

**Competitive Advantages:**
- First DID-focused vanity generator with gamification
- Multi-substring matching ("GO BE AWE SOME")
- Fuzzy matching increases match rate 10x
- Transparent odds and ethical gamification
- Dual payment models (gacha vs guaranteed)

### Session
- Session: fecuwo-1117
- Duration: Multiple sessions refining gamification mechanics
- Type: Product design and implementation planning

---

## [0.1.0] - 2025-11-17 - Phase 1 Foundation

### Added - Core Engine ✅

**Core Implementation** (~1,800 LOC):
- Ed25519 key generation with DID output
- Pattern matching: prefix, suffix, contains, regex
- Difficulty estimation and probability calculations
- CLI interface with comprehensive options
- Split-key vanity generation (secure third-party generation)

**Key Features:**
- `vanikeys generate` - Generate vanity keys with custom patterns
- `vanikeys estimate` - Estimate difficulty and time for patterns
- `vanikeys batch` - Batch generation for multiple patterns
- Support for DID method: `did:key:z6Mk...`
- Configurable difficulty targets and output formats

**Documentation** (~2,800 lines):
- `README.md` - Project overview and quick start
- `QUICKSTART.md` - 280-line getting started guide
- `docs/ARCHITECTURE.md` - 680-line technical design
- `docs/DEPLOYMENT_PLAN.md` - 1,122-line production deployment strategy

**Deployment Ready:**
- Containerization strategy (Podman)
- TIA-stickers infrastructure integration
- Production deployment plan complete
- FastHTML web app framework selected

**Technical Stack:**
- Python 3.11+
- Ed25519 cryptography (ed25519-blake2b)
- DID key generation (did-key library)
- FastHTML (planned for Phase 2 web UI)
- PostgreSQL + Redis (planned for Phase 2)

### Market Position
- **First DID-focused vanity key generator** (unexplored niche)
- Competitors: Bitcoin/Ethereum vanity generators only
- Unique value: DID vanity generation for self-sovereign identity use cases
- Market size: 50M+ crypto users, 100K+ DID early adopters

### Session
- Session: descending-star-1117
- Duration: Single session (concept to Phase 1 complete!)
- Type: Rapid implementation sprint

---

## Next Steps

**Immediate Priority** (Choose one):
1. **Validate Enterprise Opportunity**: Pilot with 3 organizations (university, company, lab)
2. **Continue Consumer Path**: Implement Phase 2 gamification (6 weeks)
3. **Build Pattern Marketplace**: Generate premium patterns, launch auctions (4 weeks)

**Recommended**: Validate enterprise first (highest ACV, lowest risk)

---

**Project**: VaniKeys
**Repository**: `/home/scottsen/src/projects/vanikeys`
**Status**: Phase 1 Complete, Phase 2 Planned, Strategic Expansion Documented
**Revenue Potential**: $28M-$31M Year 1 (combined model)
