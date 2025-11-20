# VaniKeys Production Deployment Plan

**Version**: 1.0
**Date**: 2025-11-17
**Status**: Design Phase
**Target**: TIA Infrastructure (tia-stickers + tia-proxy)

## Executive Summary

Deploy **VaniKeys** as a secure, containerized web service leveraging existing TIA infrastructure. The service will offer **split-key vanity generation** - allowing users to safely outsource computationally intensive key generation without exposing their private keys.

**Key Innovation**: Users never see their final private key on our servers. We generate a "partial key" that they combine offline with their own secret to produce the final vanity key.

## Table of Contents

1. [Infrastructure Overview](#infrastructure-overview)
2. [Split-Key Vanity Technology](#split-key-vanity-technology)
3. [Architecture Design](#architecture-design)
4. [Containerization Strategy](#containerization-strategy)
5. [Web Application Stack](#web-application-stack)
6. [Security Architecture](#security-architecture)
7. [Deployment Process](#deployment-process)
8. [Business Model](#business-model)
9. [Roadmap](#roadmap)

---

## Infrastructure Overview

### Existing TIA Production Infrastructure

**tia-proxy** (164.90.128.28):
- nginx SSL termination
- Reverse proxy for all TIA services
- Handles SSL certificates (Let's Encrypt)
- Routes traffic based on domain/subdomain

**tia-stickers** (165.227.98.17):
- Primary application server
- Runs 5 containerized microservices (SDMS platform)
- Podman container management with systemd
- DigitalOcean Spaces (S3-compatible storage)

### VaniKeys Infrastructure Plan

**Deployment Target**: tia-stickers server
**Container Management**: Podman (following SDMS pattern)
**Service Management**: systemd units
**Reverse Proxy**: tia-proxy nginx configuration
**Domain Options**:
- `vanikeys.com` (standalone brand)
- `vanity.tia.tools` (TIA ecosystem subdomain)
- `keys.tia.tools` (alternative subdomain)

**Resource Requirements**:
- CPU: 4 vCPUs (for parallel generation)
- RAM: 2GB (modest - key generation is CPU-bound)
- Storage: 10GB (code + logs + temporary job data)
- Network: 100Mbps (low bandwidth requirements)

---

## Split-Key Vanity Technology

### The Problem with Traditional Services

**Traditional vanity services are insecure**:
- User requests pattern → Service generates key → Service sends private key
- **Risk**: Service operator has access to private key
- **Result**: Users' funds/identities can be compromised

### Split-Key Solution (Proven Technology)

Split-key vanity leverages elliptic curve properties to enable secure third-party generation:

```
┌─────────────────────────────────────────────────────────────┐
│                  Split-Key Vanity Process                   │
└─────────────────────────────────────────────────────────────┘

1. USER GENERATES SECRET KEY PAIR
   User: Creates keypair (s₁, P₁) locally
   User: Keeps s₁ SECRET, shares P₁ with service

2. SERVICE SEARCHES FOR PARTIAL KEY
   Service: Generates keypairs (s₂, P₂) until P₁ + P₂ matches pattern
   Service: Returns s₂ (partial private key) to user

3. USER COMBINES KEYS OFFLINE
   User: Computes final private key: s_final = s₁ + s₂ (mod n)
   User: Final public key: P_final = P₁ + P₂ (matches vanity pattern!)

SECURITY:
✅ Service never sees s₁ (user's secret)
✅ Service cannot derive s_final from s₂ alone
✅ User combines keys offline (no network exposure)
✅ Mathematically proven secure (ECDSA properties)
```

### Implementation Details

**Supported Curves**:
- ✅ **secp256k1** (Bitcoin, Ethereum) - Fast, proven split-key support
- ⚠️ **Ed25519** (DIDs, Solana) - Limited split-key support (research needed)

**Process Flow**:
1. User generates keypair locally (browser JS or CLI)
2. User sends public key P₁ + pattern to service
3. Service searches for partial key s₂ where P₁ + P₂ matches pattern
4. Service returns s₂ to user
5. User computes s_final = s₁ + s₂ offline
6. User verifies P_final matches expected vanity address

**Security Properties**:
- Service sees: P₁ (public key), Pattern (public info)
- Service generates: s₂ (meaningless without s₁)
- Service never sees: s₁ (user secret), s_final (actual private key)

### Libraries & Tools

**Existing Split-Key Tools**:
- `vanitygen-plusplus` - C++ implementation (reference)
- `split-key.py` - Python example scripts
- Browser-based generators (JavaScript ECDSA)

**VaniKeys Implementation Plan**:
- Phase 1: secp256k1 split-key (Bitcoin/Ethereum)
- Phase 2: Ed25519 research for DID split-key
- Phase 3: Browser-based key combination UI

---

## Architecture Design

### System Components

```
┌──────────────────────────────────────────────────────────────────┐
│                      VaniKeys Architecture                       │
└──────────────────────────────────────────────────────────────────┘

┌─────────────┐     HTTPS      ┌──────────────┐
│   Client    │ ───────────────▶│  tia-proxy   │
│  (Browser)  │                 │   (nginx)    │
└─────────────┘                 │ 164.90.128.28│
                                └──────┬───────┘
                                       │ Route: vanikeys.com
                                       │
                    ┌──────────────────▼──────────────────┐
                    │       tia-stickers (165.227.98.17)  │
                    ├─────────────────────────────────────┤
                    │  ┌────────────────────────────┐     │
                    │  │  VaniKeys Web (Port 8010)  │     │
                    │  │  FastHTML + HTMX           │     │
                    │  │  - Job submission          │     │
                    │  │  - Progress tracking       │     │
                    │  │  - Key combination UI      │     │
                    │  └──────────┬─────────────────┘     │
                    │             │ Queue                 │
                    │  ┌──────────▼─────────────────┐     │
                    │  │ Worker Pool (Port 8011)    │     │
                    │  │ - Multi-core generation    │     │
                    │  │ - Job processing           │     │
                    │  │ - Progress updates         │     │
                    │  └──────────┬─────────────────┘     │
                    │             │ Store                 │
                    │  ┌──────────▼─────────────────┐     │
                    │  │ Redis (Port 6379)          │     │
                    │  │ - Job queue                │     │
                    │  │ - Progress tracking        │     │
                    │  │ - Rate limiting            │     │
                    │  └────────────────────────────┘     │
                    └─────────────────────────────────────┘

Optional:
  ┌─────────────────┐
  │  PostgreSQL DB  │  (For accounts, job history, analytics)
  │  (Port 5432)    │
  └─────────────────┘
```

### Service Containers

**1. VaniKeys Web App** (Port 8010):
- **Framework**: FastHTML (proven in SDMS)
- **Purpose**: User interface, job submission, progress tracking
- **Features**:
  - Pattern submission form
  - Public key upload (for split-key)
  - Real-time progress (SSE or WebSockets)
  - Key combination calculator (browser-side JS)
  - Difficulty estimator
  - Educational content (security warnings)

**2. VaniKeys Worker Pool** (Port 8011):
- **Engine**: VaniKeys core (Python)
- **Purpose**: Parallel key generation across CPU cores
- **Features**:
  - Multi-worker coordination
  - Job queue processing (Redis)
  - Progress updates (via Redis pub/sub)
  - Timeout handling
  - Result caching

**3. Redis** (Port 6379):
- **Purpose**: Job queue, progress tracking, rate limiting
- **Data**:
  - Job queue (pending, in-progress, completed)
  - Progress metrics (attempts, rate, ETA)
  - Rate limiting (per-IP, per-user)
  - Temporary result storage (1-hour TTL)

**4. PostgreSQL** (Optional - Port 5432):
- **Purpose**: Accounts, job history, analytics
- **Tables**:
  - users (accounts, API keys)
  - jobs (submission history, patterns, results)
  - analytics (popular patterns, completion times)

---

## Containerization Strategy

### Following SDMS Pattern

VaniKeys will follow the proven SDMS containerization approach:

**Container Structure**:
```bash
vanikeys/
├── containers/
│   ├── web/
│   │   ├── Containerfile
│   │   ├── requirements.txt
│   │   └── app/
│   ├── worker/
│   │   ├── Containerfile
│   │   └── requirements.txt
│   └── redis/
│       └── Containerfile
├── deployment/
│   ├── deploy-to-registry.sh
│   ├── systemd/
│   │   ├── vanikeys-web-container.service
│   │   ├── vanikeys-worker-container.service
│   │   └── vanikeys-redis-container.service
│   └── nginx/
│       └── vanikeys.conf
└── podman-compose.yml
```

### Containerfile Examples

**Web App Container** (`containers/web/Containerfile`):
```dockerfile
FROM python:3.11-slim

# Non-root user (security)
RUN useradd -m -u 1001 vanikeys
USER vanikeys
WORKDIR /home/vanikeys

# Install VaniKeys + dependencies
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Copy application
COPY --chown=vanikeys:vanikeys app/ ./app/

# Environment
ENV PYTHONPATH=/home/vanikeys
ENV VANIKEYS_MODE=web
ENV REDIS_URL=redis://vanikeys-redis:6379

# Health check
HEALTHCHECK --interval=30s --timeout=3s \
  CMD curl -f http://localhost:8010/health || exit 1

# Run web server
EXPOSE 8010
CMD ["python3", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8010"]
```

**Worker Container** (`containers/worker/Containerfile`):
```dockerfile
FROM python:3.11-slim

RUN useradd -m -u 1001 vanikeys
USER vanikeys
WORKDIR /home/vanikeys

# Install VaniKeys core
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Copy VaniKeys library
COPY --chown=vanikeys:vanikeys ../../../src/vanikeys ./vanikeys/

# Environment
ENV PYTHONPATH=/home/vanikeys
ENV VANIKEYS_MODE=worker
ENV REDIS_URL=redis://vanikeys-redis:6379
ENV WORKER_CORES=4

# Run worker pool
CMD ["python3", "-m", "vanikeys.worker.pool", "--cores", "4"]
```

### Systemd Service Units

**Web Service** (`vanikeys-web-container.service`):
```ini
[Unit]
Description=VaniKeys Web Application
After=network-online.target vanikeys-redis-container.service
Requires=vanikeys-redis-container.service

[Service]
Type=simple
User=scottsen
ExecStartPre=/usr/bin/podman pull registry.digitalocean.com/tia/vanikeys-web:latest
ExecStart=/usr/bin/podman run --rm --name vanikeys-web \
  --network vanikeys-net \
  -p 8010:8010 \
  -e REDIS_URL=redis://vanikeys-redis:6379 \
  -e ANTHROPIC_API_KEY_FILE=/run/secrets/anthropic_key \
  -v vanikeys-data:/home/vanikeys/data:Z \
  registry.digitalocean.com/tia/vanikeys-web:latest

ExecStop=/usr/bin/podman stop -t 10 vanikeys-web
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Worker Service** (`vanikeys-worker-container.service`):
```ini
[Unit]
Description=VaniKeys Worker Pool
After=network-online.target vanikeys-redis-container.service
Requires=vanikeys-redis-container.service

[Service]
Type=simple
User=scottsen
ExecStartPre=/usr/bin/podman pull registry.digitalocean.com/tia/vanikeys-worker:latest
ExecStart=/usr/bin/podman run --rm --name vanikeys-worker \
  --network vanikeys-net \
  --cpus=4 \
  --memory=2g \
  -e REDIS_URL=redis://vanikeys-redis:6379 \
  -e WORKER_CORES=4 \
  registry.digitalocean.com/tia/vanikeys-worker:latest

ExecStop=/usr/bin/podman stop -t 10 vanikeys-worker
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Nginx Configuration

**tia-proxy nginx config** (`/etc/nginx/sites-available/vanikeys.conf`):
```nginx
# VaniKeys - Vanity Key Generation Service
upstream vanikeys_web {
    server 165.227.98.17:8010;
}

server {
    listen 80;
    server_name vanikeys.com www.vanikeys.com;

    # Redirect to HTTPS
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name vanikeys.com www.vanikeys.com;

    # SSL (Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/vanikeys.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/vanikeys.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=vanikeys_limit:10m rate=10r/s;
    limit_req zone=vanikeys_limit burst=20 nodelay;

    # Proxy to VaniKeys web app
    location / {
        proxy_pass http://vanikeys_web;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support (for real-time progress)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # Timeouts (key generation can take minutes)
        proxy_connect_timeout 60s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }

    # Static assets (cached)
    location /static/ {
        proxy_pass http://vanikeys_web;
        expires 7d;
        add_header Cache-Control "public, immutable";
    }

    # Health check endpoint (no rate limit)
    location /health {
        proxy_pass http://vanikeys_web;
        access_log off;
    }
}
```

---

## Web Application Stack

### FastHTML + HTMX Architecture

Following the proven SDMS pattern, VaniKeys uses **FastHTML** (Python web framework) with **HTMX** for interactivity.

**Why FastHTML?**
- ✅ Proven in production (SDMS platform)
- ✅ Python-native (integrates with VaniKeys core)
- ✅ Simple, fast development
- ✅ Built-in HTMX support
- ✅ Server-side rendering (SEO friendly)

### Application Structure

```python
# app/main.py - FastHTML entry point
from fasthtml.common import *
from vanikeys.core.engine import VanityEngine
from vanikeys.core.difficulty import DifficultyCalculator
import redis

app = FastHTML()
redis_client = redis.from_url(os.getenv("REDIS_URL"))

@app.get("/")
def home():
    return Titled("VaniKeys - Secure Vanity Key Generation",
        Hero(
            H1("Generate Vanity Crypto Keys Securely"),
            P("Never expose your private key. Use split-key technology."),
            A("Get Started", href="/generate", cls="btn-primary")
        ),
        Features()
    )

@app.get("/generate")
def generate_form():
    return Titled("Generate Vanity Key",
        Form(
            Input(name="pattern", placeholder="Enter pattern (e.g., LAB)"),
            Select(name="key_type",
                Option("Bitcoin", value="bitcoin"),
                Option("Ethereum", value="ethereum"),
                Option("DID", value="did")
            ),
            Checkbox(name="split_key", label="Use split-key (recommended)"),
            Button("Estimate Difficulty", hx_post="/api/estimate", hx_target="#difficulty"),
            Div(id="difficulty"),
            Button("Generate", type="submit", hx_post="/api/generate", hx_target="#result"),
            Div(id="result")
        )
    )

@app.post("/api/estimate")
async def estimate_difficulty(pattern: str, key_type: str):
    calc = DifficultyCalculator("base58")
    difficulty = calc.calculate(...)

    return Div(
        H3("Difficulty Estimate"),
        P(f"Average attempts: {difficulty.average_attempts:,}"),
        P(f"Estimated time: {difficulty.estimated_time(50_000_000)}"),
        P(f"Rating: {difficulty.difficulty_rating}")
    )

@app.post("/api/generate")
async def start_generation(pattern: str, key_type: str, split_key: bool, public_key: str = None):
    # Create job
    job_id = str(uuid.uuid4())

    job_data = {
        "pattern": pattern,
        "key_type": key_type,
        "split_key": split_key,
        "public_key": public_key,
        "status": "pending",
        "created_at": time.time()
    }

    # Queue job
    redis_client.lpush("vanikeys:jobs:pending", json.dumps(job_data))
    redis_client.setex(f"vanikeys:job:{job_id}", 3600, json.dumps(job_data))

    # Return progress UI
    return Div(
        H3("Generation in progress..."),
        Div(id="progress", hx_get=f"/api/progress/{job_id}", hx_trigger="every 1s"),
        cls="generating"
    )

@app.get("/api/progress/{job_id}")
async def get_progress(job_id: str):
    job_data = json.loads(redis_client.get(f"vanikeys:job:{job_id}"))

    if job_data["status"] == "completed":
        return Div(
            H3("✅ Success!"),
            P(f"Pattern found: {job_data['pattern']}"),
            Code(job_data["result"]),
            SplitKeyInstructions() if job_data["split_key"] else None
        )
    else:
        progress = job_data.get("progress", {})
        return Div(
            P(f"Attempts: {progress.get('attempts', 0):,}"),
            P(f"Rate: {progress.get('rate', 0):,.0f} keys/sec"),
            P(f"ETA: {progress.get('eta', 'Calculating...')}")
        )
```

### Key UI Features

**1. Split-Key Workflow**:
```python
def SplitKeyInstructions(partial_key: str):
    return Div(
        H3("🔐 Split-Key Result"),
        Alert("Your partial private key has been generated. "
              "Combine it offline with your secret key.", type="success"),

        H4("Step 1: Your Partial Key"),
        Code(partial_key, cls="partial-key"),

        H4("Step 2: Combine Offline"),
        P("Use our CLI tool or browser calculator:"),
        Div(
            Input(name="secret_key", placeholder="Your secret key (s₁)"),
            Input(name="partial_key", value=partial_key, readonly=True),
            Button("Calculate Final Key", onclick="combineKeys()"),
            Code(id="final_key", cls="hidden")
        ),

        Script("""
            function combineKeys() {
                const s1 = BigInt('0x' + document.querySelector('[name=secret_key]').value);
                const s2 = BigInt('0x' + document.querySelector('[name=partial_key]').value);
                const curve_order = BigInt('0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141');

                const s_final = (s1 + s2) % curve_order;
                document.getElementById('final_key').innerText = s_final.toString(16);
                document.getElementById('final_key').classList.remove('hidden');
            }
        """)
    )
```

**2. Real-time Progress** (Server-Sent Events):
```python
@app.get("/api/stream/{job_id}")
async def stream_progress(job_id: str):
    async def event_generator():
        pubsub = redis_client.pubsub()
        pubsub.subscribe(f"vanikeys:progress:{job_id}")

        async for message in pubsub.listen():
            if message['type'] == 'message':
                data = json.loads(message['data'])
                yield f"data: {json.dumps(data)}\n\n"

                if data.get('status') == 'completed':
                    break

    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

**3. Educational Content**:
```python
def SecurityEducation():
    return Div(
        H2("🔒 Why Split-Key is Secure"),

        Card(
            H3("❌ Traditional Vanity Services"),
            P("Service generates full private key → Sends to you"),
            Alert("⚠️ Service operator can access your funds!", type="danger")
        ),

        Card(
            H3("✅ Split-Key Vanity (VaniKeys)"),
            Ol(
                Li("You generate secret key (s₁) locally"),
                Li("Share public key (P₁) with service"),
                Li("Service finds partial key (s₂)"),
                Li("You combine offline: s_final = s₁ + s₂")
            ),
            Alert("✅ Service never sees your secret or final private key!", type="success")
        ),

        Details(
            Summary("Technical Details"),
            P("Split-key vanity uses elliptic curve properties:"),
            Code("P_final = P₁ + P₂ = (s₁ + s₂) × G"),
            P("The service cannot derive s₁ from P₁ (discrete log problem)"),
            P("The service cannot derive s_final from s₂ alone (needs s₁)")
        )
    )
```

---

## Security Architecture

### Threat Model

**What We Protect Against**:
1. ✅ Private key exposure to service operator
2. ✅ Man-in-the-middle attacks (HTTPS only)
3. ✅ DDoS / resource exhaustion (rate limiting)
4. ✅ Result tampering (verification instructions)

**What Users Must Protect**:
1. Their secret key (s₁) - kept offline
2. Final combined key (s_final) - never share
3. Local environment security (malware, keyloggers)

### Security Measures

**1. Split-Key Architecture**:
- Service never sees user's secret key (s₁)
- Service only sees public key (P₁) - public information
- Partial key (s₂) is useless without s₁

**2. HTTPS Everywhere**:
- TLS 1.2+ only
- HSTS headers
- Certificate pinning (optional)

**3. Rate Limiting**:
```nginx
# Per-IP rate limiting
limit_req_zone $binary_remote_addr zone=vanikeys_limit:10m rate=10r/s;
limit_req zone=vanikeys_limit burst=20 nodelay;

# Per-user rate limiting (if authenticated)
limit_req_zone $http_x_user_id zone=user_limit:10m rate=100r/h;
```

**4. Resource Limits**:
```python
# Job limits
MAX_PATTERN_LENGTH = 8  # Longer = exponentially harder
MAX_JOB_DURATION = 3600  # 1 hour timeout
MAX_CONCURRENT_JOBS_PER_IP = 2

# Worker limits
WORKER_CORES = 4
WORKER_MEMORY_LIMIT = "2g"
JOB_TIMEOUT = 3600
```

**5. Verification**:
```python
def verify_result(public_key: str, partial_key: str, pattern: str) -> bool:
    """
    Provide verification code so users can check results locally.
    """
    # User can verify:
    # 1. P₁ + P₂ matches pattern
    # 2. s₂ generates P₂ correctly
    # 3. Final address from combined key matches expected
    pass
```

**6. No Persistence of Sensitive Data**:
- Partial keys (s₂) stored in Redis with 1-hour TTL
- No logging of partial keys
- No database storage of keys
- All job results auto-deleted after 24 hours

**7. Open Source**:
- VaniKeys code is open source
- Users can verify no backdoors
- Self-hosting option available

---

## Deployment Process

### Phase 1: Development Environment

**1. Local Development Setup**:
```bash
# Clone VaniKeys
cd ~/src/projects/vanikeys

# Install dependencies
pip install -r requirements.txt

# Run local dev server
cd src
python3 -m vanikeys.web.dev --port 8010
```

**2. Local Container Testing**:
```bash
# Build containers
podman build -t vanikeys-web:dev -f containers/web/Containerfile .
podman build -t vanikeys-worker:dev -f containers/worker/Containerfile .

# Create network
podman network create vanikeys-net

# Start Redis
podman run -d --name vanikeys-redis --network vanikeys-net redis:7-alpine

# Start worker
podman run -d --name vanikeys-worker --network vanikeys-net \
  --cpus=2 -e REDIS_URL=redis://vanikeys-redis:6379 \
  vanikeys-worker:dev

# Start web
podman run -d --name vanikeys-web --network vanikeys-net \
  -p 8010:8010 -e REDIS_URL=redis://vanikeys-redis:6379 \
  vanikeys-web:dev

# Test
curl http://localhost:8010/health
```

### Phase 2: Production Deployment

**1. Container Registry Setup**:
```bash
# Tag for registry
podman tag vanikeys-web:latest registry.digitalocean.com/tia/vanikeys-web:latest
podman tag vanikeys-worker:latest registry.digitalocean.com/tia/vanikeys-worker:latest

# Push to registry
podman push registry.digitalocean.com/tia/vanikeys-web:latest
podman push registry.digitalocean.com/tia/vanikeys-worker:latest
```

**2. Deploy to tia-stickers**:
```bash
# SSH to tia-stickers
ssh tia-stickers

# Create network
podman network create vanikeys-net

# Create volumes
podman volume create vanikeys-data
podman volume create vanikeys-redis

# Install systemd units
sudo cp deployment/systemd/*.service /etc/systemd/system/
sudo systemctl daemon-reload

# Start services
sudo systemctl enable vanikeys-redis-container.service
sudo systemctl enable vanikeys-worker-container.service
sudo systemctl enable vanikeys-web-container.service

sudo systemctl start vanikeys-redis-container.service
sudo systemctl start vanikeys-worker-container.service
sudo systemctl start vanikeys-web-container.service

# Check status
sudo systemctl status vanikeys-*
```

**3. Configure tia-proxy**:
```bash
# SSH to tia-proxy
ssh tia-proxy

# Copy nginx config
sudo cp vanikeys.conf /etc/nginx/sites-available/
sudo ln -s /etc/nginx/sites-available/vanikeys.conf /etc/nginx/sites-enabled/

# Get SSL cert
sudo certbot --nginx -d vanikeys.com -d www.vanikeys.com

# Reload nginx
sudo nginx -t && sudo systemctl reload nginx
```

**4. Verify Deployment**:
```bash
# Test health endpoint
curl https://vanikeys.com/health

# Test full workflow
curl -X POST https://vanikeys.com/api/estimate \
  -H "Content-Type: application/json" \
  -d '{"pattern": "ABC", "key_type": "bitcoin"}'
```

### Phase 3: Monitoring & Operations

**1. Health Checks**:
```bash
# Container health
ssh tia-stickers "sudo systemctl status vanikeys-*"

# Resource usage
ssh tia-stickers "podman stats vanikeys-web vanikeys-worker vanikeys-redis"

# Logs
ssh tia-stickers "podman logs -f vanikeys-web"
ssh tia-stickers "podman logs -f vanikeys-worker"
```

**2. Scaling**:
```bash
# Scale workers (if needed)
ssh tia-stickers "sudo systemctl stop vanikeys-worker-container"

# Edit worker count
# ExecStart=... --cpus=8 -e WORKER_CORES=8

ssh tia-stickers "sudo systemctl start vanikeys-worker-container"
```

---

## Business Model

### Pricing Strategy

**Freemium Model**:

**Free Tier**:
- 3-4 character patterns (easy, instant)
- CPU-only generation
- 10 jobs per day per IP
- Public job queue (may wait)
- Community support

**Pro Tier** ($9.99/month):
- 5-6 character patterns (moderate difficulty)
- Priority queue (no waiting)
- 100 jobs per month
- Email support
- API access

**Enterprise Tier** ($99/month):
- Unlimited patterns (within reason)
- Dedicated workers (guaranteed resources)
- 1000 jobs per month
- Priority support
- White-label option
- SLA guarantee (99.9% uptime)

**Pay-as-you-go**:
- $0.50 for 3-char pattern
- $2.00 for 4-char pattern
- $10.00 for 5-char pattern
- $50.00 for 6-char pattern
- $500.00 for 7-char pattern (GPU required)

### Revenue Projections

**Conservative Estimate** (Year 1):
- 100 free users/month
- 10 pro subscriptions/month ($99/month)
- 5 enterprise clients/month ($495/month)
- 20 pay-as-you-go jobs/month ($400/month)

**Monthly Revenue**: $1,900
**Annual Revenue**: ~$23,000

**Optimistic Estimate** (Year 2):
- 1000 free users/month
- 100 pro subscriptions ($999/month)
- 20 enterprise ($1,980/month)
- 200 pay-as-you-go ($4,000/month)

**Monthly Revenue**: $7,000
**Annual Revenue**: ~$84,000

### Market Opportunity

**Target Markets**:
1. **Crypto enthusiasts** - Branded wallet addresses
2. **DID users** - Organization identifiers
3. **Businesses** - Corporate crypto addresses
4. **NFT projects** - Vanity contract addresses
5. **DAOs** - Recognizable treasury addresses

**Competitive Advantages**:
- ✅ Split-key security (most services are insecure)
- ✅ DID support (no competition)
- ✅ Modern UI/UX (most tools are CLI-only)
- ✅ Educational focus (security awareness)
- ✅ Open source (trust through transparency)

### Marketing Strategy

**Phase 1: Launch** (Month 1-3):
- Launch on Product Hunt
- Post on /r/Bitcoin, /r/ethereum, /r/CryptoCurrency
- Write technical blog posts (SEO)
- Reach out to crypto YouTubers/influencers

**Phase 2: Growth** (Month 4-6):
- Partnership with wallet providers
- Integration with DID platforms
- Sponsorship of crypto conferences
- Affiliate program (20% commission)

**Phase 3: Scale** (Month 7-12):
- Enterprise sales (DAOs, businesses)
- White-label offering
- API partnerships
- Educational content (YouTube channel)

---

## Roadmap

### Phase 1: MVP (Week 1-4)

**Week 1: Core Implementation**
- ✅ VaniKeys core library (DONE)
- ✅ CLI interface (DONE)
- ⏳ Split-key implementation (secp256k1)
- ⏳ Worker queue system (Redis)

**Week 2: Web Application**
- ⏳ FastHTML app structure
- ⏳ Job submission UI
- ⏳ Progress tracking (SSE)
- ⏳ Key combination calculator

**Week 3: Containerization**
- ⏳ Containerfiles (web + worker + redis)
- ⏳ Systemd units
- ⏳ Local testing
- ⏳ Documentation

**Week 4: Deployment**
- ⏳ Deploy to tia-stickers
- ⏳ Configure tia-proxy
- ⏳ SSL setup
- ⏳ Monitoring

**MVP Deliverables**:
- Working web service at vanikeys.com
- Bitcoin/Ethereum split-key generation
- Free tier functional
- Basic documentation

### Phase 2: Features (Month 2-3)

**Features**:
- DID vanity generation
- User accounts (PostgreSQL)
- Payment integration (Stripe)
- Job history
- API endpoints
- Difficulty calculator improvements
- GPU support (secp256k1)

### Phase 3: Scale (Month 4-6)

**Scaling**:
- Multi-server deployment
- Load balancing
- Advanced rate limiting
- Analytics dashboard
- Marketing launch
- Customer support system

### Phase 4: Enterprise (Month 7-12)

**Enterprise Features**:
- White-label deployments
- Dedicated infrastructure
- SLA agreements
- Priority support
- Custom integrations
- API SDK (Python, JavaScript, Go)

---

## Risk Analysis

### Technical Risks

**Risk**: Ed25519 split-key not yet proven
**Mitigation**: Start with secp256k1 only, research Ed25519 split-key in parallel

**Risk**: Server compromise exposes partial keys
**Mitigation**: 1-hour TTL on all results, no persistent storage, open source code

**Risk**: DDoS attacks overwhelm workers
**Mitigation**: Rate limiting, Cloudflare, queue prioritization

### Business Risks

**Risk**: Low adoption (market too niche)
**Mitigation**: Freemium model, focus on DID market (underserved)

**Risk**: Competition from free tools
**Mitigation**: Superior UX, split-key security, DID support, education

**Risk**: Regulatory concerns (key generation service)
**Mitigation**: Clear disclaimers, educational focus, self-hosting option

### Security Risks

**Risk**: Users don't understand split-key security
**Mitigation**: Extensive educational content, verification tools, warnings

**Risk**: Phishing sites impersonating VaniKeys
**Mitigation**: SSL, brand awareness, verified social media

---

## Success Metrics

### Technical Metrics
- ✅ 99.9% uptime
- ✅ <1s response time for web pages
- ✅ 50M+ keys/sec generation rate (GPU)
- ✅ <30s avg completion for 4-char patterns

### Business Metrics
- 📊 100+ free tier users/month (Month 3)
- 📊 10+ paid subscriptions (Month 6)
- 📊 $1,000/month revenue (Month 6)
- 📊 $5,000/month revenue (Month 12)

### User Satisfaction
- ⭐ 4.5+ star rating (Product Hunt, Trustpilot)
- 💬 <24h support response time
- 📈 80%+ job completion rate
- 🔒 Zero security incidents

---

## Appendix

### A. Technology Stack

**Backend**:
- Python 3.11
- FastHTML (web framework)
- Redis (job queue)
- PostgreSQL (optional - accounts)
- uvicorn (ASGI server)

**Frontend**:
- HTMX (interactivity)
- Alpine.js (client-side logic)
- Tailwind CSS (styling)
- Chart.js (analytics)

**Infrastructure**:
- Podman (containers)
- systemd (service management)
- nginx (reverse proxy)
- Let's Encrypt (SSL)

**Crypto Libraries**:
- cryptography (Python)
- eth-keys (Ethereum)
- bitcoin (Bitcoin)

### B. Code Examples

See `/examples/split_key_demo.py` for working split-key implementation.

### C. References

**Split-Key Vanity**:
- Bitcoin Wiki: https://en.bitcoin.it/wiki/Split-key_vanity_address
- vanitygen-plusplus: https://github.com/10gic/vanitygen-plusplus

**TIA Infrastructure**:
- SDMS Architecture: `/projects/websites/platforms/sdms/docs/`
- Containerization Guide: `/docs/guides/CONTAINERIZATION_USER_GUIDE.md`

**FastHTML**:
- FastHTML Docs: https://fastht.ml/
- SDMS FastHTML Implementation: `/projects/websites/platforms/sdms/`

---

**Document Status**: Design Phase - Ready for Implementation
**Next Steps**: Begin Phase 1 - Week 1 (Core Implementation)
**Owner**: VaniKeys Project Team
**Last Updated**: 2025-11-17
