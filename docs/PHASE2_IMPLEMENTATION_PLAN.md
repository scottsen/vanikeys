# VaniKeys Phase 2: Gamification Implementation Plan

**Version**: 1.0
**Created**: 2025-11-17
**Timeline**: 6 weeks
**Goal**: Launch gamified VaniKeys MVP with VaniPull mechanics

---

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Architecture Overview](#architecture-overview)
- [Week-by-Week Plan](#week-by-week-plan)
- [File Changelist](#file-changelist)
- [Testing Strategy](#testing-strategy)
- [Deployment Plan](#deployment-plan)
- [Success Metrics](#success-metrics)

---

## Overview

### What We're Building

Transform VaniKeys from a CLI utility into a gamified web service with:
- 🎰 Slot machine-style "pulls" for key generation
- 🪙 Token economy with multiple pricing tiers
- 🎯 Multi-substring pattern matching with fuzzy rules
- 📊 Transparent odds display
- 💰 Dual payment models (gacha vs guaranteed)

### What Already Exists (Phase 1)

✅ Core key generation engine
✅ Ed25519 + DID support
✅ Basic pattern matching (prefix/suffix/contains/regex)
✅ CLI interface
✅ Difficulty estimation
✅ Comprehensive documentation

### What We Need to Build (Phase 2)

**Backend:**
- Multi-substring matcher with fuzzy matching
- Probability calculator for complex patterns
- VaniPull engine (gacha + guaranteed modes)
- Token economy (user accounts, balances, transactions)
- Payment integration (Stripe)
- Job queue for guaranteed mode (Redis + workers)

**Frontend:**
- FastHTML web application
- Pattern submission UI
- Odds display
- Pull animation
- "What You Got" results display
- Token purchase flow
- User dashboard

**Infrastructure:**
- PostgreSQL database
- Redis job queue
- Background workers
- Containerization (Podman)
- Deployment to tia-stickers

---

## Prerequisites

### Development Environment

**Required:**
- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Node.js 18+ (for frontend tooling)
- Git

**Optional but Recommended:**
- Podman (for local container testing)
- pgAdmin (database management)
- Redis Commander (Redis GUI)

### Dependencies to Add

```toml
# Add to pyproject.toml

[project]
dependencies = [
    # Existing
    "cryptography>=42.0.0",
    "click>=8.1.7",
    "rich>=13.7.0",

    # New for Phase 2
    "fasthtml>=0.4.0",           # Web framework
    "python-fasthtml>=0.4.0",    # FastHTML components
    "sqlalchemy>=2.0.23",        # ORM
    "alembic>=1.13.0",           # Database migrations
    "redis>=5.0.1",              # Job queue
    "stripe>=7.7.0",             # Payment processing
    "pydantic>=2.5.2",           # Data validation
    "pydantic-settings>=2.1.0",  # Settings management
    "passlib[bcrypt]>=1.7.4",    # Password hashing
    "python-jose[cryptography]>=3.3.0",  # JWT tokens
    "httpx>=0.25.2",             # HTTP client
    "pytest>=7.4.3",             # Testing
    "pytest-asyncio>=0.23.2",    # Async testing
    "faker>=21.0.0",             # Test data generation
]
```

### Environment Variables

Create `.env` file:
```bash
# Database
DATABASE_URL=postgresql://vanikeys:password@localhost:5432/vanikeys

# Redis
REDIS_URL=redis://localhost:6379/0

# Stripe
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Application
SECRET_KEY=your-secret-key-here
DEBUG=true
ENVIRONMENT=development

# Token Pricing (cents)
TOKEN_PRICE_STARTER=99      # $0.99 for 100 tokens
TOKEN_PRICE_POPULAR=399     # $3.99 for 500 tokens
TOKEN_PRICE_POWER=1499      # $14.99 for 2500 tokens
TOKEN_PRICE_WHALE=4999      # $49.99 for 10000 tokens
```

---

## Architecture Overview

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                      VaniKeys System                         │
└─────────────────────────────────────────────────────────────┘

┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│   Frontend   │─────▶│   FastHTML   │─────▶│  PostgreSQL  │
│   (HTMX)     │◀─────│   Backend    │◀─────│   Database   │
└──────────────┘      └──────────────┘      └──────────────┘
                            │
                            │
                            ▼
                      ┌──────────────┐
                      │    Redis     │
                      │  Job Queue   │
                      └──────────────┘
                            │
                            │
                            ▼
                      ┌──────────────┐
                      │   Workers    │
                      │  (Gacha +    │
                      │  Guaranteed) │
                      └──────────────┘
                            │
                            │
                            ▼
                      ┌──────────────┐
                      │   VaniKeys   │
                      │  Core Engine │
                      └──────────────┘
```

### Database Schema

**Users:**
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    token_balance INTEGER DEFAULT 0,
    free_pulls_today INTEGER DEFAULT 3,
    free_pulls_reset_at TIMESTAMP,
    subscription_tier VARCHAR(20) DEFAULT 'free',
    subscription_expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**Pulls:**
```sql
CREATE TABLE pulls (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    pattern TEXT NOT NULL,
    pattern_config JSONB,  -- fuzzy, case_insensitive, etc
    result_key TEXT,
    match_score FLOAT,
    matches JSONB,
    missing JSONB,
    bonus JSONB,
    is_win BOOLEAN DEFAULT FALSE,
    tokens_spent INTEGER,
    pull_number INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Transactions:**
```sql
CREATE TABLE transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    type VARCHAR(20) NOT NULL,  -- purchase, pull, refund
    amount INTEGER NOT NULL,    -- token amount
    balance_before INTEGER,
    balance_after INTEGER,
    payment_intent_id VARCHAR(255),  -- Stripe reference
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Jobs (Guaranteed Mode):**
```sql
CREATE TABLE jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    pattern TEXT NOT NULL,
    pattern_config JSONB,
    status VARCHAR(20) DEFAULT 'queued',  -- queued, running, completed, failed
    tokens_paid INTEGER,
    attempts INTEGER DEFAULT 0,
    result_key TEXT,
    match_result JSONB,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### API Endpoints

**Authentication:**
- `POST /auth/register` - Create account
- `POST /auth/login` - Login (returns JWT)
- `POST /auth/logout` - Logout
- `GET /auth/me` - Current user info

**Patterns:**
- `POST /api/patterns/estimate` - Calculate odds for pattern
- `POST /api/patterns/validate` - Validate pattern syntax

**Pulls (Gacha Mode):**
- `POST /api/pulls/execute` - Execute single pull
- `GET /api/pulls/history` - User's pull history
- `GET /api/pulls/:id` - Get specific pull result

**Jobs (Guaranteed Mode):**
- `POST /api/jobs/create` - Create guaranteed job
- `GET /api/jobs/:id` - Get job status
- `GET /api/jobs/:id/result` - Get job result (when complete)

**Tokens:**
- `GET /api/tokens/balance` - Current token balance
- `GET /api/tokens/transactions` - Transaction history
- `POST /api/tokens/purchase` - Initiate purchase (Stripe)

**Payments (Stripe):**
- `POST /api/payments/create-intent` - Create Stripe PaymentIntent
- `POST /api/payments/webhook` - Stripe webhook handler

**Pages:**
- `GET /` - Landing page
- `GET /app` - Main application (authenticated)
- `GET /pricing` - Token pricing page
- `GET /how-it-works` - Tutorial/explanation

---

## Week-by-Week Plan

### Week 1: Core Backend (Multi-Substring Matcher + Probability)

**Goal**: Implement pattern matching and odds calculation

**Tasks:**

1. **Multi-Substring Matcher** (2 days)
   - File: `src/vanikeys/matchers/multi_substring.py`
   - Implement `MultiSubstringMatcher` class
   - Support sequential substring matching
   - Fuzzy character substitutions (0→O, 1→I, etc)
   - Unit tests

2. **Probability Calculator** (2 days)
   - File: `src/vanikeys/core/probability.py`
   - Implement `ProbabilityCalculator` class
   - Calculate odds for multi-substring patterns
   - Calculate partial match probabilities
   - Fuzzy matching factor calculation
   - Unit tests

3. **CLI Integration** (1 day)
   - Add `vanikeys estimate-multi` command
   - Test multi-substring patterns from CLI
   - Validate against manual calculations

**Deliverables:**
- ✅ Working multi-substring matcher
- ✅ Accurate probability calculations
- ✅ CLI command for testing
- ✅ Unit tests (>90% coverage)

**Testing:**
```bash
# Test multi-substring matching
vanikeys estimate-multi "GO BE AWE SOME" --fuzzy --case-insensitive

# Expected output:
# Exact match: 1 in 4,234,567,890 (0.000000024%)
# 3/4 match: 1 in 421,356 (0.000237%)
# 2/4 match: 1 in 17,576 (0.0057%)
# 1/4 match: 1 in 68 (1.47%)
```

---

### Week 2: VaniPull Engine + Database

**Goal**: Implement core pull mechanics and persistence

**Tasks:**

1. **Database Setup** (1 day)
   - File: `src/vanikeys/db/models.py`
   - SQLAlchemy models (User, Pull, Transaction, Job)
   - Alembic migrations
   - Database initialization script

2. **VaniPull Engine** (2 days)
   - File: `src/vanikeys/engine/vanipull.py`
   - Implement `VaniPullEngine` class
   - Gacha mode (single pull with token deduction)
   - Result formatting ("What You Got")
   - Pull history recording

3. **Token Economy** (1 day)
   - File: `src/vanikeys/economy/tokens.py`
   - Token balance management
   - Transaction logging
   - Free daily pulls (3/day for free users)

4. **Testing** (1 day)
   - Integration tests
   - Database fixture setup
   - Test pull execution end-to-end

**Deliverables:**
- ✅ Working database schema
- ✅ VaniPull engine (gacha mode)
- ✅ Token economy logic
- ✅ Integration tests

**Testing:**
```python
# Test pull execution
from vanikeys.engine import VaniPullEngine
from vanikeys.matchers import MultiSubstringMatcher

matcher = MultiSubstringMatcher(["GO", "BE", "AWE", "SOME"])
engine = VaniPullEngine(matcher=matcher, mode="gacha")

result = engine.pull(user_id="test-user")
print(result.to_ui_dict())
# Expected: key, match score, matches list, missing, bonus, tokens remaining
```

---

### Week 3: FastHTML Frontend (Pattern Submission + Odds)

**Goal**: Build web UI for pattern submission and odds display

**Tasks:**

1. **FastHTML Application Setup** (1 day)
   - File: `src/vanikeys/web/app.py`
   - FastHTML app initialization
   - Route structure
   - Authentication middleware
   - Static assets setup

2. **Pattern Submission UI** (2 days)
   - File: `src/vanikeys/web/components/pattern_form.py`
   - Pattern input form
   - Substring configuration (fuzzy, case-insensitive)
   - Real-time validation
   - HTMX integration

3. **Odds Display UI** (2 days)
   - File: `src/vanikeys/web/components/odds_display.py`
   - Probability breakdown
   - Token cost calculator
   - Visual chart (if time permits)
   - Gacha vs Guaranteed comparison

**Deliverables:**
- ✅ Working FastHTML app
- ✅ Pattern submission form
- ✅ Odds display page
- ✅ Basic styling (responsive)

**UI Flow:**
```
1. User visits /app
2. Enter pattern: "GO BE AWE SOME"
3. Click "Calculate Odds"
4. See odds display:
   - Exact: 1 in 4.2B
   - 3/4: 1 in 421K
   - Gacha: 100 tokens/pull
   - Guaranteed: 484K tokens
5. Choose "Gacha Mode" button
```

---

### Week 4: Pull Animation + Results Display

**Goal**: Implement pull execution UI and results

**Tasks:**

1. **Pull Animation** (2 days)
   - File: `src/vanikeys/web/components/pull_animation.py`
   - Slot machine-style loading animation
   - Progress indicator
   - Sound effects (optional, toggle)
   - HTMX polling for result

2. **"What You Got" Results Display** (2 days)
   - File: `src/vanikeys/web/components/results_display.py`
   - Match score visualization (⭐⭐⭐☆)
   - Matched substrings (with positions)
   - Missing substrings
   - Bonus patterns found
   - "Kind of what you wanted?" copy
   - Action buttons (Pull Again, Keep Key, Share)

3. **Pull History** (1 day)
   - File: `src/vanikeys/web/pages/history.py`
   - List of past pulls
   - Filter by match score
   - Export keys

**Deliverables:**
- ✅ Working pull animation
- ✅ Results display UI
- ✅ Pull history page

**UI Flow:**
```
1. User clicks "Pull for 100 Tokens"
2. Animation shows:
   [▓▓▓▓▓▓▓░░░░░] 50%
   Generating key...
3. Result reveals:
   did:key:z6Mk3468GO5643BEE3596SOME
   ✅ GO, ✅ BE, ✅ SOME (3/4) - 75%
   Missing: AWE
   Bonus: BEE, 68GO
4. Buttons: [Pull Again] [Keep This Key] [Share]
```

---

### Week 5: Payments + Guaranteed Mode

**Goal**: Implement token purchases and guaranteed generation

**Tasks:**

1. **Stripe Integration** (2 days)
   - File: `src/vanikeys/payments/stripe_client.py`
   - Stripe API setup
   - PaymentIntent creation
   - Webhook handler (payment success)
   - Token crediting on successful payment

2. **Purchase Flow UI** (1 day)
   - File: `src/vanikeys/web/pages/pricing.py`
   - Token package cards (Starter, Popular, Power, Whale)
   - Stripe Checkout integration
   - Success/cancel pages

3. **Guaranteed Mode** (2 days)
   - File: `src/vanikeys/engine/guaranteed.py`
   - Job creation and queueing (Redis)
   - Background worker (separate process)
   - Job status polling UI
   - Result delivery

**Deliverables:**
- ✅ Working Stripe integration
- ✅ Token purchase flow
- ✅ Guaranteed mode (jobs + workers)

**Testing:**
```bash
# Test Stripe (using test keys)
# 1. Navigate to /pricing
# 2. Select "Power Pack" ($14.99)
# 3. Complete test payment (4242 4242 4242 4242)
# 4. Verify 2,500 tokens credited

# Test Guaranteed Mode
# 1. Submit pattern "ACME CORP"
# 2. Click "Guaranteed Mode"
# 3. Pay tokens upfront
# 4. Monitor job status page
# 5. Receive notification when complete
```

---

### Week 6: Polish + Launch

**Goal**: Final polish, testing, and production deployment

**Tasks:**

1. **UI Polish** (2 days)
   - Consistent styling across pages
   - Mobile responsiveness
   - Loading states
   - Error handling UI
   - Success animations (confetti on jackpot)
   - Sound effects (with toggle)

2. **Testing** (2 days)
   - End-to-end testing
   - Load testing (concurrent pulls)
   - Payment testing (Stripe test mode)
   - Security audit (SQL injection, XSS, CSRF)
   - Browser compatibility

3. **Deployment** (1 day)
   - Containerize with Podman
   - Deploy to tia-stickers
   - Configure tia-proxy (nginx SSL)
   - Setup production database
   - Configure production Stripe keys
   - Setup monitoring (logs, metrics)

**Deliverables:**
- ✅ Polished, production-ready UI
- ✅ All tests passing
- ✅ Deployed to production
- ✅ Monitoring in place

**Launch Checklist:**
- [ ] All features working in production
- [ ] Stripe live mode enabled
- [ ] SSL certificate valid
- [ ] Database backups configured
- [ ] Error logging (Sentry or similar)
- [ ] Performance monitoring
- [ ] Landing page live
- [ ] How It Works tutorial complete
- [ ] Terms of Service + Privacy Policy
- [ ] Social media accounts created
- [ ] Launch announcement ready

---

## File Changelist

### New Files to Create

**Backend (Python):**

```
src/vanikeys/
├── matchers/
│   └── multi_substring.py          # NEW - Multi-substring matcher
│
├── core/
│   └── probability.py              # NEW - Probability calculator
│
├── engine/
│   ├── __init__.py                 # NEW
│   ├── vanipull.py                 # NEW - VaniPull engine
│   └── guaranteed.py               # NEW - Guaranteed mode
│
├── economy/
│   ├── __init__.py                 # NEW
│   └── tokens.py                   # NEW - Token management
│
├── db/
│   ├── __init__.py                 # NEW
│   ├── base.py                     # NEW - Database connection
│   ├── models.py                   # NEW - SQLAlchemy models
│   └── migrations/                 # NEW - Alembic migrations
│       └── versions/
│
├── payments/
│   ├── __init__.py                 # NEW
│   └── stripe_client.py            # NEW - Stripe integration
│
├── workers/
│   ├── __init__.py                 # NEW
│   └── guaranteed_worker.py        # NEW - Background worker
│
└── web/
    ├── __init__.py                 # NEW
    ├── app.py                      # NEW - FastHTML app
    ├── auth.py                     # NEW - Authentication
    ├── components/
    │   ├── __init__.py             # NEW
    │   ├── pattern_form.py         # NEW - Pattern input form
    │   ├── odds_display.py         # NEW - Odds display
    │   ├── pull_animation.py       # NEW - Pull animation
    │   └── results_display.py      # NEW - Results display
    ├── pages/
    │   ├── __init__.py             # NEW
    │   ├── landing.py              # NEW - Landing page
    │   ├── app.py                  # NEW - Main app page
    │   ├── pricing.py              # NEW - Pricing page
    │   ├── history.py              # NEW - Pull history
    │   └── how_it_works.py         # NEW - Tutorial
    └── static/
        ├── css/
        │   └── style.css           # NEW - Custom styles
        └── js/
            └── app.js              # NEW - Client-side JS
```

**Configuration:**

```
.env                                # NEW - Environment variables
alembic.ini                         # NEW - Alembic config
docker-compose.yml                  # NEW - Local development
Containerfile.web                   # NEW - Web container
Containerfile.worker                # NEW - Worker container
systemd/
├── vanikeys-web.service            # NEW - Web service
└── vanikeys-worker.service         # NEW - Worker service
```

**Documentation:**

```
docs/
├── PHASE2_IMPLEMENTATION_PLAN.md   # NEW - This file
├── API.md                          # NEW - API documentation
└── DEPLOYMENT.md                   # NEW - Deployment guide
```

### Files to Modify

**Existing files that need updates:**

```
src/vanikeys/
├── cli/main.py                     # MODIFY - Add estimate-multi command
└── __init__.py                     # MODIFY - Export new modules

pyproject.toml                      # MODIFY - Add dependencies
README.md                           # MODIFY - Update with Phase 2 status
requirements.txt                    # MODIFY - Regenerate from pyproject.toml
```

---

## Testing Strategy

### Unit Tests

**Coverage Target**: >90%

```bash
pytest tests/unit/ -v --cov=vanikeys --cov-report=html
```

**Test Files:**
```
tests/
├── unit/
│   ├── test_multi_substring_matcher.py
│   ├── test_probability_calculator.py
│   ├── test_vanipull_engine.py
│   ├── test_token_economy.py
│   └── test_guaranteed_mode.py
└── integration/
    ├── test_pull_flow.py
    ├── test_payment_flow.py
    └── test_guaranteed_flow.py
```

### Integration Tests

**Test Scenarios:**

1. **Full Gacha Flow**:
   - User registers
   - User submits pattern
   - User executes pull
   - Result displayed
   - Token balance updated
   - Pull recorded in history

2. **Full Payment Flow**:
   - User selects token package
   - Stripe checkout completes
   - Webhook received
   - Tokens credited
   - Transaction logged

3. **Full Guaranteed Flow**:
   - User submits complex pattern
   - User selects guaranteed mode
   - Tokens deducted upfront
   - Job queued
   - Worker processes job
   - Result delivered
   - User notified

### Load Tests

**Tools**: `locust` or `k6`

**Test Scenarios:**
- 100 concurrent users pulling
- 1000 requests/minute sustained
- Database connection pool handling
- Redis queue depth under load

```python
# Example locust test
from locust import HttpUser, task, between

class VaniKeysUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def execute_pull(self):
        self.client.post("/api/pulls/execute", json={
            "pattern": ["GO", "BE"],
            "fuzzy": True,
            "case_insensitive": True
        })
```

---

## Deployment Plan

### Local Development

**Setup:**
```bash
# 1. Clone and setup
cd ~/src/projects/vanikeys
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# 2. Start services
docker-compose up -d postgres redis

# 3. Run migrations
alembic upgrade head

# 4. Start dev server
python -m vanikeys.web.app

# 5. Start worker (separate terminal)
python -m vanikeys.workers.guaranteed_worker
```

### Production Deployment (tia-stickers)

**Architecture:**
```
tia-proxy (164.90.128.28) - nginx SSL termination
    │
    ├─▶ vanikeys.com → tia-stickers:8000 (web)
    └─▶ api.vanikeys.com → tia-stickers:8000 (API)

tia-stickers (165.227.98.17)
    ├─▶ vanikeys-web (Podman container, port 8000)
    ├─▶ vanikeys-worker (Podman container)
    ├─▶ postgres (Podman container)
    └─▶ redis (Podman container)
```

**Deployment Steps:**

1. **Build containers**:
```bash
# Web
podman build -f Containerfile.web -t vanikeys-web:latest .

# Worker
podman build -f Containerfile.worker -t vanikeys-worker:latest .
```

2. **Deploy to tia-stickers**:
```bash
# Copy to server
rsync -avz . tia-stickers:/opt/vanikeys/

# SSH to server
ssh tia-stickers

# Start services
cd /opt/vanikeys
./deploy.sh
```

3. **Configure nginx** (on tia-proxy):
```nginx
# /etc/nginx/sites-available/vanikeys.com
server {
    listen 443 ssl http2;
    server_name vanikeys.com www.vanikeys.com;

    ssl_certificate /etc/letsencrypt/live/vanikeys.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/vanikeys.com/privkey.pem;

    location / {
        proxy_pass http://165.227.98.17:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

4. **Setup systemd services**:
```bash
# Copy service files
sudo cp systemd/vanikeys-web.service /etc/systemd/system/
sudo cp systemd/vanikeys-worker.service /etc/systemd/system/

# Enable and start
sudo systemctl enable vanikeys-web vanikeys-worker
sudo systemctl start vanikeys-web vanikeys-worker
```

---

## Success Metrics

### Week 1-2 Success Criteria
- [ ] Multi-substring matcher passes all unit tests
- [ ] Probability calculations match manual verification
- [ ] VaniPull engine executes pulls correctly
- [ ] Database schema created and migrations work

### Week 3-4 Success Criteria
- [ ] Pattern submission form works
- [ ] Odds display shows accurate probabilities
- [ ] Pull animation executes smoothly
- [ ] Results display shows all match data

### Week 5-6 Success Criteria
- [ ] Token purchase completes successfully
- [ ] Guaranteed mode delivers exact matches
- [ ] All pages mobile-responsive
- [ ] Production deployment successful

### Launch Success Criteria (Week 6)
- [ ] 100% uptime during launch day
- [ ] All features functional in production
- [ ] No critical bugs reported
- [ ] First 10 users successfully complete pulls
- [ ] Payment processing works correctly

### Post-Launch Metrics (Week 7-8)
- Target: 100 registered users
- Target: 10 paying users
- Target: $100 revenue
- Target: 70% 7-day retention
- Target: 0 security incidents

---

## Risk Mitigation

### Technical Risks

**Risk**: Stripe integration issues
**Mitigation**: Use Stripe test mode extensively, implement robust error handling, have manual token crediting backup

**Risk**: Background workers crash
**Mitigation**: Implement worker health checks, automatic restart (systemd), job retry logic

**Risk**: Database performance under load
**Mitigation**: Add indexes on hot columns, implement connection pooling, query optimization

**Risk**: Redis queue backup
**Mitigation**: Monitor queue depth, scale workers horizontally, implement queue size alerts

### Business Risks

**Risk**: Low user adoption
**Mitigation**: Free daily pulls, referral system, social media marketing

**Risk**: Regulatory concerns (gambling)
**Mitigation**: Clear ToS stating "virtual currency for service", no cash-out, 18+ age gate

**Risk**: Abuse (botting, fraud)
**Mitigation**: Rate limiting, CAPTCHA on registration, fraud detection (unusual patterns)

---

## Next Steps

### Immediate Actions (This Week)

1. **Setup Development Environment**
   ```bash
   cd ~/src/projects/vanikeys
   docker-compose up -d
   ```

2. **Start Week 1 Tasks**
   - Begin multi-substring matcher implementation
   - Review probability calculation formulas
   - Setup test framework

3. **Confirm Technical Decisions**
   - FastHTML vs Flask/Django? (Recommendation: FastHTML)
   - PostgreSQL vs SQLite? (Recommendation: PostgreSQL for production-readiness)
   - Podman vs Docker? (Recommendation: Podman to match TIA infrastructure)

### Questions to Resolve

- [ ] Domain name: vanikeys.com available? (Need to check/purchase)
- [ ] Stripe account: Existing or create new?
- [ ] Server resources: tia-stickers sufficient or need new VPS?
- [ ] Design assets: Need logo, color scheme, branding?

---

## Conclusion

This plan provides a clear 6-week roadmap to transform VaniKeys into a gamified web service. The phased approach allows for:

- **Incremental validation** (test each component before moving forward)
- **Parallel work** (frontend can develop while backend finalizes)
- **Risk mitigation** (identify issues early in dev environment)
- **Clear milestones** (weekly demos/check-ins)

**Ready to begin Week 1 implementation? Let's build this! 🚀**

---

**Document Version**: 1.0
**Last Updated**: 2025-11-17
**Status**: Ready for Implementation
**Estimated Effort**: 6 weeks (1 full-time developer)
