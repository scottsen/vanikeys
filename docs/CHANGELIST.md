# VaniKeys Phase 2: Complete Changelist

**Version**: 1.0
**Date**: 2025-11-17
**Purpose**: Detailed inventory of all files to create/modify for Phase 2 gamification

---

## Summary

**Total Files**: 62 files
- **New**: 56 files (~8,500 lines of code)
- **Modified**: 6 files
- **Estimated Total Code**: ~10,000 lines (including tests)

---

## Table of Contents

- [New Files by Category](#new-files-by-category)
- [Files to Modify](#files-to-modify)
- [Detailed File Descriptions](#detailed-file-descriptions)
- [Implementation Order](#implementation-order)

---

## New Files by Category

### Backend Core (11 files, ~2,500 LOC)

```
src/vanikeys/matchers/multi_substring.py         [NEW] 250 LOC
src/vanikeys/core/probability.py                 [NEW] 300 LOC
src/vanikeys/engine/__init__.py                  [NEW] 10 LOC
src/vanikeys/engine/vanipull.py                  [NEW] 350 LOC
src/vanikeys/engine/guaranteed.py                [NEW] 200 LOC
src/vanikeys/economy/__init__.py                 [NEW] 10 LOC
src/vanikeys/economy/tokens.py                   [NEW] 250 LOC
src/vanikeys/db/__init__.py                      [NEW] 20 LOC
src/vanikeys/db/base.py                          [NEW] 80 LOC
src/vanikeys/db/models.py                        [NEW] 400 LOC
src/vanikeys/payments/__init__.py                [NEW] 10 LOC
src/vanikeys/payments/stripe_client.py           [NEW] 300 LOC
src/vanikeys/workers/__init__.py                 [NEW] 10 LOC
src/vanikeys/workers/guaranteed_worker.py        [NEW] 320 LOC
```

### Web Frontend (16 files, ~2,800 LOC)

```
src/vanikeys/web/__init__.py                     [NEW] 20 LOC
src/vanikeys/web/app.py                          [NEW] 400 LOC
src/vanikeys/web/auth.py                         [NEW] 200 LOC
src/vanikeys/web/config.py                       [NEW] 80 LOC
src/vanikeys/web/components/__init__.py          [NEW] 10 LOC
src/vanikeys/web/components/layout.py            [NEW] 150 LOC
src/vanikeys/web/components/pattern_form.py      [NEW] 250 LOC
src/vanikeys/web/components/odds_display.py      [NEW] 300 LOC
src/vanikeys/web/components/pull_animation.py    [NEW] 200 LOC
src/vanikeys/web/components/results_display.py   [NEW] 350 LOC
src/vanikeys/web/pages/__init__.py               [NEW] 10 LOC
src/vanikeys/web/pages/landing.py                [NEW] 250 LOC
src/vanikeys/web/pages/app_page.py               [NEW] 300 LOC
src/vanikeys/web/pages/pricing.py                [NEW] 200 LOC
src/vanikeys/web/pages/history.py                [NEW] 250 LOC
src/vanikeys/web/pages/how_it_works.py           [NEW] 180 LOC
src/vanikeys/web/static/css/style.css            [NEW] 500 LOC
src/vanikeys/web/static/js/app.js                [NEW] 350 LOC
```

### Tests (18 files, ~2,200 LOC)

```
tests/unit/test_multi_substring_matcher.py       [NEW] 200 LOC
tests/unit/test_probability_calculator.py        [NEW] 150 LOC
tests/unit/test_vanipull_engine.py               [NEW] 180 LOC
tests/unit/test_token_economy.py                 [NEW] 120 LOC
tests/unit/test_guaranteed_mode.py               [NEW] 150 LOC
tests/unit/test_stripe_client.py                 [NEW] 100 LOC
tests/integration/test_pull_flow.py              [NEW] 250 LOC
tests/integration/test_payment_flow.py           [NEW] 200 LOC
tests/integration/test_guaranteed_flow.py        [NEW] 180 LOC
tests/integration/test_web_app.py                [NEW] 220 LOC
tests/fixtures/__init__.py                       [NEW] 10 LOC
tests/fixtures/database.py                       [NEW] 100 LOC
tests/fixtures/users.py                          [NEW] 80 LOC
tests/fixtures/patterns.py                       [NEW] 60 LOC
tests/conftest.py                                [NEW] 120 LOC
tests/load/locustfile.py                         [NEW] 150 LOC
tests/e2e/test_user_journey.py                   [NEW] 250 LOC
```

### Configuration & Infrastructure (11 files, ~800 LOC)

```
.env.example                                     [NEW] 40 LOC
alembic.ini                                      [NEW] 100 LOC
alembic/env.py                                   [NEW] 80 LOC
alembic/versions/001_initial_schema.py           [NEW] 150 LOC
docker-compose.yml                               [NEW] 80 LOC
Containerfile.web                                [NEW] 40 LOC
Containerfile.worker                             [NEW] 35 LOC
systemd/vanikeys-web.service                     [NEW] 30 LOC
systemd/vanikeys-worker.service                  [NEW] 30 LOC
nginx/vanikeys.conf                              [NEW] 60 LOC
scripts/deploy.sh                                [NEW] 120 LOC
scripts/db-backup.sh                             [NEW] 40 LOC
```

### Documentation (5 files, ~500 LOC)

```
docs/API.md                                      [NEW] 600 LOC (markdown)
docs/DEPLOYMENT.md                               [NEW] 400 LOC (markdown)
docs/DEVELOPMENT.md                              [NEW] 350 LOC (markdown)
docs/TESTING.md                                  [NEW] 250 LOC (markdown)
```

---

## Files to Modify

### Existing Files (6 files)

```
src/vanikeys/__init__.py                         [MODIFY] +20 LOC
src/vanikeys/cli/main.py                         [MODIFY] +150 LOC
pyproject.toml                                   [MODIFY] +40 LOC
README.md                                        [MODIFY] Already updated ✅
requirements.txt                                 [MODIFY] Regenerate
.gitignore                                       [MODIFY] +15 LOC
```

---

## Detailed File Descriptions

### Week 1: Core Backend

#### `src/vanikeys/matchers/multi_substring.py` [NEW] 250 LOC

**Purpose**: Multi-substring pattern matching with fuzzy rules

**Key Classes/Functions**:
```python
class MultiSubstringMatcher:
    """Match multiple substrings sequentially with fuzzy matching."""

    def __init__(self, substrings, fuzzy=False, case_insensitive=True, sequential=True)
    def match(self, text: str) -> MatchResult
    def _build_fuzzy_patterns(self)
    def _build_pattern(self, substring: str) -> str
    def _find_bonus_patterns(self, text: str) -> List[str]

@dataclass
class MatchResult:
    score: float           # 0.0 to 1.0
    matches: List[Match]   # Matched substrings
    missing: List[str]     # Missing substrings
    bonus: List[str]       # Bonus patterns found

@dataclass
class Match:
    substring: str
    position: int
    matched_text: str
    exact: bool
```

**Dependencies**: `re`, `dataclasses`, `typing`

**Test Coverage Target**: 95%

---

#### `src/vanikeys/core/probability.py` [NEW] 300 LOC

**Purpose**: Calculate probabilities for pattern matching

**Key Classes/Functions**:
```python
class ProbabilityCalculator:
    """Calculate odds for multi-substring patterns."""

    def calculate_odds(self, substrings, fuzzy=False, case_insensitive=True) -> ProbabilityEstimate
    def _calculate_fuzzy_factor(self, substring: str) -> float
    def _calculate_sequential_probability(self, substring_probs) -> float
    def _calculate_partial_probability(self, substring_probs, k: int) -> float

@dataclass
class ProbabilityEstimate:
    exact_match_odds: float              # e.g., 4,234,567,890
    exact_match_probability: float       # e.g., 0.000000024%
    partial_match_odds: Dict[int, float] # {3: 421356, 2: 17576, 1: 68}
    expected_pulls: Dict[str, int]       # {'exact': 4234567890, '3/4': 421356}
```

**Dependencies**: `numpy`, `scipy.special` (for combinations), `dataclasses`

**Test Coverage Target**: 90%

---

### Week 2: VaniPull Engine + Database

#### `src/vanikeys/db/models.py` [NEW] 400 LOC

**Purpose**: SQLAlchemy ORM models

**Key Models**:
```python
class User(Base):
    __tablename__ = "users"
    id: UUID
    email: str
    username: str
    password_hash: str
    token_balance: int
    free_pulls_today: int
    free_pulls_reset_at: datetime
    subscription_tier: str
    subscription_expires_at: datetime
    created_at: datetime
    updated_at: datetime

class Pull(Base):
    __tablename__ = "pulls"
    id: UUID
    user_id: UUID
    pattern: str
    pattern_config: dict  # JSONB
    result_key: str
    match_score: float
    matches: dict  # JSONB
    missing: dict  # JSONB
    bonus: dict  # JSONB
    is_win: bool
    tokens_spent: int
    pull_number: int
    created_at: datetime

class Transaction(Base):
    __tablename__ = "transactions"
    id: UUID
    user_id: UUID
    type: str  # purchase, pull, refund
    amount: int
    balance_before: int
    balance_after: int
    payment_intent_id: str
    metadata: dict  # JSONB
    created_at: datetime

class Job(Base):
    __tablename__ = "jobs"
    id: UUID
    user_id: UUID
    pattern: str
    pattern_config: dict
    status: str  # queued, running, completed, failed
    tokens_paid: int
    attempts: int
    result_key: str
    match_result: dict
    started_at: datetime
    completed_at: datetime
    created_at: datetime
```

**Dependencies**: `sqlalchemy`, `uuid`, `datetime`

---

#### `src/vanikeys/engine/vanipull.py` [NEW] 350 LOC

**Purpose**: Core pull execution engine

**Key Classes/Functions**:
```python
class VaniPullEngine:
    """Execute gacha-style pulls."""

    def __init__(self, generator, matcher, mode="gacha")
    def pull(self, user_id: str) -> PullResult
    def _check_tokens(self, user_id: str, amount: int = None) -> bool
    def _deduct_tokens(self, user_id: str, amount: int = None)
    def _record_pull(self, user_id, key, match_result)
    def _check_win_condition(self, match_result) -> bool
    def _get_pull_count(self, user_id: str) -> int
    def _get_token_balance(self, user_id: str) -> int

@dataclass
class PullResult:
    key: KeyPair
    match_result: MatchResult
    is_win: bool
    pull_number: int
    tokens_remaining: int

    def to_ui_dict(self) -> dict
```

**Dependencies**: `vanikeys.generators`, `vanikeys.matchers`, `vanikeys.db`

---

#### `src/vanikeys/economy/tokens.py` [NEW] 250 LOC

**Purpose**: Token balance and transaction management

**Key Functions**:
```python
def get_token_balance(user_id: UUID) -> int
def credit_tokens(user_id: UUID, amount: int, reason: str, metadata: dict = None) -> Transaction
def debit_tokens(user_id: UUID, amount: int, reason: str, metadata: dict = None) -> Transaction
def get_transaction_history(user_id: UUID, limit: int = 50) -> List[Transaction]
def check_free_pulls(user_id: UUID) -> int
def reset_free_pulls(user_id: UUID)
def get_token_cost_for_pattern(pattern_difficulty: str) -> int

# Token pricing tiers
TOKEN_PACKAGES = {
    "starter": {"tokens": 100, "price": 99},    # $0.99
    "popular": {"tokens": 500, "price": 399},   # $3.99
    "power": {"tokens": 2500, "price": 1499},   # $14.99
    "whale": {"tokens": 10000, "price": 4999},  # $49.99
}
```

**Dependencies**: `vanikeys.db.models`, `sqlalchemy`, `uuid`

---

### Week 3: FastHTML Frontend

#### `src/vanikeys/web/app.py` [NEW] 400 LOC

**Purpose**: Main FastHTML application setup

**Key Structure**:
```python
from fasthtml.common import *
from vanikeys.web import auth, pages, components

app, rt = fast_app(
    db_file="vanikeys.db",
    live=True,
    hdrs=(
        Script(src="https://unpkg.com/htmx.org@1.9.10"),
        Link(rel="stylesheet", href="/static/css/style.css"),
    )
)

# Middleware
@app.middleware("http")
async def auth_middleware(request, call_next):
    # Check JWT, populate request.state.user
    pass

# Routes
@rt("/")
def get():
    return pages.landing()

@rt("/app")
def get(request):
    if not request.state.user:
        return Redirect("/login")
    return pages.app_page(request.state.user)

@rt("/api/pulls/execute", methods=["POST"])
async def execute_pull(request):
    # Execute pull and return result
    pass

# ... more routes
```

**Dependencies**: `fasthtml`, `vanikeys.web.auth`, `vanikeys.web.pages`, `vanikeys.web.components`

---

#### `src/vanikeys/web/components/pattern_form.py` [NEW] 250 LOC

**Purpose**: Pattern input form component

**Key Functions**:
```python
def PatternForm(pattern: str = "", config: dict = None):
    """
    Render pattern submission form.

    Returns FastHTML Form component with:
    - Pattern input (space-separated substrings)
    - Fuzzy matching toggle
    - Case-insensitive toggle
    - Sequential matching toggle
    - "Calculate Odds" button
    """
    return Form(
        Div(
            Label("Enter Pattern", for_="pattern"),
            Input(
                id="pattern",
                name="pattern",
                placeholder="GO BE AWE SOME",
                value=pattern,
                hx_post="/api/patterns/validate",
                hx_trigger="keyup changed delay:500ms",
                hx_target="#validation-feedback",
            ),
            Div(id="validation-feedback"),
        ),
        Fieldset(
            Legend("Options"),
            Label(
                Input(type="checkbox", name="fuzzy", checked=True),
                "Fuzzy matching (0→O, 1→I, etc)",
            ),
            Label(
                Input(type="checkbox", name="case_insensitive", checked=True),
                "Case insensitive",
            ),
        ),
        Button(
            "Calculate Odds",
            type="submit",
            hx_post="/api/patterns/estimate",
            hx_target="#odds-display",
        ),
        id="pattern-form",
    )
```

**Dependencies**: `fasthtml.common`

---

#### `src/vanikeys/web/components/odds_display.py` [NEW] 300 LOC

**Purpose**: Display probability calculations

**Key Functions**:
```python
def OddsDisplay(estimate: ProbabilityEstimate, pattern: str):
    """
    Render odds display with:
    - Exact match probability
    - Partial match probabilities (3/4, 2/4, 1/4)
    - Token cost per pull
    - Expected pulls for each scenario
    - Gacha vs Guaranteed comparison
    """
    return Div(
        H2("🎰 Your VaniPull Odds 🎰"),
        Div(
            H3(f"Pattern: {pattern}"),
            P(f"Exact Match: 1 in {estimate.exact_match_odds:,.0f}"),
            P(f"Probability: {estimate.exact_match_probability:.9f}%"),
            # ... more stats
        ),
        Div(
            H3("💰 Your Options"),
            Div(
                H4("🎲 Gacha Mode"),
                P("100 tokens per pull"),
                P("No guarantee"),
                Button("Try Your Luck", hx_post="/api/pulls/execute"),
                cls="option-card gacha",
            ),
            Div(
                H4("✅ Guaranteed Mode"),
                P(f"{calculate_guaranteed_cost(estimate):,} tokens"),
                P("Perfect match guaranteed"),
                Button("Buy Now", hx_post="/api/jobs/create"),
                cls="option-card guaranteed",
            ),
            cls="options-container",
        ),
        id="odds-display",
        cls="odds-container",
    )
```

**Dependencies**: `fasthtml.common`, `vanikeys.core.probability`

---

### Week 4: Pull Animation + Results

#### `src/vanikeys/web/components/pull_animation.py` [NEW] 200 LOC

**Purpose**: Animated pull execution UI

**Key Functions**:
```python
def PullAnimation(pull_id: str = None):
    """
    Slot machine-style animation during pull execution.

    Phases:
    1. Loading animation (spinning)
    2. Key generation progress bar
    3. Pattern matching indicator
    4. Reveal animation
    """
    if pull_id:
        # Pull in progress, show status
        return Div(
            H2("🎰 PULLING... 🎰"),
            Div(
                Progress(value=50, max=100),
                P("Generating key..."),
                P("Checking patterns..."),
            ),
            # Poll for result
            hx_get=f"/api/pulls/{pull_id}/status",
            hx_trigger="every 500ms",
            hx_swap="outerHTML",
            id="pull-animation",
        )
    else:
        return Div(id="pull-animation")  # Empty state

def PullComplete(result: PullResult):
    """Transition to result display."""
    return ResultsDisplay(result)
```

**Dependencies**: `fasthtml.common`, `vanikeys.engine.vanipull`

---

#### `src/vanikeys/web/components/results_display.py` [NEW] 350 LOC

**Purpose**: "What You Got" results display

**Key Functions**:
```python
def ResultsDisplay(result: PullResult):
    """
    Display pull results with:
    - Generated key (with copy button)
    - Match score visualization (stars)
    - Matched substrings (with positions)
    - Missing substrings
    - Bonus patterns found
    - "Kind of what you wanted?" message
    - Action buttons (Pull Again, Keep Key, Share)
    """
    match_result = result.match_result
    percentage = match_result.score * 100
    stars = "⭐" * int(match_result.score * 4) + "☆" * (4 - int(match_result.score * 4))

    return Div(
        H2("🎉 YOUR VANIPULL RESULT 🎉" if result.is_win else "YOUR RESULT"),
        Div(
            P(f"Key: {result.key.to_did()}"),
            Button("Copy", onclick=f"navigator.clipboard.writeText('{result.key.to_did()}')"),
            cls="key-display",
        ),
        Hr(),
        H3("WHAT YOU ASKED FOR:"),
        P(f"Match: {len(match_result.matches)}/{len(match_result.matches) + len(match_result.missing)} ({percentage:.0f}%) {stars}"),
        Ul(
            *[
                Li(f"✅ {m.substring} - Position {m.position}")
                for m in match_result.matches
            ],
            *[
                Li(f"❌ {missing} - Not found")
                for missing in match_result.missing
            ],
        ),
        Hr() if match_result.bonus else None,
        (
            Div(
                H3("BONUS FINDS:"),
                P("We also found these patterns:"),
                Ul(*[Li(f"🎲 {bonus}") for bonus in match_result.bonus]),
            )
            if match_result.bonus
            else None
        ),
        P("Kind of what you wanted? 🤔", cls="playful-copy"),
        Hr(),
        Div(
            Button("Pull Again (100 tokens)", hx_post="/api/pulls/execute"),
            Button("Keep This Key & Export", hx_get=f"/api/pulls/{result.key.to_did()}/export"),
            Button("Share Result", onclick="share()"),
            cls="action-buttons",
        ),
        id="results-display",
        cls="results-container",
    )
```

**Dependencies**: `fasthtml.common`, `vanikeys.engine.vanipull`

---

### Week 5: Payments + Guaranteed Mode

#### `src/vanikeys/payments/stripe_client.py` [NEW] 300 LOC

**Purpose**: Stripe payment integration

**Key Functions**:
```python
import stripe
from vanikeys.economy import tokens

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

def create_payment_intent(user_id: UUID, package: str) -> stripe.PaymentIntent:
    """Create Stripe PaymentIntent for token purchase."""
    package_info = tokens.TOKEN_PACKAGES[package]
    return stripe.PaymentIntent.create(
        amount=package_info["price"],
        currency="usd",
        metadata={
            "user_id": str(user_id),
            "package": package,
            "tokens": package_info["tokens"],
        },
    )

def handle_webhook(payload: bytes, sig_header: str):
    """Handle Stripe webhook events."""
    event = stripe.Webhook.construct_event(
        payload, sig_header, os.getenv("STRIPE_WEBHOOK_SECRET")
    )

    if event["type"] == "payment_intent.succeeded":
        payment_intent = event["data"]["object"]
        user_id = UUID(payment_intent["metadata"]["user_id"])
        token_amount = int(payment_intent["metadata"]["tokens"])

        # Credit tokens
        tokens.credit_tokens(
            user_id=user_id,
            amount=token_amount,
            reason="purchase",
            metadata={"payment_intent_id": payment_intent["id"]},
        )

def get_checkout_session(payment_intent_id: str) -> dict:
    """Get Stripe Checkout session info."""
    return stripe.PaymentIntent.retrieve(payment_intent_id)
```

**Dependencies**: `stripe`, `vanikeys.economy.tokens`, `os`, `uuid`

---

#### `src/vanikeys/engine/guaranteed.py` [NEW] 200 LOC

**Purpose**: Guaranteed mode (background job processing)

**Key Functions**:
```python
import redis
import json

redis_client = redis.from_url(os.getenv("REDIS_URL"))

def create_guaranteed_job(user_id: UUID, pattern: dict, tokens_paid: int) -> UUID:
    """Create guaranteed generation job."""
    job = Job(
        user_id=user_id,
        pattern=json.dumps(pattern),
        pattern_config=pattern.get("config", {}),
        status="queued",
        tokens_paid=tokens_paid,
    )
    db.session.add(job)
    db.session.commit()

    # Queue job in Redis
    redis_client.lpush("guaranteed_jobs", str(job.id))

    return job.id

def get_job_status(job_id: UUID) -> Job:
    """Get job status from database."""
    return db.session.query(Job).filter(Job.id == job_id).first()

def update_job_status(job_id: UUID, status: str, **kwargs):
    """Update job status."""
    job = db.session.query(Job).filter(Job.id == job_id).first()
    job.status = status
    for key, value in kwargs.items():
        setattr(job, key, value)
    db.session.commit()

def calculate_guaranteed_cost(estimate: ProbabilityEstimate) -> int:
    """Calculate guaranteed mode cost (15% premium)."""
    base_cost = estimate.expected_pulls["exact"] * 100  # 100 tokens per pull
    premium = int(base_cost * 0.15)
    return base_cost + premium
```

**Dependencies**: `redis`, `vanikeys.db.models`, `json`, `uuid`

---

#### `src/vanikeys/workers/guaranteed_worker.py` [NEW] 320 LOC

**Purpose**: Background worker for guaranteed jobs

**Key Structure**:
```python
import redis
import time
from vanikeys.engine.guaranteed import get_job_status, update_job_status
from vanikeys.engine.vanipull import VaniPullEngine
from vanikeys.matchers.multi_substring import MultiSubstringMatcher
from vanikeys.generators.ed25519 import Ed25519Generator

redis_client = redis.from_url(os.getenv("REDIS_URL"))

def worker_loop():
    """Main worker loop - process jobs from queue."""
    print("🔧 Guaranteed worker started")

    while True:
        # Block until job available
        job_id = redis_client.brpop("guaranteed_jobs", timeout=5)

        if job_id:
            job_id = UUID(job_id[1].decode())
            process_job(job_id)

def process_job(job_id: UUID):
    """Process a single guaranteed job."""
    print(f"📦 Processing job {job_id}")

    job = get_job_status(job_id)
    if job.status != "queued":
        print(f"⚠️  Job {job_id} already processed")
        return

    # Update status to running
    update_job_status(job_id, "running", started_at=datetime.now())

    # Parse pattern
    pattern = json.loads(job.pattern)
    matcher = MultiSubstringMatcher(
        substrings=pattern["substrings"],
        fuzzy=pattern["config"].get("fuzzy", False),
        case_insensitive=pattern["config"].get("case_insensitive", True),
    )

    # Generate until exact match
    generator = Ed25519Generator()
    attempts = 0
    max_attempts = 10_000_000  # Safety limit

    while attempts < max_attempts:
        attempts += 1

        # Generate key
        key = generator.generate()

        # Check match
        match_result = matcher.match(key.public_key_base58)

        if match_result.score == 1.0:
            # Perfect match! Job complete
            print(f"✅ Job {job_id} complete after {attempts} attempts")
            update_job_status(
                job_id,
                "completed",
                attempts=attempts,
                result_key=key.to_did(),
                match_result=match_result.__dict__,
                completed_at=datetime.now(),
            )
            return

        # Log progress every 10K attempts
        if attempts % 10_000 == 0:
            print(f"🔄 Job {job_id}: {attempts:,} attempts...")

    # Max attempts reached without match (should be extremely rare)
    print(f"❌ Job {job_id} failed after {attempts} attempts")
    update_job_status(job_id, "failed", attempts=attempts)

if __name__ == "__main__":
    worker_loop()
```

**Dependencies**: `redis`, `vanikeys.engine`, `vanikeys.matchers`, `vanikeys.generators`

---

### Configuration Files

#### `.env.example` [NEW] 40 LOC

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
BASE_URL=http://localhost:8000

# Token Pricing (cents)
TOKEN_PRICE_STARTER=99
TOKEN_PRICE_POPULAR=399
TOKEN_PRICE_POWER=1499
TOKEN_PRICE_WHALE=4999

# Pull Costs (tokens)
PULL_COST_EASY=1
PULL_COST_MEDIUM=10
PULL_COST_HARD=100
PULL_COST_INSANE=1000

# Free Pulls
FREE_PULLS_PER_DAY=3
```

---

#### `docker-compose.yml` [NEW] 80 LOC

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_USER: vanikeys
      POSTGRES_PASSWORD: password
      POSTGRES_DB: vanikeys
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  web:
    build:
      context: .
      dockerfile: Containerfile.web
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis
    environment:
      DATABASE_URL: postgresql://vanikeys:password@postgres:5432/vanikeys
      REDIS_URL: redis://redis:6379/0
    volumes:
      - ./src:/app/src

  worker:
    build:
      context: .
      dockerfile: Containerfile.worker
    depends_on:
      - postgres
      - redis
    environment:
      DATABASE_URL: postgresql://vanikeys:password@postgres:5432/vanikeys
      REDIS_URL: redis://redis:6379/0
    volumes:
      - ./src:/app/src

volumes:
  postgres_data:
  redis_data:
```

---

## Implementation Order

### Week 1 Priority Order

1. `src/vanikeys/matchers/multi_substring.py` ⭐ CRITICAL
2. `tests/unit/test_multi_substring_matcher.py`
3. `src/vanikeys/core/probability.py` ⭐ CRITICAL
4. `tests/unit/test_probability_calculator.py`
5. `src/vanikeys/cli/main.py` (modification - add estimate-multi command)

### Week 2 Priority Order

1. `.env.example` ⭐ CRITICAL
2. `docker-compose.yml`
3. `src/vanikeys/db/base.py`
4. `src/vanikeys/db/models.py` ⭐ CRITICAL
5. `alembic.ini` and migrations
6. `src/vanikeys/economy/tokens.py` ⭐ CRITICAL
7. `src/vanikeys/engine/vanipull.py` ⭐ CRITICAL
8. `tests/unit/test_vanipull_engine.py`
9. `tests/integration/test_pull_flow.py`

### Week 3 Priority Order

1. `src/vanikeys/web/app.py` ⭐ CRITICAL
2. `src/vanikeys/web/auth.py`
3. `src/vanikeys/web/components/layout.py`
4. `src/vanikeys/web/components/pattern_form.py` ⭐ CRITICAL
5. `src/vanikeys/web/components/odds_display.py` ⭐ CRITICAL
6. `src/vanikeys/web/pages/landing.py`
7. `src/vanikeys/web/pages/app_page.py`
8. `src/vanikeys/web/static/css/style.css`

### Week 4 Priority Order

1. `src/vanikeys/web/components/pull_animation.py` ⭐ CRITICAL
2. `src/vanikeys/web/components/results_display.py` ⭐ CRITICAL
3. `src/vanikeys/web/pages/history.py`
4. `src/vanikeys/web/static/js/app.js`
5. `tests/integration/test_web_app.py`

### Week 5 Priority Order

1. `src/vanikeys/payments/stripe_client.py` ⭐ CRITICAL
2. `src/vanikeys/web/pages/pricing.py`
3. `src/vanikeys/engine/guaranteed.py` ⭐ CRITICAL
4. `src/vanikeys/workers/guaranteed_worker.py` ⭐ CRITICAL
5. `tests/integration/test_payment_flow.py`
6. `tests/integration/test_guaranteed_flow.py`

### Week 6 Priority Order

1. `Containerfile.web` ⭐ CRITICAL
2. `Containerfile.worker` ⭐ CRITICAL
3. `systemd/vanikeys-web.service`
4. `systemd/vanikeys-worker.service`
5. `nginx/vanikeys.conf`
6. `scripts/deploy.sh`
7. `docs/API.md`
8. `docs/DEPLOYMENT.md`
9. `tests/e2e/test_user_journey.py`
10. `tests/load/locustfile.py`

---

## Modifications to Existing Files

### `src/vanikeys/__init__.py` [MODIFY]

**Add exports:**
```python
# Existing
from vanikeys.core import *
from vanikeys.generators import *
from vanikeys.matchers import *

# New exports (add these)
from vanikeys.engine import VaniPullEngine
from vanikeys.economy import tokens
from vanikeys.payments import stripe_client

__version__ = "0.2.0"  # Update version (was 0.1.0)
```

---

### `src/vanikeys/cli/main.py` [MODIFY]

**Add new command:**
```python
@cli.command()
@click.argument("pattern")
@click.option("--fuzzy/--no-fuzzy", default=False)
@click.option("--case-insensitive/--case-sensitive", default=True)
def estimate_multi(pattern: str, fuzzy: bool, case_insensitive: bool):
    """
    Estimate probability for multi-substring pattern.

    Example: vanikeys estimate-multi "GO BE AWE SOME" --fuzzy
    """
    from vanikeys.core.probability import ProbabilityCalculator

    substrings = pattern.split()
    calc = ProbabilityCalculator()
    estimate = calc.calculate_odds(substrings, fuzzy, case_insensitive)

    console.print(f"\n[bold]Pattern:[/bold] {pattern}")
    console.print(f"[bold]Substrings:[/bold] {len(substrings)}\n")

    console.print("[bold cyan]Exact Match:[/bold cyan]")
    console.print(f"  Odds: 1 in {estimate.exact_match_odds:,.0f}")
    console.print(f"  Probability: {estimate.exact_match_probability:.9f}%")
    console.print(f"  Expected pulls: {estimate.expected_pulls['exact']:,}\n")

    for k in range(len(substrings) - 1, 0, -1):
        key = f"{k}/{len(substrings)}"
        if key in estimate.expected_pulls:
            console.print(f"[bold green]At Least {key} Matches:[/bold green]")
            console.print(f"  Expected pulls: {estimate.expected_pulls[key]:,}\n")
```

---

### `pyproject.toml` [MODIFY]

**Add dependencies:**
```toml
[project]
name = "vanikeys"
version = "0.2.0"  # Update version
dependencies = [
    # Existing
    "cryptography>=42.0.0",
    "click>=8.1.7",
    "rich>=13.7.0",
    "multiformats>=0.3.1",

    # New for Phase 2
    "fasthtml>=0.4.0",
    "python-fasthtml>=0.4.0",
    "sqlalchemy>=2.0.23",
    "alembic>=1.13.0",
    "redis>=5.0.1",
    "stripe>=7.7.0",
    "pydantic>=2.5.2",
    "pydantic-settings>=2.1.0",
    "passlib[bcrypt]>=1.7.4",
    "python-jose[cryptography]>=3.3.0",
    "httpx>=0.25.2",
    "pytest>=7.4.3",
    "pytest-asyncio>=0.23.2",
    "faker>=21.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest-cov>=4.1.0",
    "black>=23.12.0",
    "ruff>=0.1.9",
    "mypy>=1.7.1",
    "locust>=2.20.0",
]
```

---

### `.gitignore` [MODIFY]

**Add:**
```
# Environment
.env
.env.local

# Database
*.db
vanikeys.db

# IDE
.vscode/
.idea/

# Python
__pycache__/
*.pyc
.pytest_cache/
.coverage
htmlcov/

# Containers
.containerfiles/

# Logs
logs/
*.log
```

---

## Summary Statistics

**Total Implementation Effort**:
- **Lines of Code**: ~10,000 LOC (including tests)
- **Files**: 62 files (56 new, 6 modified)
- **Test Coverage Target**: >90%
- **Estimated Time**: 6 weeks (1 developer)

**Breakdown by Type**:
- Backend Python: ~3,800 LOC
- Frontend (FastHTML + CSS + JS): ~3,500 LOC
- Tests: ~2,200 LOC
- Configuration: ~500 LOC

**Critical Path**:
1. Multi-substring matcher (Week 1)
2. VaniPull engine (Week 2)
3. FastHTML app + UI components (Week 3-4)
4. Stripe + Guaranteed mode (Week 5)
5. Deployment (Week 6)

---

**Document Version**: 1.0
**Last Updated**: 2025-11-17
**Status**: Ready for Implementation
