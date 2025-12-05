# VaniKeys Compute Options - Quick Comparison

**Last Updated**: 2025-12-05
**Purpose**: Fast decision-making for GPU infrastructure

---

## TL;DR: Which Option When?

| Your Situation | Recommendation | Doc to Read |
|----------------|----------------|-------------|
| MVP, <100 jobs/day | **RunPod Serverless** (RTX 4090) | SERVERLESS_GPU_OPTIONS.md |
| Growing, 100-1K jobs/day | **RunPod + Modal** (hybrid) | SERVERLESS_GPU_OPTIONS.md |
| Scaling, 1K-5K jobs/day | **RunPod Serverless** (multi-region) | SERVERLESS_GPU_OPTIONS.md |
| Enterprise, >5K jobs/day | **DigitalOcean GPU** (dedicated) | DIGITALOCEAN_GPU_DEPLOYMENT.md |
| Viral spike handling | **Hybrid** (dedicated + serverless) | Both docs |
| AWS-only requirement | **AWS Batch + Spot** | SERVERLESS_GPU_OPTIONS.md |

---

## Platform Comparison Table

| Feature | RunPod Serverless | Modal | DigitalOcean GPU | AWS Batch |
|---------|-------------------|-------|------------------|-----------|
| **Cost (per job)** | $0.008 | $0.026 | $0.024 (amortized) | $0.007 |
| **Cold Start** | <200ms | 5-10s | N/A (always on) | 1-2 min |
| **GPU Options** | RTX 4090, A100, H100 | A100, H100 | RTX 4000 Ada, H100 | Various |
| **Performance** | 50M keys/sec | 80M keys/sec | 40M keys/sec | Varies |
| **Auto-scale** | ✅ 0→1000 workers | ✅ Dynamic | ❌ Manual | ✅ Spot fleet |
| **Checkpointing** | ❌ | ✅ Built-in | ✅ DIY | ✅ DIY |
| **Setup Time** | 1 hour | 2 hours | 4 hours | 8 hours |
| **Complexity** | ⭐ Simple | ⭐⭐ Moderate | ⭐⭐⭐ Advanced | ⭐⭐⭐⭐ Expert |
| **Best For** | Gacha mode | Guaranteed mode | Baseline traffic | AWS enterprise |

---

## Cost Breakdown by Volume

### Monthly Infrastructure Costs

| Jobs/Day | RunPod | Modal | DO GPU | AWS Batch | Recommendation |
|----------|--------|-------|--------|-----------|----------------|
| 10 | $2 | $8 | $1,095 | $2 | **RunPod** (99% savings) |
| 100 | $24 | $78 | $1,095 | $21 | **RunPod** (98% savings) |
| 500 | $120 | $390 | $1,095 | $105 | **RunPod** (89% savings) |
| 1,000 | $240 | $780 | $1,095 | $210 | **RunPod** (78% savings) |
| 2,500 | $600 | $1,950 | $1,095 | $525 | **RunPod** (45% savings) |
| 5,000 | $1,200 | $3,900 | $1,095 | $1,050 | **DO GPU** (8% savings) |
| 10,000 | $2,400 | $7,800 | $2,190 (×2) | $2,100 | **DO GPU** (9% savings) |

**Notes**:
- RunPod: $0.008/job average (gacha + guaranteed mix)
- Modal: $0.026/job (A100)
- DO GPU: $1,095/mo fixed (RTX 4000 Ada)
- AWS Batch: $0.007/job (Spot pricing)

---

## Performance Comparison

### Pattern: "GO BE AWE SOME" (4.2B attempts expected)

| Platform | GPU | Time | Cost | Keys/sec |
|----------|-----|------|------|----------|
| **RunPod** | RTX 4090 | 84 sec | $0.008 | 50M |
| **Modal** | A100 | 53 sec | $0.026 | 80M |
| **DO GPU** | RTX 4000 Ada | 105 sec | $0.024 | 40M |
| **AWS Batch** | g5.xlarge | 168 sec | $0.007 | 25M |

**Winner**: RunPod (best cost + speed balance)

### Pattern: "SWIFT" (simple prefix, 2.1M attempts)

| Platform | GPU | Time | Cost | Keys/sec |
|----------|-----|------|------|----------|
| **RunPod** | RTX 4090 | <1 sec | $0.008 | 50M |
| **Modal** | A100 | <1 sec | $0.026 | 80M |
| **DO GPU** | RTX 4000 Ada | <1 sec | $0.024 | 40M |
| **AWS Batch** | g5.xlarge | 10 sec | $0.007 | 25M |

**Winner**: RunPod (lowest cost, <1s is fast enough)

---

## Use Case Recommendations

### Use Case 1: MVP Launch (0-100 users)

**Scenario**: Testing product-market fit, unpredictable traffic

**Recommendation**: RunPod Serverless only

**Why**:
- $24/mo at 100 jobs/day (vs $1,095 dedicated)
- No commitment
- Scales to zero when idle
- Fast iteration

**Configuration**:
```yaml
Platform: RunPod Serverless
GPU: RTX 4090
Workers: 0-10 (auto-scale)
Cost: $2-24/mo
Setup Time: 1 hour
```

---

### Use Case 2: Growing Product (100-1K users)

**Scenario**: Product validated, growing traffic, need reliability

**Recommendation**: RunPod (gacha) + Modal (guaranteed)

**Why**:
- RunPod handles fast gacha pulls (<200ms)
- Modal provides checkpointing for guaranteed mode
- Combined cost still 78% cheaper than dedicated
- Best UX for both modes

**Configuration**:
```yaml
Gacha Mode: RunPod RTX 4090
Guaranteed Mode: Modal A100
Total Cost: $240-355/mo
Setup Time: 3 hours
```

---

### Use Case 3: Scaled Product (1K-5K users)

**Scenario**: Consistent high volume, predictable patterns

**Recommendation**: RunPod Serverless (multi-region)

**Why**:
- Still cheaper than dedicated up to 5K jobs/day
- Multi-region for redundancy
- Prepare for dedicated migration at 5K+ threshold

**Configuration**:
```yaml
Platform: RunPod Serverless
Regions: US-East, US-West, EU
GPU: RTX 4090
Workers: 0-50 per region
Cost: $600-1,200/mo
```

---

### Use Case 4: Enterprise Scale (>5K users)

**Scenario**: High volume, need control, predictable costs

**Recommendation**: DigitalOcean GPU + RunPod burst

**Why**:
- Dedicated GPU handles baseline (cheaper at this scale)
- RunPod handles traffic spikes
- Full infrastructure control
- Enterprise-friendly (no vendor lock-in)

**Configuration**:
```yaml
Baseline: DigitalOcean RTX 4000 Ada
Burst: RunPod Serverless
Workers: 4-8 baseline + 0-20 burst
Cost: $1,095-1,500/mo
```

---

## Decision Flowchart

```
Start
  │
  ├─ Do you have >5K jobs/day consistently?
  │   ├─ Yes → DigitalOcean GPU (DIGITALOCEAN_GPU_DEPLOYMENT.md)
  │   └─ No ↓
  │
  ├─ Do you need guaranteed delivery with checkpoints?
  │   ├─ Yes → RunPod (gacha) + Modal (guaranteed)
  │   └─ No ↓
  │
  ├─ Are you on AWS-only infrastructure?
  │   ├─ Yes → AWS Batch + Spot
  │   └─ No ↓
  │
  └─ Default → RunPod Serverless (SERVERLESS_GPU_OPTIONS.md)
```

---

## Quick Start Commands

### Deploy RunPod MVP (30 minutes)

```bash
# 1. Build Docker image
docker build -t vanikeys-runpod:latest .
docker push yourusername/vanikeys-runpod:latest

# 2. Create RunPod endpoint (via console)
# https://www.runpod.io/console/serverless

# 3. Test
python -c "
import runpod
runpod.api_key = 'YOUR_KEY'
endpoint = runpod.Endpoint('YOUR_ENDPOINT_ID')
result = endpoint.run({'pattern': 'TEST'})
print(result.output())
"
```

### Deploy Modal Guaranteed Mode (1 hour)

```bash
# 1. Install Modal
pip install modal
modal token new

# 2. Deploy function
modal deploy modal_handler.py

# 3. Test
modal run modal_handler.py::main
```

### Deploy DigitalOcean GPU (4 hours)

```bash
# 1. Create droplet
doctl compute droplet create vanikeys-gpu-1 \
  --region nyc3 \
  --size gpu-rtx4000ada-8vcpu-30gb \
  --image ubuntu-22-04-x64 \
  --ssh-keys YOUR_SSH_KEY_ID

# 2. Install NVIDIA drivers (see DIGITALOCEAN_GPU_DEPLOYMENT.md)

# 3. Deploy workers (see guide)
```

---

## Real-World Examples

### Example 1: Indie Hacker MVP

**Situation**: Solo dev, $0 budget, testing VaniKeys idea

**Solution**: RunPod Serverless
- Month 1: 50 jobs → $12/mo
- Month 2: 200 jobs → $48/mo
- Month 3: 500 jobs → $120/mo

**ROI**: 99% profit margin, scales as revenue grows

---

### Example 2: Funded Startup

**Situation**: Seed round, need reliability, 1K jobs/day

**Solution**: RunPod + Modal hybrid
- Baseline: $240/mo (RunPod gacha)
- Safety net: $50/mo (Modal guaranteed)
- Total: $290/mo

**ROI**: 99% margin, enterprise-grade reliability

---

### Example 3: Scale-up

**Situation**: Series A, 8K jobs/day, need predictability

**Solution**: DigitalOcean GPU baseline + RunPod burst
- Dedicated: $1,095/mo (handles 5K jobs/day)
- Burst: $240/mo (handles 3K overflow)
- Total: $1,335/mo

**ROI**: 50% cheaper than pure serverless at this scale

---

## Migration Path

### Phase 1: MVP (Month 1-3)
```
RunPod Serverless (RTX 4090)
  ↓
Cost: $12-120/mo
Volume: 50-500 jobs/day
```

### Phase 2: Growth (Month 4-6)
```
RunPod (gacha) + Modal (guaranteed)
  ↓
Cost: $120-355/mo
Volume: 500-1K jobs/day
```

### Phase 3: Scale (Month 7-12)
```
RunPod Serverless (multi-region)
  ↓
Cost: $355-1,200/mo
Volume: 1K-5K jobs/day
```

### Phase 4: Enterprise (Year 2+)
```
DigitalOcean GPU + RunPod burst
  ↓
Cost: $1,095-2,000/mo
Volume: 5K-15K jobs/day
```

---

## Common Mistakes to Avoid

### ❌ Mistake 1: Starting with Dedicated GPU
**Why it's wrong**: Pays $1,095/mo when MVP needs $24/mo
**Fix**: Start serverless, migrate at 5K jobs/day

### ❌ Mistake 2: Using Modal for Gacha Mode
**Why it's wrong**: 5-10s cold start kills UX, costs 3× more
**Fix**: RunPod for gacha (<200ms), Modal for guaranteed

### ❌ Mistake 3: No Monitoring
**Why it's wrong**: Can't tell when to switch platforms
**Fix**: Track jobs/day, cost per job, breakeven approaching

### ❌ Mistake 4: Over-engineering
**Why it's wrong**: Building for 10K jobs/day when doing 100
**Fix**: Start simple (RunPod only), add complexity as needed

---

## Cost Optimization Tips

### 1. Cache Popular Patterns
Save 10-30% by not regenerating common patterns.

### 2. Use Fuzzy Matching Wisely
Increases match rate 10×, reduces compute cost proportionally.

### 3. Batch Similar Jobs
Process similar patterns together for GPU efficiency.

### 4. Monitor Breakeven Point
Watch for 5K jobs/day threshold to switch to dedicated.

### 5. Use Spot Instances
AWS Batch with Spot can save 70% vs on-demand.

---

## Summary Table

| Metric | RunPod | Modal | DO GPU | AWS Batch |
|--------|--------|-------|--------|-----------|
| **Setup Complexity** | ⭐ Easy | ⭐⭐ Moderate | ⭐⭐⭐ Hard | ⭐⭐⭐⭐ Expert |
| **Cost Efficiency** | ⭐⭐⭐⭐⭐ Best | ⭐⭐⭐ Good | ⭐⭐⭐⭐ Best at scale | ⭐⭐⭐⭐⭐ Cheapest |
| **Performance** | ⭐⭐⭐⭐ Fast | ⭐⭐⭐⭐⭐ Fastest | ⭐⭐⭐⭐ Fast | ⭐⭐⭐ Moderate |
| **Reliability** | ⭐⭐⭐⭐ Good | ⭐⭐⭐⭐⭐ Best | ⭐⭐⭐⭐⭐ Best | ⭐⭐⭐⭐ Good |
| **Ease of Scale** | ⭐⭐⭐⭐⭐ Auto | ⭐⭐⭐⭐⭐ Auto | ⭐⭐ Manual | ⭐⭐⭐⭐ Auto |

**Recommendation for VaniKeys**: Start with **RunPod**, add **Modal** at 500 jobs/day, migrate to **DO GPU** at 5K jobs/day.

---

## Next Steps

1. **Read**: SERVERLESS_GPU_OPTIONS.md for RunPod setup
2. **Deploy**: RunPod MVP endpoint (1 hour)
3. **Monitor**: Track jobs/day and cost per job
4. **Optimize**: Add Modal or switch to dedicated based on data

---

**Last Updated**: 2025-12-05
**Author**: VaniKeys Infrastructure Team
**Status**: Production-Ready
