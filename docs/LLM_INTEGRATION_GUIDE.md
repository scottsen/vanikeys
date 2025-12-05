# VaniKeys AI/LLM Integration Guide

**Version**: 1.0
**Date**: 2025-11-17
**Status**: Design & Implementation Ready
**Recommended**: Together.ai for MVP

---

## Executive Summary

Enhance VaniKeys with **AI-powered features** using open-source LLMs at negligible cost (<$50/mo). Key capabilities:

1. **Pattern Suggestions** - AI suggests vanity patterns based on user description
2. **Difficulty Explanations** - Human-friendly explanations of pattern odds
3. **Natural Language Parsing** - Convert "swift golden tiger" → "SWIFT GOLD TIGER"
4. **Pattern Valuation** - AI estimates market value for pattern marketplace
5. **Customer Support** - AI chatbot for common questions

**Cost**: $13-50/mo for 30K-100K requests (using Together.ai or Hugging Face)

---

## Table of Contents

1. [Why Add AI Features](#why-add-ai-features)
2. [Platform Recommendations](#platform-recommendations)
3. [Feature Implementations](#feature-implementations)
4. [Cost Analysis](#cost-analysis)
5. [Integration Guide](#integration-guide)
6. [Advanced Features](#advanced-features)

---

## Why Add AI Features

### The Problem Without AI

**Current UX** (VaniKeys Phase 1):
```
User: "I want a vanity key"
System: "Enter pattern (e.g., ABC 123)"
User: "Uh... what should I put?"
System: [no suggestions]
User: [abandons site]
```

**With AI** (VaniKeys Phase 2+):
```
User: "I'm a Stanford CS student"
AI: "Suggested patterns:
     - STANFORD CS 2025
     - STUDENT SWE 042
     - CARDINAL CODE DEV"
User: "I like STANFORD CS 2025!"
System: "That pattern has 1 in 4.2B odds. That's like
         finding a specific grain of sand on every beach
         in California!"
User: [excited, buys tokens, pulls]
```

### Benefits

1. **Reduced Friction** - Users don't need to think of patterns
2. **Increased Engagement** - AI makes interaction fun
3. **Better Conversions** - Suggestions → higher purchase rate
4. **Educational** - Explains difficulty in relatable terms
5. **Viral Potential** - AI features are shareable/tweetable

---

## Platform Recommendations

### Quick Comparison

| Platform | Best For | Cost (30K req/mo) | Latency | Setup |
|----------|----------|-------------------|---------|-------|
| **Together.ai** ⭐ | Production | $13/mo | <100ms | 5 min |
| **HF (SambaNova)** ⭐ | Cheapest | $9/mo | <100ms | 5 min |
| **Replicate** | Pre-packaged | $22/mo | ~10s | 10 min |
| **Modal + Ollama** | Custom models | $90/mo | ~5-10s | 1 day |

**Recommendation**: **Together.ai** for MVP (best balance of cost, latency, ease)

---

## Feature Implementations

### Feature 1: AI Pattern Suggestions

**User Flow**:
```
1. User enters description: "I'm a university researcher studying quantum physics"
2. AI generates 5 pattern suggestions:
   - QUANTUM PHY RESEARCHER
   - STANFORD PHYSICS 2025
   - QC RESEARCH LAB
   - PROFESSOR QUANTUM SCI
   - PHD PHYSICS STUDENT
3. User picks one or requests more suggestions
4. System shows odds, pricing, and pull options
```

**Implementation (Together.ai)**:
```python
# vanikeys/ai/pattern_suggester.py
from together import Together
import os

class PatternSuggester:
    """AI-powered pattern suggestion engine."""

    def __init__(self):
        self.client = Together(api_key=os.getenv("TOGETHER_API_KEY"))
        self.model = "meta-llama/Llama-3.1-70B-Instruct-Turbo"

    def suggest(
        self,
        description: str,
        count: int = 5,
        max_substrings: int = 4
    ) -> list[dict]:
        """
        Suggest vanity key patterns based on user description.

        Args:
            description: User's description (e.g., "Stanford CS student")
            count: Number of suggestions to generate
            max_substrings: Maximum substrings per pattern

        Returns:
            List of pattern suggestions with metadata
        """

        prompt = f"""You are a vanity key pattern expert. Suggest {count} SHORT,
memorable patterns based on this description.

DESCRIPTION:
{description}

RULES:
1. Each pattern: {max_substrings} substrings max (space-separated)
2. Each substring: 3-6 characters (uppercase letters + numbers only)
3. Patterns should be meaningful and relevant to the description
4. Mix of personal identifiers, roles, organizations, years
5. Creative but not random

EXAMPLES:
- "STANFORD CS 2025" (university + major + year)
- "ACME ENG 042" (company + dept + employee ID)
- "DR SMITH MD" (title + name + credential)

Return ONLY the patterns, one per line, no explanations or numbering."""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.8,  # Higher temp for creativity
        )

        # Parse patterns
        raw_patterns = response.choices[0].message.content.strip().split('\n')
        patterns = []

        for raw in raw_patterns[:count]:
            pattern = raw.strip().strip('"').strip()
            if not pattern:
                continue

            # Validate format
            substrings = pattern.split()
            if len(substrings) <= max_substrings:
                patterns.append({
                    'pattern': pattern,
                    'substrings': substrings,
                    'substring_count': len(substrings)
                })

        return patterns

    def refine(
        self,
        original_pattern: str,
        feedback: str,
        count: int = 3
    ) -> list[dict]:
        """
        Refine a pattern based on user feedback.

        Example:
            original: "STANFORD CS 2025"
            feedback: "Make it shorter and include my name"
            → ["STAN ALICE CS", "ALICE CS 25", "ALICE STANFORD"]
        """

        prompt = f"""Refine this vanity key pattern based on user feedback.

ORIGINAL PATTERN: {original_pattern}
USER FEEDBACK: {feedback}

Generate {count} refined patterns that incorporate the feedback while keeping
the same style and constraints (3-6 char substrings, meaningful, relevant).

Return ONLY the refined patterns, one per line."""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.7
        )

        # Parse
        raw_patterns = response.choices[0].message.content.strip().split('\n')
        return [{'pattern': p.strip()} for p in raw_patterns if p.strip()][:count]
```

**FastHTML Integration**:
```python
# vanikeys/web/routes/ai.py
from fasthtml.common import *
from vanikeys.ai.pattern_suggester import PatternSuggester

suggester = PatternSuggester()

@app.get("/")
def home():
    return Titled("VaniKeys - AI-Powered Vanity Keys",
        Card(
            H2("🤖 Describe Yourself"),
            P("Our AI will suggest perfect vanity patterns for you!"),
            Form(
                Textarea(
                    name="description",
                    placeholder="e.g., 'I'm a Stanford CS student graduating in 2025'",
                    rows=3,
                    cls="w-full"
                ),
                Button(
                    "✨ Get AI Suggestions",
                    type="submit",
                    hx_post="/api/ai/suggest",
                    hx_target="#suggestions",
                    cls="btn-primary"
                )
            ),
            Div(id="suggestions", cls="mt-4")
        )
    )

@app.post("/api/ai/suggest")
async def suggest_patterns(description: str):
    """AI pattern suggestions."""

    if not description or len(description) < 10:
        return Div(
            P("Please provide a more detailed description!", cls="text-red-500")
        )

    # Get AI suggestions
    patterns = suggester.suggest(description, count=5)

    if not patterns:
        return Div(
            P("Couldn't generate patterns. Try a different description!", cls="text-red-500")
        )

    # Return interactive suggestions
    return Div(
        H3("🎯 AI Suggested Patterns:", cls="text-lg font-bold mb-2"),
        *[
            Card(
                Div(
                    P(p['pattern'], cls="text-xl font-mono font-bold"),
                    P(f"{p['substring_count']} substrings", cls="text-sm text-gray-500"),
                    Button(
                        "📊 Check Odds",
                        hx_post="/api/estimate",
                        hx_vals=f'{{"pattern": "{p["pattern"]}"}}',
                        hx_target="#odds",
                        cls="btn-secondary mt-2"
                    ),
                    Button(
                        "🎰 Pull Now!",
                        hx_post="/api/pull/gacha",
                        hx_vals=f'{{"pattern": "{p["pattern"]}"}}',
                        hx_target="#result",
                        cls="btn-primary mt-2 ml-2"
                    )
                ),
                cls="mb-2"
            )
            for p in patterns
        ],
        Div(id="odds", cls="mt-4"),
        Div(id="result", cls="mt-4"),
        Button(
            "🔄 More Suggestions",
            hx_post="/api/ai/suggest",
            hx_vals=f'{{"description": "{description}"}}',
            hx_target="#suggestions",
            cls="btn-outline mt-4"
        )
    )
```

**Cost**:
```
Per request: ~200 tokens
Cost: 200 × $0.88/M = $0.00018 per suggestion

1,000 suggestions/day × 30 = 30,000/month
Cost: 30,000 × $0.00018 = $5.40/month

Negligible!
```

---

### Feature 2: Human-Friendly Difficulty Explanations

**User Flow**:
```
User picks pattern: "GO BE AWE SOME"
System calculates: 1 in 4.2 billion

Without AI:
  "Probability: 0.000000024%"
  [User confused, doesn't understand]

With AI:
  "This is like finding one specific grain of sand on every
   beach in California. You'd need to generate 4.2 billion
   keys on average to find this exact pattern. That's why
   our guaranteed mode exists!"
  [User understands, converts]
```

**Implementation**:
```python
# vanikeys/ai/explainer.py
from together import Together
import os

class DifficultyExplainer:
    """Explain pattern difficulty in human-friendly terms."""

    def __init__(self):
        self.client = Together(api_key=os.getenv("TOGETHER_API_KEY"))
        self.model = "meta-llama/Llama-3.1-70B-Instruct-Turbo"

    def explain(
        self,
        pattern: str,
        probability: float,
        expected_attempts: int
    ) -> str:
        """
        Generate human-friendly explanation of difficulty.

        Args:
            pattern: The pattern (e.g., "GO BE AWE SOME")
            probability: Probability as decimal (e.g., 0.00000002)
            expected_attempts: Expected number of attempts

        Returns:
            Human-friendly explanation string
        """

        odds_ratio = int(1 / probability)

        prompt = f"""Explain the difficulty of finding this vanity key pattern
in simple, relatable, FUN terms that anyone can understand.

PATTERN: {pattern}
ODDS: 1 in {odds_ratio:,}
EXPECTED ATTEMPTS: {expected_attempts:,}

REQUIREMENTS:
1. Use creative analogies (e.g., "finding a needle in X haystacks")
2. Make it relatable to everyday experiences
3. Keep it under 80 words
4. Make it engaging and slightly humorous
5. Don't use technical jargon or percentages
6. End with encouragement or context (why this matters)

EXAMPLES:
- "This is like randomly picking the correct atom from Mount Everest!"
- "Imagine shuffling a deck and getting the same order twice in a row -
   that's easier than this!"
- "You'd have better odds of being struck by lightning... twice...
   in the same day!"

Be creative! Make it memorable!"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.9  # High creativity
        )

        return response.choices[0].message.content.strip()

    def compare_difficulty(
        self,
        pattern1: str,
        prob1: float,
        pattern2: str,
        prob2: float
    ) -> str:
        """
        Compare difficulty of two patterns.

        Example:
            "LAB" (1 in 195K) vs "GO BE AWE SOME" (1 in 4.2B)
            → "Pattern 2 is 21,500× harder - like comparing a city block
               to the entire Earth!"
        """

        ratio = (1/prob2) / (1/prob1)

        prompt = f"""Compare the difficulty of these two vanity key patterns:

PATTERN 1: {pattern1} (1 in {int(1/prob1):,})
PATTERN 2: {pattern2} (1 in {int(1/prob2):,})

Pattern 2 is {ratio:.0f}× harder than Pattern 1.

Explain this difference using a memorable analogy. Keep it under 50 words."""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
            temperature=0.8
        )

        return response.choices[0].message.content.strip()
```

**Integration Example**:
```python
@app.post("/api/estimate")
async def estimate_difficulty(pattern: str):
    """Estimate difficulty with AI explanation."""
    from vanikeys.core.probability import ProbabilityCalculator
    from vanikeys.ai.explainer import DifficultyExplainer

    # Calculate odds
    calc = ProbabilityCalculator()
    estimate = calc.calculate_odds(pattern.split())

    # Get AI explanation
    explainer = DifficultyExplainer()
    explanation = explainer.explain(
        pattern,
        estimate.exact_match_probability,
        estimate.expected_pulls['exact']
    )

    return Card(
        H3("🎯 Pattern Difficulty"),
        Div(
            P(f"Pattern: {pattern}", cls="font-mono text-lg"),
            P(f"Odds: 1 in {estimate.exact_match_odds:,.0f}", cls="text-2xl font-bold"),
            Div(
                P(explanation, cls="text-lg italic"),
                cls="bg-blue-100 p-4 rounded mt-2"
            ),
            Div(
                H4("Your Options:", cls="mt-4 font-bold"),
                Div(
                    P("🎲 Gacha Mode: 100 tokens/pull (gamble)"),
                    P(f"✅ Guaranteed Mode: {estimate.expected_pulls['exact'] * 100 * 1.15:,.0f} tokens (guaranteed)")
                )
            )
        )
    )
```

---

### Feature 3: Natural Language Pattern Parsing

**User Flow**:
```
User types: "make me a key that says swift golden tiger"
AI parses: "SWIFT GOLD TIGER"
System: "Great! Here are your odds..."

Instead of user manually formatting pattern.
```

**Implementation**:
```python
# vanikeys/ai/parser.py
from together import Together
import os

class NLPPatternParser:
    """Parse natural language into vanity key patterns."""

    def __init__(self):
        self.client = Together(api_key=os.getenv("TOGETHER_API_KEY"))
        self.model = "meta-llama/Llama-3.1-70B-Instruct-Turbo"

    def parse(self, natural_language: str) -> str:
        """
        Convert natural language to vanity pattern.

        Examples:
            "make me a key that says swift golden tiger"
            → "SWIFT GOLD TIGER"

            "I want my name alice and the year 2025"
            → "ALICE 2025"

            "something with stanford computer science"
            → "STANFORD CS"
        """

        prompt = f"""Convert this natural language request into a vanity key pattern.

REQUEST: {natural_language}

RULES:
1. Extract key words/concepts
2. Convert to uppercase
3. Use 3-6 characters per word when possible
4. Separate with spaces
5. Return ONLY the pattern, no explanation

EXAMPLES:
Request: "make me a key with swift golden tiger"
Pattern: SWIFT GOLD TIGER

Request: "I want my university stanford and year 2025"
Pattern: STANFORD 2025

Request: "doctor smith cardiology"
Pattern: DR SMITH CARDIO

Now convert the request above:"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=50,
            temperature=0.3  # Low temp for consistent parsing
        )

        return response.choices[0].message.content.strip().upper()
```

**Integration**:
```python
@app.post("/api/ai/parse")
async def parse_natural_language(text: str):
    """Parse natural language into pattern."""
    from vanikeys.ai.parser import NLPPatternParser

    parser = NLPPatternParser()
    pattern = parser.parse(text)

    # Redirect to estimate
    return Div(
        H3(f"📝 Parsed Pattern: {pattern}"),
        Button(
            "Check Odds",
            hx_post="/api/estimate",
            hx_vals=f'{{"pattern": "{pattern}"}}',
            hx_target="#odds"
        )
    )
```

---

### Feature 4: Pattern Marketplace Valuation

**Use Case**: For Pattern Marketplace feature (see `PATTERN_MARKETPLACE_DESIGN.md`)

**Implementation**:
```python
# vanikeys/ai/valuator.py
from together import Together
import os

class PatternValuator:
    """AI-powered pattern valuation for marketplace."""

    def __init__(self):
        self.client = Together(api_key=os.getenv("TOGETHER_API_KEY"))
        self.model = "meta-llama/Llama-3.1-70B-Instruct-Turbo"

    def estimate_value(
        self,
        pattern: str,
        probability: float,
        category: str
    ) -> dict:
        """
        Estimate market value of a vanity pattern.

        Factors:
        - Rarity (probability)
        - Desirability (common name, org, etc.)
        - Category (VIP, common name, org, etc.)
        - Memorability
        """

        prompt = f"""Estimate the market value of this vanity key pattern for
the VaniKeys marketplace.

PATTERN: {pattern}
RARITY: 1 in {int(1/probability):,}
CATEGORY: {category}

Consider:
1. Rarity (how hard to generate)
2. Desirability (is it a common name, org, cool word?)
3. Utility (would people/companies want this?)
4. Memorability (easy to remember?)

Provide:
1. Estimated price range ($X - $Y)
2. Target buyer (who would want this?)
3. Value proposition (why is it worth this much?)

Be realistic but generous for premium patterns.

Format your response as:
PRICE: $X - $Y
BUYER: [description]
VALUE: [1-2 sentences]"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.7
        )

        # Parse response
        content = response.choices[0].message.content

        # Extract fields (simple parsing)
        lines = content.strip().split('\n')
        price_line = [l for l in lines if l.startswith('PRICE:')][0]
        buyer_line = [l for l in lines if l.startswith('BUYER:')][0]
        value_line = [l for l in lines if l.startswith('VALUE:')][0]

        return {
            'pattern': pattern,
            'price_range': price_line.replace('PRICE:', '').strip(),
            'target_buyer': buyer_line.replace('BUYER:', '').strip(),
            'value_proposition': value_line.replace('VALUE:', '').strip(),
        }
```

---

## Cost Analysis

### Usage Estimates

**MVP (Month 1-3)**:
```
Pattern Suggestions: 1,000 requests/day × 200 tokens = 200K tokens/day
Difficulty Explanations: 500 requests/day × 150 tokens = 75K tokens/day
NLP Parsing: 200 requests/day × 50 tokens = 10K tokens/day

Total: ~285K tokens/day = 8.5M tokens/month
Cost: 8.5M × $0.88/M = $7.50/month
```

**Growth (Month 6-9)**:
```
Pattern Suggestions: 5,000 requests/day
Difficulty Explanations: 2,000 requests/day
NLP Parsing: 1,000 requests/day

Total: ~40M tokens/month
Cost: 40M × $0.88/M = $35/month
```

**Scale (Month 12+)**:
```
Pattern Suggestions: 20,000 requests/day
Difficulty Explanations: 10,000 requests/day
NLP Parsing: 5,000 requests/day
Marketplace Valuation: 1,000 requests/day

Total: ~180M tokens/month
Cost: 180M × $0.88/M = $158/month
```

### ROI Analysis

**Conversion Impact**:
```
Without AI suggestions:
  Conversion rate: 5%
  100 visitors → 5 customers

With AI suggestions:
  Conversion rate: 15% (3× improvement)
  100 visitors → 15 customers

Extra revenue: 10 customers × $6.30 avg = $63 extra
AI cost: $0.25 per 100 visitors

ROI: 252× return on AI investment
```

---

## Integration Guide

### Setup Together.ai

```bash
# 1. Sign up
# Go to together.ai and create account

# 2. Get API key
# Dashboard → API Keys → Create New Key

# 3. Install SDK
pip install together

# 4. Set environment variable
export TOGETHER_API_KEY="your-key-here"

# Or in .env file
echo "TOGETHER_API_KEY=your-key-here" >> .env
```

### Setup Hugging Face (Alternative)

```bash
# 1. Sign up at huggingface.co

# 2. Get token
# Settings → Access Tokens → New Token

# 3. Install SDK
pip install huggingface_hub

# 4. Configure
export HF_TOKEN="your-token-here"
```

### VaniKeys Integration

```python
# vanikeys/web/app.py
from fasthtml.common import *
from vanikeys.ai.pattern_suggester import PatternSuggester
from vanikeys.ai.explainer import DifficultyExplainer
from vanikeys.ai.parser import NLPPatternParser

app = FastHTML()

# Initialize AI services
suggester = PatternSuggester()
explainer = DifficultyExplainer()
parser = NLPPatternParser()

# Add routes (see examples above)
# ...
```

---

## Advanced Features

### 1. Chatbot Support

```python
# vanikeys/ai/chatbot.py
from together import Together
import os

class VaniKeysChatbot:
    """Customer support chatbot."""

    def __init__(self):
        self.client = Together(api_key=os.getenv("TOGETHER_API_KEY"))
        self.model = "meta-llama/Llama-3.1-70B-Instruct-Turbo"

        self.system_prompt = """You are a helpful VaniKeys support agent.
VaniKeys generates vanity cryptographic keys with custom patterns.

Key facts:
- Gacha mode: Pay per pull, no guarantee (like lottery)
- Guaranteed mode: Pay premium, guaranteed exact match
- Patterns use 3-6 character substrings
- We support Bitcoin, Ethereum, DIDs, Solana
- All keys are cryptographically secure
- Split-key technology protects private keys

Be friendly, concise, and helpful!"""

    def chat(self, user_message: str, history: list = None) -> str:
        """Handle chat message."""

        messages = [
            {"role": "system", "content": self.system_prompt}
        ]

        if history:
            messages.extend(history)

        messages.append({"role": "user", "content": user_message})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=300,
            temperature=0.7
        )

        return response.choices[0].message.content
```

### 2. Batch Pattern Generation

```python
def generate_batch_patterns(theme: str, count: int = 100) -> list[str]:
    """
    Generate many patterns for marketplace pre-population.

    Example:
        theme = "professional titles"
        → ["CEO", "CTO", "CFO", "VP ENG", "DR SMITH", ...]
    """

    prompt = f"""Generate {count} short vanity key patterns for: {theme}

Requirements:
- 2-3 substrings each
- 3-6 characters per substring
- Relevant to theme
- Diverse and creative

Return ONLY the patterns, one per line."""

    # ... (implementation similar to above)
```

---

## Monitoring & Optimization

### Track Costs

```python
# vanikeys/ai/tracker.py
import redis
from datetime import datetime

class AIUsageTracker:
    """Track AI usage and costs."""

    def __init__(self):
        self.redis = redis.Redis()

    def log_request(
        self,
        feature: str,
        tokens_used: int,
        cost: float
    ):
        """Log AI request."""

        key = f"ai:usage:{datetime.now().strftime('%Y-%m-%d')}"

        self.redis.hincrby(key, f"{feature}:requests", 1)
        self.redis.hincrbyfloat(key, f"{feature}:tokens", tokens_used)
        self.redis.hincrbyfloat(key, f"{feature}:cost", cost)

    def get_daily_stats(self, date: str = None) -> dict:
        """Get daily AI usage stats."""

        if not date:
            date = datetime.now().strftime('%Y-%m-%d')

        key = f"ai:usage:{date}"
        data = self.redis.hgetall(key)

        # Parse and return
        # ...
```

### Optimize Prompts

```python
# Experiment with different prompts to minimize tokens

# Bad (too verbose):
"I need you to help me suggest some vanity key patterns..."
→ 50 tokens output

# Good (concise):
"Suggest 5 patterns:"
→ 30 tokens output

# Savings: 40% token reduction
```

---

## Production Checklist

- [ ] Sign up for Together.ai (or Hugging Face)
- [ ] Get API key
- [ ] Set environment variables
- [ ] Implement pattern suggester
- [ ] Implement difficulty explainer
- [ ] Add to web UI
- [ ] Test with real users
- [ ] Monitor costs
- [ ] Set up usage tracking
- [ ] Optimize prompts for cost
- [ ] Add rate limiting (prevent abuse)
- [ ] Cache common suggestions (reduce API calls)

---

## Conclusion

**AI features add massive value to VaniKeys for <$50/mo**:
- ✅ Better UX (pattern suggestions)
- ✅ Higher conversions (explanations)
- ✅ Viral potential (AI-generated content)
- ✅ Scalable (API handles all the work)
- ✅ Negligible cost (tokens are cheap!)

**Recommended implementation order**:
1. Pattern suggestions (MVP - Week 1)
2. Difficulty explanations (MVP - Week 1)
3. NLP parsing (Week 2-3)
4. Chatbot (Week 4)
5. Marketplace valuation (Phase 3+)

---

**Document Status**: Implementation Ready
**Next Action**: Sign up for Together.ai and implement pattern suggester
**Owner**: VaniKeys AI Team
**Last Updated**: 2025-11-17
