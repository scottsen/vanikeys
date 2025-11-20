# VaniKeys Compute Options: Quick Comparison

**Last Updated**: 2025-11-17

This is a quick reference guide for choosing compute infrastructure for VaniKeys. For detailed guides, see:
- **Serverless GPU**: [`SERVERLESS_GPU_OPTIONS.md`](SERVERLESS_GPU_OPTIONS.md)
- **DigitalOcean**: [`DIGITALOCEAN_GPU_DEPLOYMENT.md`](DIGITALOCEAN_GPU_DEPLOYMENT.md)

---

## TL;DR Recommendations

### MVP (Now - Month 3)
**Use**: **RunPod Serverless** (RTX 4090)
- **Cost**: $25-100/mo (vs $1,095 for dedicated)
- **Savings**: 98%
- **Cold start**: <200ms
- **Perfect for**: Gacha mode instant pulls

### Growing (Month 3-6)
**Use**: **RunPod + Modal** hybrid
- **RunPod**: Gacha mode ($0.008/job)
- **Modal**: Guaranteed mode with checkpointing
- **Cost**: $200-500/mo
- **Revenue**: $10K-30K/mo (90%+ margins)

### Scale (Month 6-12)
**Evaluate**: Dedicated vs serverless based on volume
- **<5K jobs/day**: Stay serverless
- **>5K jobs/day**: Consider dedicated baseline + serverless burst

---

## Cost Comparison Table

### At 100 Jobs/Day (MVP Volume)

| Option | Monthly Cost | Setup Time | Scalability | Best For |
|--------|--------------|------------|-------------|----------|
| **RunPod Serverless** ⭐ | **$24** | 1 day | Auto (0-1000) | **MVP** |
| **Modal** | $92 | 1 day | Auto | Flexibility |
| **DO GPU Droplet** | $1,095 | 1 week | Manual | Always-on |
| **AWS Batch Spot** | $45 | 2 weeks | Complex | Batch jobs |

**Winner**: RunPod Serverless (98% cheaper)

### At 1,000 Jobs/Day (Growth Volume)

| Option | Monthly Cost | Margin |
|--------|--------------|--------|
| **RunPod Serverless** ⭐ | **$240** | 96% |
| **Modal** | $900 | 86% |
| **DO GPU (1x)** | $1,095 | 83% |
| **AWS Batch Spot** | $450 | 93% |

**Winner**: RunPod Serverless (78% cheaper than dedicated)

### At 10,000 Jobs/Day (Scale Volume)

| Option | Monthly Cost | Throughput |
|--------|--------------|------------|
| **AWS Batch Spot** ⭐ | **$1,350** | Unlimited |
| **RunPod Serverless** | $2,400 | 500M keys/sec |
| **DO GPU (4x)** | $4,380 | 200M keys/sec |
| **Modal** | $9,000 | Account limited |

**Winner**: AWS Batch Spot (but RunPod simpler)

---

## Feature Comparison

### Serverless Options

| Feature | RunPod | Modal | Replicate | AWS Batch |
|---------|--------|-------|-----------|-----------|
| **Cold Start** | <200ms ⭐ | ~10s | ~30s | ~5 min |
| **Billing** | Per ms ⭐ | Per sec | Per job | Per hour |
| **RTX 4090** | $0.34/hr ✅ | ❌ | ❌ | ❌ |
| **A100** | $1.14/hr | $1.10/hr | N/A | ~$3/hr |
| **Auto-scale** | ✅ 0-1000 | ✅ | ✅ | ⚠️ Complex |
| **Checkpoints** | ❌ | ✅ ⭐ | ❌ | ✅ |
| **Python Code** | ❌ Docker | ✅ ⭐ | ❌ | ❌ |
| **Setup Time** | 1 day | 1 day | 1 day | 2 weeks |

### Dedicated Options

| Feature | DigitalOcean | AWS EC2 | GCP |
|---------|--------------|---------|-----|
| **RTX 4000 Ada** | $1,095/mo ✅ | N/A | N/A |
| **H100** | $2,600/mo | ~$8,000/mo | ~$7,500/mo |
| **Setup** | Simple ✅ | Complex | Complex |
| **Scaling** | Manual | Auto (ASG) | Auto (MIG) |
| **Best for** | Baseline load | Enterprise | Enterprise |

---

## Decision Matrix

### Choose RunPod Serverless If:
- ✅ MVP or early stage (<1K jobs/day)
- ✅ Highly variable traffic (bursty)
- ✅ Need instant response (<200ms)
- ✅ Want simplest setup
- ✅ Want lowest cost at low volume

### Choose Modal If:
- ✅ Long-running jobs (hours)
- ✅ Need checkpointing/resume
- ✅ Want flexible Python code
- ✅ Willing to trade cold start for features

### Choose DigitalOcean GPU If:
- ✅ Consistent high volume (>5K jobs/day)
- ✅ Want full control
- ✅ Already on DigitalOcean
- ✅ Simple deployment preferred over AWS

### Choose AWS Batch + Spot If:
- ✅ Very high volume (>10K jobs/day)
- ✅ Can tolerate interruptions
- ✅ Want maximum cost savings
- ✅ Have AWS expertise

---

## Cost Breakeven Points

### RunPod vs Dedicated GPU

```
Dedicated DO GPU: $1,095/month (fixed)
RunPod per job: $0.008 (variable)

Breakeven: 136,875 jobs/month = 4,562 jobs/day

Below 4,562 jobs/day → RunPod wins
Above 4,562 jobs/day → Consider dedicated
```

### RunPod vs Modal

```
RunPod: $0.008 per job (RTX 4090)
Modal: $0.026 per job (A100)

Modal is 3.25x more expensive per job
Use Modal only for features (checkpointing, flexibility)
Not for cost savings
```

---

## Performance Comparison

### GPU Performance (secp256k1)

| GPU | Keys/Sec | Cost/Hour | Cost per 1B Keys |
|-----|----------|-----------|------------------|
| RTX 4090 (RunPod) | 50M | $0.34 | $0.0068 |
| A100 (Modal) | 80M | $1.10 | $0.0138 |
| RTX 4000 (DO) | 50M | $1.52 | $0.0304 |
| H100 (RunPod) | 200M | $1.99 | $0.0100 |

**Winner**: RTX 4090 on RunPod (best price/performance)

### CPU Performance (Ed25519)

| Platform | vCPUs | Keys/Sec | Cost/Hour | Cost per 1M Keys |
|----------|-------|----------|-----------|------------------|
| Modal CPU | 16 | 2M | $0.0016 | $0.0008 |
| DO c-16 | 16 | 2M | $0.26 | $0.13 |
| DO c-32 | 32 | 4M | $0.53 | $0.13 |

**Winner**: Modal CPU (100x cheaper for Ed25519)

---

## Real-World Example

### Pattern: "GO BE AWE SOME" (4 substrings)

**Difficulty**:
- Expected attempts: 421,356 (for 3/4 match)
- Expected attempts: 4.2 billion (for 4/4 exact match)

**Guaranteed Mode (Exact Match) Costs**:

```
RunPod RTX 4090:
  Time: 84 seconds (50M keys/sec)
  Cost: $0.008
  Revenue: $6.30 (630 tokens)
  Profit: $6.29 (99.9% margin)

Modal A100:
  Time: 53 seconds (80M keys/sec)
  Cost: $0.026
  Revenue: $6.30
  Profit: $6.27 (99.6% margin)

DO RTX 4000 (dedicated):
  Time: 84 seconds
  Cost: $0.035 (amortized from monthly)
  Revenue: $6.30
  Profit: $6.27 (99.4% margin)

AWS Batch Spot (T4):
  Time: 168 seconds (25M keys/sec)
  Cost: $0.007 (spot pricing)
  Revenue: $6.30
  Profit: $6.29 (99.9% margin)
```

**Ranking by Profit**:
1. **RunPod RTX 4090**: $6.29 profit (99.9%)
2. AWS Batch Spot: $6.29 profit (99.9%)
3. Modal A100: $6.27 profit (99.6%)
4. DO Dedicated: $6.27 profit (99.4%)

**Ranking by Simplicity**:
1. **RunPod**: Dead simple
2. Modal: Very simple
3. DO Dedicated: Simple
4. AWS Batch: Complex

**Overall Winner**: **RunPod RTX 4090** (best profit + simplest)

---

## Monthly Cost Projections

### Revenue Model (from GAMIFICATION_DESIGN.md)

```
Conservative (100 jobs/day):
  Revenue: $10,950/mo

Moderate (500 jobs/day):
  Revenue: $62,700/mo

Growth (2,000 jobs/day):
  Revenue: $250,800/mo
```

### Cost Model

| Jobs/Day | RunPod | Modal | DO GPU | Margin (RunPod) |
|----------|--------|-------|--------|-----------------|
| 100 | $24 | $92 | $1,095 | **99.8%** |
| 500 | $120 | $460 | $1,095 | **99.8%** |
| 1,000 | $240 | $900 | $2,190 | **99.6%** |
| 2,000 | $480 | $1,800 | $4,380 | **99.8%** |
| 5,000 | $1,200 | $4,500 | $10,950 | **98.8%** |

**Key Insight**: Even at 5,000 jobs/day, serverless maintains 98%+ margins!

---

## Migration Timeline

### Month 1-3: MVP
- **Deploy**: RunPod Serverless only
- **Cost**: $25-100/mo
- **Revenue**: $1K-10K/mo
- **Focus**: Product-market fit

### Month 3-6: Growth
- **Deploy**: RunPod + Modal hybrid
- **Cost**: $200-500/mo
- **Revenue**: $10K-50K/mo
- **Focus**: User acquisition

### Month 6-9: Optimize
- **Deploy**: Evaluate usage patterns
- **Cost**: $500-2K/mo
- **Revenue**: $50K-100K/mo
- **Focus**: Cost optimization

### Month 9-12: Scale
- **Deploy**: Hybrid (dedicated baseline + serverless burst)
- **Cost**: $2K-5K/mo
- **Revenue**: $100K-250K/mo
- **Focus**: Efficiency at scale

---

## Quick Start Commands

### RunPod (1 hour setup)

```bash
# 1. Install SDK
pip install runpod

# 2. Get API key from runpod.io/console

# 3. Build Docker image
docker build -t vanikeys-gpu -f Dockerfile.runpod .

# 4. Push to RunPod registry
docker push registry.runpod.io/username/vanikeys-gpu

# 5. Create endpoint via web UI
# 6. Test
python test_runpod.py
```

### Modal (30 min setup)

```bash
# 1. Install Modal
pip install modal

# 2. Authenticate
modal token new

# 3. Create app (vanikeys_modal.py)

# 4. Deploy
modal deploy vanikeys_modal.py

# 5. Test
modal run vanikeys_modal.py::main
```

---

## Support & Resources

### Documentation
- **Serverless Deep Dive**: [`SERVERLESS_GPU_OPTIONS.md`](SERVERLESS_GPU_OPTIONS.md)
- **DigitalOcean Guide**: [`DIGITALOCEAN_GPU_DEPLOYMENT.md`](DIGITALOCEAN_GPU_DEPLOYMENT.md)
- **Main Deployment Plan**: [`DEPLOYMENT_PLAN.md`](DEPLOYMENT_PLAN.md)

### External Links
- RunPod: https://docs.runpod.io/serverless
- Modal: https://modal.com/docs
- DigitalOcean GPUs: https://www.digitalocean.com/products/gradient/gpu-droplets

### Code Examples
- RunPod handler: `examples/runpod_handler.py`
- Modal app: `examples/vanikeys_modal.py`
- GPU router: `src/vanikeys/web/services/gpu_router.py`

---

**Document Status**: Production Ready
**Recommended**: Start with RunPod Serverless
**Next Action**: Follow [SERVERLESS_GPU_OPTIONS.md](SERVERLESS_GPU_OPTIONS.md) setup guide
**Last Updated**: 2025-11-17
