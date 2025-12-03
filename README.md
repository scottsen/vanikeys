# VaniKeys - Gamified Vanity Key Generation

**Crypto Slot Machine Meets Vanity Key Generation**

Turn the boring wait for vanity keys into an entertaining gacha experience with transparent odds, fair pricing, and optional guaranteed delivery.

---

## 🎯 Quick Start (5 Minutes)

```bash
# Clone and setup
cd /home/scottsen/src/projects/vanikeys

# Create virtual environment
uv venv
source .venv/bin/activate

# Install dependencies
uv pip install -e ".[dev]"

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Start infrastructure (PostgreSQL + Redis)
docker-compose up -d

# Run development server
python -m vanikeys.app

# Verify
curl http://localhost:8000/health
```

**Access**: http://localhost:8000

---

## 🌟 What is VaniKeys?

VaniKeys transforms cryptographic vanity key generation into an engaging slot machine experience:

### The Problem
Traditional vanity generators are **boring**:
- "Pay $X and wait Y minutes"
- No engagement, no fun
- Hidden pricing, unclear odds
- Single prefix/suffix matching only

### The VaniKeys Solution
**Gamification + Transparency + Innovation**:
- 🎰 **VaniPull Mechanic**: Slot machine-style key generation
- 📊 **Complete Transparency**: Visible odds before purchase
- 🎯 **Multi-Substring Matching**: "GO BE AWE SOME" (sequential patterns)
- 🔀 **Fuzzy Matching**: 0→O, 1→I, 3→E (10x more matches)
- 💎 **Dual Payment Models**: Gacha mode OR guaranteed delivery
- 🤖 **AI-Powered**: Pattern suggestions, difficulty explanations

---

## 💰 Business Model

### Bootstrap Score: 85/100
- **Capital Required**: $0 (serverless infrastructure)
- **Time to Revenue**: 6 weeks
- **Year 1 Target**: $600K-$3.6M

### Revenue Streams

**1. VaniTokens (Gacha Mode)** - Primary Revenue
```yaml
Pricing:
  100 tokens: $5
  500 tokens: $20 (20% bonus)
  2000 tokens: $70 (30% bonus)
  10000 tokens: $300 (40% bonus)

Pull_Cost: 100-500 tokens (based on difficulty)

Projections:
  100 users × $50/month = $5K/month
  500 users × $50/month = $25K/month
  2000 users × $50/month = $100K/month
```

**2. Guaranteed Mode** - Whale Revenue
```yaml
Model: Pay 15% premium for exact match delivery
Use_Cases:
  - Businesses needing branded DIDs
  - High-value patterns
  - Professional use cases

Projections: 20% of users, $100 avg purchase
```

**3. Enterprise DID Branding** - Future Revenue
```yaml
Model: White-label DID generation
Pricing: $5K-$50K one-time + $500-$5K/month
Timeline: 6-12 months after consumer validation
```

---

## 🏗️ Architecture

### Technology Stack

**Frontend**:
- FastHTML (Python-based web framework)
- HTMX (dynamic updates)
- Tailwind CSS (styling)

**Backend**:
- FastHTML + PostgreSQL (core application)
- Redis (job queue + caching)
- Structlog (structured logging)

**Compute**:
- RunPod Serverless (GPU - gacha mode, <200ms cold start)
- Modal (GPU - guaranteed mode, checkpointing)
- Cost: $24/month for 100 jobs/day (vs $1,095/month dedicated GPU)

**Payments**:
- Stripe (payment processing)
- Token economy system

**AI Features**:
- Together.ai (Llama 3.1 70B)
- Cost: $13/month for 30K requests
- Pattern suggestions, difficulty explanations

### Infrastructure Cost

```yaml
MVP (100 jobs/day):
  RunPod: $24/month
  Together.ai: $13/month
  Hosting: $12/month
  Redis: $20/month
  Total: $69/month

Revenue: $10,950/month
Profit Margin: 99.4%
```

### System Design

```
┌─────────────┐
│   Client    │
│  (Browser)  │
└──────┬──────┘
       │
┌──────▼────────┐
│  FastHTML     │
│   Web App     │
└──────┬────────┘
       │
   ┌───┴────────────┐
   │                │
┌──▼──────┐   ┌────▼─────┐
│ Gacha   │   │Guaranteed│
│  Mode   │   │   Mode   │
└──┬──────┘   └────┬─────┘
   │               │
┌──▼─────────┐ ┌──▼────────┐
│  RunPod    │ │   Modal   │
│Serverless  │ │   (GPU)   │
│<200ms cold │ │Checkpoints│
│$0.008/job  │ │Long jobs  │
└────────────┘ └───────────┘
```

---

## 📁 Project Structure

```
vanikeys/
├── pyproject.toml          # Python project configuration
├── README.md               # This file
├── CHANGELOG.md            # Version history
├── .env.example            # Environment template
│
├── src/
│   └── vanikeys/
│       ├── __init__.py     # Package initialization
│       ├── domain/         # Pure models (Pattern, Key, Pull, etc.)
│       ├── services/       # Business logic (PullService, TokenService)
│       ├── repositories/   # Data access (UserRepo, PullRepo)
│       ├── ui/             # FastHTML components
│       ├── routes/         # API endpoints
│       └── config/         # Configuration & wiring
│
├── tests/                  # Test suite
│   ├── test_domain.py
│   ├── test_services.py
│   └── test_integration.py
│
├── docs/                   # Documentation
│   ├── DEPLOYMENT_GUIDE.md # Complete deployment guide
│   ├── ARCHITECTURE.md     # System architecture (from Phase 1)
│   ├── GAMIFICATION_DESIGN.md  # Game mechanics (from Phase 2)
│   └── PHASE2_IMPLEMENTATION_PLAN.md  # 6-week roadmap
│
└── deployment/             # Deployment scripts
    ├── deploy-staging.sh
    ├── deploy-production.sh
    └── rollback.sh
```

---

## 🚀 Development

### Prerequisites

- Python 3.10+
- PostgreSQL 14+
- Redis 7+
- Docker (for local infrastructure)

### Setup Development Environment

```bash
# Install uv (fast package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment
uv venv
source .venv/bin/activate

# Install project in editable mode with dev dependencies
uv pip install -e ".[dev]"

# Setup infrastructure
docker-compose up -d

# Run database migrations
python -m vanikeys.migrations.run

# Start development server
python -m vanikeys.app --reload
```

### Development Workflow

```bash
# Run tests
pytest

# Run tests with coverage
pytest --cov=src tests/

# Lint code
ruff check .

# Format code
ruff format .

# Type check
mypy src/

# Explore code structure
reveal src/vanikeys/
```

### Using Reveal for Code Exploration

```bash
# View project structure
reveal src/vanikeys/

# View specific module
reveal src/vanikeys/services/pull_service.py

# Extract specific function
reveal src/vanikeys/services/pull_service.py execute_pull

# Find complex functions
reveal src/vanikeys/ --god
```

---

## 🎯 Phase 2 Implementation Plan

### Status: Ready to Begin

**Timeline**: 6 weeks to MVP launch

### Week 1-2: Core Backend
- [ ] Multi-substring matcher implementation
- [ ] Probability calculator (odds display)
- [ ] Database schema (Users, Pulls, Transactions, Jobs)
- [ ] Token economy backend
- [ ] VaniPull engine

### Week 3-4: Frontend
- [ ] FastHTML web app structure
- [ ] Pattern submission form with live odds
- [ ] VaniPull animation (slot machine reveal)
- [ ] Results display ("What You Got" UI)
- [ ] Pull history and account management

### Week 5-6: Payments & Launch
- [ ] Stripe integration (token purchases)
- [ ] Guaranteed mode background workers
- [ ] Production deployment (tia-apps)
- [ ] Beta testing with 10 users
- [ ] Public launch (Product Hunt + crypto communities)

### Success Metrics (Month 1)
- [ ] 50 beta signups
- [ ] 10 paying customers
- [ ] $500 revenue
- [ ] 100+ pulls executed
- [ ] <5% error rate

---

## 🎮 Key Features

### 1. VaniPull Slot Machine Mechanic
- Users buy VaniTokens
- Spend tokens on VaniPulls
- See results with slot machine animation
- "What You Got" UI shows all matches (exact + partial)

### 2. Multi-Substring Sequential Matching
```python
Pattern: "GO BE AWE SOME"
Matches: did:key:...GO...BE...AWE...SOME...

# Sequential order matters
# Any characters between substrings OK
# 10x more engaging than single prefix/suffix
```

### 3. Fuzzy Character Matching
```yaml
Rules:
  0 ↔ O
  1 ↔ I
  3 ↔ E

Impact: 10x more matches
Example: "G0AL" matches "GOAL", "G0AL", "GO4L", etc.
```

### 4. AI-Powered Features
- **Pattern Suggester**: AI generates 5 ideas from description
- **Difficulty Explainer**: "1 in 4.2B" → human-friendly terms
- **NLP Parser**: "swift golden tiger" → "SWIFT GOLD TIGER"
- **Cost**: <$50/month for 30K requests

### 5. Transparent Odds
```yaml
Before_Purchase:
  - Exact match probability shown
  - Partial match probabilities shown
  - Token cost displayed
  - Expected value calculated

During_Pull:
  - Live generation animation
  - Result revelation (slot machine style)

After_Pull:
  - What you got (all matches)
  - Bonus matches highlighted
  - Share to social media
```

---

## 🏆 Competitive Advantages

### vs. Traditional Vanity Generators
✅ DID support (no competitor has this)
✅ Multi-substring matching
✅ Fuzzy matching (10x more matches)
✅ Gamified experience
✅ Dual payment models
✅ Complete transparency

### vs. DIY Solutions
✅ No technical knowledge required
✅ GPU acceleration (50M keys/sec vs 10-20K CPU)
✅ Web interface (no CLI)
✅ Probability estimation
✅ Guaranteed delivery option
✅ Secure split-key technology

---

## 📚 Documentation

### Core Documents
- **[DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md)** - Complete deployment guide
- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - System architecture (Phase 1)
- **[GAMIFICATION_DESIGN.md](docs/GAMIFICATION_DESIGN.md)** - Complete game design (Phase 2)
- **[PHASE2_IMPLEMENTATION_PLAN.md](docs/PHASE2_IMPLEMENTATION_PLAN.md)** - 6-week roadmap
- **[CHANGELIST.md](docs/CHANGELIST.md)** - 62 files, ~10K LOC planned

### TIA Integration
```bash
# Project dashboard
tia project show vanikeys

# Related sessions
tia session search vanikeys

# Knowledge graph
tia beth explore "vanikeys"

# Tasks
tia task list --search vanikeys
```

---

## 🔗 External Resources

### Development Tools
- [FastHTML](https://fastht.ml/) - Python web framework
- [reveal-cli](https://github.com/scottsen/reveal) - Code exploration
- [uv](https://github.com/astral-sh/uv) - Fast Python package manager
- [ruff](https://github.com/astral-sh/ruff) - Fast linter & formatter

### Infrastructure
- [RunPod Serverless](https://www.runpod.io/) - GPU compute
- [Modal](https://modal.com/) - Serverless Python
- [Together.ai](https://www.together.ai/) - LLM API

### Related Research
- **Session xolihu-1117**: Serverless GPU infrastructure research
- **Session fecuwo-1117**: Phase 2 gamification design
- **Session descending-star-1117**: Phase 1 foundation

---

## 📊 Progress Tracking

**Current Status**: Phase 2 Planning → Implementation

**Completed**:
- ✅ Phase 1: Core engine implementation
- ✅ Phase 2: Complete gamification design
- ✅ Infrastructure research (serverless GPU)
- ✅ Business model validation
- ✅ 6-week implementation plan
- ✅ TIA project structure aligned

**Next Up**:
- 🚧 Week 1: Multi-substring matcher + probability calculator
- ⏳ Week 2: Token economy + database schema
- ⏳ Week 3-4: Frontend UI
- ⏳ Week 5-6: Payments + launch

**Track Progress**: `tia task list --search vanikeys`

---

## 🤝 Contributing

This is a solo project (bootstrap opportunity), but best practices:

1. Follow TIA Python Development Guide
2. Write tests for new features
3. Use reveal for code exploration before modifying
4. Keep functions small (3-7 lines ideal)
5. Maintain layer separation (domain → services → repos)

---

## 📜 License

Proprietary - Revenue-generating business opportunity

---

## 🎬 Let's Build This!

**Bootstrap Score**: 85/100
**Capital Required**: $0
**Timeline**: 6 weeks to first dollar
**Year 1 Target**: $600K-$3.6M

**Ready to start**: Week 1 tasks in `docs/PHASE2_IMPLEMENTATION_PLAN.md`

---

**Version**: 0.1.0 (Pre-MVP)
**Last Updated**: 2025-12-03
**Status**: Phase 2 Planning → Implementation
