# VaniKeys DigitalOcean GPU/CPU Deployment Guide

**Version**: 1.0
**Date**: 2025-11-17
**Status**: Implementation Ready

## Executive Summary

Deploy VaniKeys on DigitalOcean using their new **GPU Droplets** (2025) for secp256k1 key generation and **CPU-Optimized Droplets** for Ed25519 keys. This architecture provides 50M+ keys/sec throughput with 90%+ profit margins.

---

## Table of Contents

1. [Compute Options Overview](#compute-options-overview)
2. [Architecture Design](#architecture-design)
3. [Cost Analysis](#cost-analysis)
4. [Deployment Commands](#deployment-commands)
5. [Scaling Strategy](#scaling-strategy)
6. [Monitoring & Optimization](#monitoring--optimization)

---

## Compute Options Overview

### GPU Droplets (NEW 2025)

**Available GPUs**:
- **NVIDIA RTX 4000 Ada Generation**
  - Entry-level GPU for AI/ML workloads
  - ~$0.76-1.50/hour
  - Perfect for VaniKeys MVP

- **NVIDIA RTX 6000 Ada Generation**
  - High-performance GPU
  - ~$1.50-2.50/hour
  - Production scaling

- **NVIDIA L40S**
  - Data center GPU
  - ~$2-3/hour
  - Enterprise workloads

- **NVIDIA H100 Tensor Core**
  - Top-tier GPU
  - ~$3.44+/hour
  - Maximum performance

**Performance for VaniKeys**:
```
secp256k1 (Bitcoin/Ethereum):
- RTX 4000: ~50M keys/sec
- RTX 6000: ~100M keys/sec (estimated)
- H100: ~200M keys/sec (estimated)

Use Case: Guaranteed mode for high-value patterns
Cost: $0.035 per 4.2B attempt job (84 seconds @ 50M keys/sec)
Revenue: $6.30 (630 tokens guaranteed mode)
Profit: $6.26 per job (99.4% margin!)
```

### CPU-Optimized Droplets

**Premium CPU-Optimized Tiers**:

| Tier | vCPUs | RAM | Price/mo | Use Case |
|------|-------|-----|----------|----------|
| c-4  | 4     | 8GB | ~$48     | MVP/testing |
| c-8  | 8     | 16GB | ~$96    | Light production |
| c-16 | 16    | 32GB | ~$192   | Medium production |
| c-32 | 32    | 64GB | ~$384   | Heavy production |
| c-60 | 60    | 120GB | ~$720  | Maximum throughput |

**Performance for VaniKeys**:
```
Ed25519 (DIDs/Solana):
- c-16 (16 vCPUs): ~2M keys/sec (multi-core optimized)
- c-32 (32 vCPUs): ~4M keys/sec
- c-60 (60 vCPUs): ~7M keys/sec

Use Case: DID vanity generation (Phase 1 focus)
Cost: $0.02 per job (195K attempts @ 2M keys/sec)
Revenue: $1.00 (100 tokens)
Profit: $0.98 per job (98% margin)
```

**Key Features**:
- **10 Gbps network** (5x faster than regular droplets)
- **NVMe SSDs** (290% faster writes)
- **Dedicated vCPUs** (no noisy neighbors)
- **58% better single-core** performance
- **20% better multi-core** performance

---

## Architecture Design

### Hybrid Multi-Worker Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                    VaniKeys Production Stack                   │
└────────────────────────────────────────────────────────────────┘

┌─────────────┐                 ┌──────────────┐
│   Client    │────HTTPS────────▶│  tia-proxy   │
│  (Browser)  │                 │   (nginx)    │
└─────────────┘                 │ 164.90.128.28│
                                └──────┬───────┘
                                       │
                    ┌──────────────────┼──────────────────┐
                    │                  │                  │
         ┌──────────▼──────┐  ┌────────▼───────┐  ┌──────▼───────┐
         │  vanikeys-web   │  │ vanikeys-redis │  │ Load Balancer│
         │  (FastHTML)     │  │  (Queue/Cache) │  │              │
         │  tia-stickers   │  │                │  │              │
         └─────────┬───────┘  └────────┬───────┘  └──────┬───────┘
                   │                   │                  │
                   │         ┌─────────┴──────────────────┤
                   │         │                            │
         ┌─────────▼─────────▼──────┐      ┌──────────────▼────────┐
         │   WORKER POOL (GPU)      │      │  WORKER POOL (CPU)    │
         ├──────────────────────────┤      ├───────────────────────┤
         │                          │      │                       │
         │  ┌────────────────────┐  │      │  ┌─────────────────┐ │
         │  │ gpu-worker-1       │  │      │  │ cpu-worker-1    │ │
         │  │ RTX 4000 Ada       │  │      │  │ c-16 (16vCPU)   │ │
         │  │ secp256k1 only     │  │      │  │ Ed25519 only    │ │
         │  │ 50M keys/sec       │  │      │  │ 2M keys/sec     │ │
         │  └────────────────────┘  │      │  └─────────────────┘ │
         │                          │      │                       │
         │  ┌────────────────────┐  │      │  ┌─────────────────┐ │
         │  │ gpu-worker-2       │  │      │  │ cpu-worker-2    │ │
         │  │ RTX 4000 Ada       │  │      │  │ c-16 (16vCPU)   │ │
         │  │ secp256k1 only     │  │      │  │ Ed25519 only    │ │
         │  │ 50M keys/sec       │  │      │  │ 2M keys/sec     │ │
         │  └────────────────────┘  │      │  └─────────────────┘ │
         │                          │      │                       │
         │  [...scale to N]         │      │  [...scale to M]      │
         └──────────────────────────┘      └───────────────────────┘

         Total GPU Capacity:              Total CPU Capacity:
         N × 50M = 100M-500M keys/sec     M × 2M = 4M-20M keys/sec
```

### Job Routing Logic

```python
# Redis queue-based routing
def route_job(job):
    if job.key_type in ['bitcoin', 'ethereum', 'secp256k1']:
        # Route to GPU workers
        redis.lpush('vanikeys:queue:gpu', job)
    elif job.key_type in ['did:key', 'solana', 'ed25519']:
        # Route to CPU workers
        redis.lpush('vanikeys:queue:cpu', job)

    # Workers poll their respective queues
```

---

## Cost Analysis

### Phase 1: MVP (Month 1-3)

**Infrastructure**:
```
1x GPU Droplet (RTX 4000 Ada):
  - $1.50/hour × 730 hours = $1,095/mo
  - Capacity: 50M keys/sec (secp256k1)
  - Handles: ~500 guaranteed jobs/day

1x CPU Droplet (c-8, 8 vCPUs):
  - $96/mo
  - Capacity: 1M keys/sec (Ed25519)
  - Handles: ~1000 DID jobs/day

Existing Infrastructure:
  - tia-stickers (web app): $0 (already running)
  - tia-proxy (nginx): $0 (already running)
  - Redis: $20/mo (DigitalOcean Managed Redis)

Total: $1,211/mo
```

**Revenue Estimate**:
```
Conservative (100 jobs/day):
- 50 GPU jobs @ $6.30 avg = $315/day
- 50 CPU jobs @ $1.00 avg = $50/day
Total: $365/day × 30 = $10,950/mo

Profit: $10,950 - $1,211 = $9,739/mo (89% margin)
```

### Phase 2: Production (Month 3-6)

**Infrastructure**:
```
2x GPU Droplets (RTX 4000 Ada): $2,190/mo
2x CPU Droplets (c-16): $384/mo
Load Balancer: $12/mo
Managed Redis: $40/mo
Monitoring: $50/mo

Total: $2,676/mo
Capacity: 100M keys/sec (GPU), 4M keys/sec (CPU)
```

**Revenue Estimate**:
```
Moderate (500 jobs/day):
- 300 GPU jobs @ $6.30 = $1,890/day
- 200 CPU jobs @ $1.00 = $200/day
Total: $2,090/day × 30 = $62,700/mo

Profit: $62,700 - $2,676 = $60,024/mo (96% margin)
```

### Phase 3: Scale (Month 6-12)

**Infrastructure**:
```
4x GPU Droplets (RTX 6000 Ada): $7,300/mo
4x CPU Droplets (c-32): $1,536/mo
Kubernetes Cluster (DOKS): $500/mo
Managed Database: $100/mo
Monitoring/Logging: $200/mo

Total: $9,636/mo
Capacity: 400M keys/sec (GPU), 16M keys/sec (CPU)
```

**Revenue Estimate**:
```
Growth (2000 jobs/day):
- 1200 GPU jobs @ $6.30 = $7,560/day
- 800 CPU jobs @ $1.00 = $800/day
Total: $8,360/day × 30 = $250,800/mo

Profit: $250,800 - $9,636 = $241,164/mo (96% margin)
```

---

## Deployment Commands

### Prerequisites

```bash
# Install doctl (DigitalOcean CLI)
brew install doctl  # macOS
# or
curl -sL https://github.com/digitalocean/doctl/releases/download/v1.104.0/doctl-1.104.0-linux-amd64.tar.gz | tar -xzv
sudo mv doctl /usr/local/bin

# Authenticate
doctl auth init
# Enter your API token when prompted

# Verify
doctl account get
```

### Phase 1: MVP Deployment

#### Step 1: Create GPU Worker

```bash
# List available GPU images
doctl compute image list --public | grep -i gpu

# Create GPU droplet (RTX 4000 Ada)
doctl compute droplet create vanikeys-gpu-1 \
  --image gradient-pytorch-2.0-cuda-11.8 \
  --size gpu-h100x1-80gb \
  --region nyc3 \
  --enable-ipv6 \
  --enable-monitoring \
  --ssh-keys $(doctl compute ssh-key list --format ID --no-header) \
  --wait

# Get IP address
doctl compute droplet list | grep vanikeys-gpu-1

# SSH in and setup
ssh root@<GPU_IP>

# Install VaniKeys worker
git clone https://github.com/your-org/vanikeys.git
cd vanikeys
pip install -e .

# Install GPU-optimized libraries
pip install cupy-cuda11x  # CUDA-accelerated NumPy
pip install pycuda

# Configure worker
cat > /etc/vanikeys-worker.conf << EOF
WORKER_TYPE=gpu
WORKER_ID=gpu-1
REDIS_URL=redis://your-redis-host:6379
QUEUE_NAME=vanikeys:queue:gpu
KEY_TYPES=secp256k1,bitcoin,ethereum
CUDA_DEVICE=0
EOF

# Create systemd service
cat > /etc/systemd/system/vanikeys-gpu-worker.service << EOF
[Unit]
Description=VaniKeys GPU Worker
After=network.target

[Service]
Type=simple
User=vanikeys
WorkingDirectory=/opt/vanikeys
EnvironmentFile=/etc/vanikeys-worker.conf
ExecStart=/usr/bin/python3 -m vanikeys.workers.gpu_worker
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Start worker
systemctl enable vanikeys-gpu-worker
systemctl start vanikeys-gpu-worker
systemctl status vanikeys-gpu-worker
```

#### Step 2: Create CPU Worker

```bash
# Create CPU-optimized droplet
doctl compute droplet create vanikeys-cpu-1 \
  --image ubuntu-22-04-x64 \
  --size c-8 \
  --region nyc3 \
  --enable-ipv6 \
  --enable-monitoring \
  --ssh-keys $(doctl compute ssh-key list --format ID --no-header) \
  --wait

# Get IP
doctl compute droplet list | grep vanikeys-cpu-1

# SSH and setup
ssh root@<CPU_IP>

# Install VaniKeys
git clone https://github.com/your-org/vanikeys.git
cd vanikeys
pip install -e .

# Configure CPU worker
cat > /etc/vanikeys-worker.conf << EOF
WORKER_TYPE=cpu
WORKER_ID=cpu-1
REDIS_URL=redis://your-redis-host:6379
QUEUE_NAME=vanikeys:queue:cpu
KEY_TYPES=ed25519,did:key,solana
CPU_CORES=8
EOF

# Create systemd service
cat > /etc/systemd/system/vanikeys-cpu-worker.service << EOF
[Unit]
Description=VaniKeys CPU Worker
After=network.target

[Service]
Type=simple
User=vanikeys
WorkingDirectory=/opt/vanikeys
EnvironmentFile=/etc/vanikeys-worker.conf
ExecStart=/usr/bin/python3 -m vanikeys.workers.cpu_worker
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Start worker
systemctl enable vanikeys-cpu-worker
systemctl start vanikeys-cpu-worker
```

#### Step 3: Setup Managed Redis

```bash
# Create managed Redis database
doctl databases create vanikeys-redis \
  --engine redis \
  --region nyc3 \
  --size db-s-1vcpu-1gb \
  --num-nodes 1 \
  --version 7

# Get connection details
doctl databases connection vanikeys-redis \
  --format Host,Port,User,Password

# Update worker configs with Redis URL
```

#### Step 4: Configure Load Balancer (Optional)

```bash
# Create load balancer for multiple workers
doctl compute load-balancer create \
  --name vanikeys-workers-lb \
  --region nyc3 \
  --forwarding-rules entry_protocol:http,entry_port:80,target_protocol:http,target_port:8011 \
  --health-check protocol:http,port:8011,path:/health \
  --droplet-ids $(doctl compute droplet list --format ID --no-header | tr '\n' ',')
```

### Phase 2: Kubernetes Deployment (Advanced)

```bash
# Create Kubernetes cluster
doctl kubernetes cluster create vanikeys-prod \
  --region nyc3 \
  --version 1.28.2-do.0 \
  --node-pool "name=gpu-workers;size=gpu-h100x1-80gb;count=2;auto-scale=true;min-nodes=1;max-nodes=5" \
  --node-pool "name=cpu-workers;size=c-16;count=2;auto-scale=true;min-nodes=1;max-nodes=8" \
  --wait

# Get kubeconfig
doctl kubernetes cluster kubeconfig save vanikeys-prod

# Deploy VaniKeys via Helm
helm repo add vanikeys https://charts.vanikeys.com
helm install vanikeys vanikeys/vanikeys \
  --set gpu.workers=2 \
  --set cpu.workers=2 \
  --set redis.url=$REDIS_URL

# Check status
kubectl get pods -n vanikeys
kubectl logs -f deployment/vanikeys-gpu-worker
```

---

## Scaling Strategy

### Horizontal Scaling

**When to scale GPU workers**:
- Queue depth > 100 guaranteed jobs
- Average wait time > 10 minutes
- Revenue > $20K/mo (can afford more GPUs)

```bash
# Add GPU worker
doctl compute droplet create vanikeys-gpu-2 \
  --image gradient-pytorch-2.0-cuda-11.8 \
  --size gpu-h100x1-80gb \
  --region nyc3 \
  --user-data-file gpu-worker-cloud-init.yaml

# Kubernetes auto-scales automatically based on queue depth
```

**When to scale CPU workers**:
- Queue depth > 500 DID jobs
- CPU utilization > 80%
- DID revenue > $5K/mo

```bash
# Add CPU worker
doctl compute droplet create vanikeys-cpu-3 \
  --image ubuntu-22-04-x64 \
  --size c-16 \
  --region nyc3 \
  --user-data-file cpu-worker-cloud-init.yaml
```

### Vertical Scaling

**GPU upgrades**:
```bash
# Upgrade RTX 4000 → RTX 6000 (2x performance)
# Requires creating new droplet (can't resize GPU droplets)

# Create new droplet
doctl compute droplet create vanikeys-gpu-1-upgraded \
  --image gradient-pytorch-2.0-cuda-11.8 \
  --size gpu-h100x2-160gb \  # Larger GPU
  --region nyc3

# Migrate traffic, delete old droplet
```

**CPU upgrades**:
```bash
# Resize CPU droplet (c-8 → c-16)
doctl compute droplet-action resize <DROPLET_ID> \
  --size c-16 \
  --resize-disk
```

### Geographic Scaling

```bash
# Deploy workers in multiple regions for global coverage
doctl compute droplet create vanikeys-gpu-eu \
  --image gradient-pytorch-2.0-cuda-11.8 \
  --size gpu-h100x1-80gb \
  --region lon1  # London

doctl compute droplet create vanikeys-gpu-asia \
  --image gradient-pytorch-2.0-cuda-11.8 \
  --size gpu-h100x1-80gb \
  --region sgp1  # Singapore

# Route jobs to nearest worker
```

---

## Monitoring & Optimization

### Performance Monitoring

```bash
# Install Prometheus + Grafana
doctl compute droplet create monitoring \
  --image ubuntu-22-04-x64 \
  --size s-2vcpu-4gb \
  --region nyc3

# Setup monitoring stack
docker-compose up -d prometheus grafana

# Configure worker metrics
# Each worker exposes /metrics endpoint
# Prometheus scrapes: keys/sec, queue depth, job completion time
```

### Key Metrics to Track

**Worker Performance**:
- Keys generated per second (keys/sec)
- GPU utilization (%)
- CPU utilization (%)
- Memory usage (GB)
- Queue processing time (seconds)

**Business Metrics**:
- Jobs completed per day
- Average job duration
- Revenue per worker
- Cost per job
- Profit margin (%)

**Queue Health**:
- Queue depth (pending jobs)
- Average wait time
- Worker idle time
- Job timeout rate

### Cost Optimization

**Auto-shutdown during low demand**:
```bash
# Scale down GPU workers at night (if demand is low)
crontab -e
0 23 * * * doctl compute droplet-action power-off <GPU_DROPLET_ID>  # 11 PM
0 7 * * * doctl compute droplet-action power-on <GPU_DROPLET_ID>    # 7 AM

# Save ~$12/day per GPU ($360/mo)
```

**Reserved pricing**:
- GPU Droplets: Reserve for 1-3 years for 30-50% discount
- Best for: Baseline capacity (keep 1-2 GPUs always on)

**Spot instances** (if available):
- Use spot/preemptible instances for gacha mode (non-critical)
- Use on-demand for guaranteed mode (critical)

---

## Worker Implementation

### GPU Worker (Python)

```python
# vanikeys/workers/gpu_worker.py
import os
import redis
import json
import cupy as cp  # CUDA-accelerated NumPy
from vanikeys.core.engine import VanityEngine
from vanikeys.generators.secp256k1_gpu import Secp256k1GPUGenerator

class GPUWorker:
    def __init__(self):
        self.redis = redis.from_url(os.getenv('REDIS_URL'))
        self.queue_name = os.getenv('QUEUE_NAME', 'vanikeys:queue:gpu')
        self.worker_id = os.getenv('WORKER_ID', 'gpu-1')
        self.cuda_device = int(os.getenv('CUDA_DEVICE', 0))

        # Initialize GPU generator
        self.generator = Secp256k1GPUGenerator(device=self.cuda_device)

    def run(self):
        print(f"GPU Worker {self.worker_id} started on CUDA device {self.cuda_device}")

        while True:
            # Pop job from queue (blocking)
            job_data = self.redis.brpop(self.queue_name, timeout=5)

            if not job_data:
                continue

            job = json.loads(job_data[1])
            print(f"Processing job {job['id']}: {job['pattern']}")

            # Process job
            result = self.process_job(job)

            # Store result
            self.redis.setex(
                f"vanikeys:result:{job['id']}",
                3600,  # 1 hour TTL
                json.dumps(result)
            )

            # Publish completion event
            self.redis.publish(
                f"vanikeys:complete:{job['id']}",
                json.dumps(result)
            )

    def process_job(self, job):
        mode = job.get('mode', 'gacha')

        if mode == 'gacha':
            # Single pull
            key = self.generator.generate()
            match_result = self.matcher.match(key.public_key_base58)
            return {
                'job_id': job['id'],
                'key': key.to_dict(),
                'match': match_result.to_dict(),
                'attempts': 1
            }
        else:
            # Guaranteed mode - grind until match
            attempts = 0
            while True:
                key = self.generator.generate()
                match_result = self.matcher.match(key.public_key_base58)
                attempts += 1

                if match_result.score == 1.0:
                    # Exact match found!
                    return {
                        'job_id': job['id'],
                        'key': key.to_dict(),
                        'match': match_result.to_dict(),
                        'attempts': attempts
                    }

                # Update progress every 1M attempts
                if attempts % 1_000_000 == 0:
                    self.redis.publish(
                        f"vanikeys:progress:{job['id']}",
                        json.dumps({'attempts': attempts})
                    )

if __name__ == '__main__':
    worker = GPUWorker()
    worker.run()
```

### CPU Worker (Python)

```python
# vanikeys/workers/cpu_worker.py
import os
import redis
import json
import multiprocessing as mp
from vanikeys.generators.ed25519 import Ed25519Generator

class CPUWorker:
    def __init__(self):
        self.redis = redis.from_url(os.getenv('REDIS_URL'))
        self.queue_name = os.getenv('QUEUE_NAME', 'vanikeys:queue:cpu')
        self.worker_id = os.getenv('WORKER_ID', 'cpu-1')
        self.cpu_cores = int(os.getenv('CPU_CORES', mp.cpu_count()))

        # Initialize generator
        self.generator = Ed25519Generator()

    def run(self):
        print(f"CPU Worker {self.worker_id} started with {self.cpu_cores} cores")

        # Create worker pool
        pool = mp.Pool(processes=self.cpu_cores)

        while True:
            job_data = self.redis.brpop(self.queue_name, timeout=5)

            if not job_data:
                continue

            job = json.loads(job_data[1])
            print(f"Processing job {job['id']}: {job['pattern']}")

            # Process in parallel across cores
            result = self.process_job_parallel(job, pool)

            # Store result
            self.redis.setex(
                f"vanikeys:result:{job['id']}",
                3600,
                json.dumps(result)
            )

            # Publish completion
            self.redis.publish(
                f"vanikeys:complete:{job['id']}",
                json.dumps(result)
            )

    def process_job_parallel(self, job, pool):
        # Distribute work across CPU cores
        # Each core generates keys independently

        if job.get('mode') == 'gacha':
            # Single attempt
            key = self.generator.generate()
            match_result = self.matcher.match(key.public_key_base58)
            return {
                'job_id': job['id'],
                'key': key.to_dict(),
                'match': match_result.to_dict(),
                'attempts': 1
            }
        else:
            # Guaranteed mode - parallel search
            # Use multiprocessing to search in parallel
            results = pool.map(
                self.search_worker,
                [(job, i) for i in range(self.cpu_cores)]
            )

            # Return first successful result
            for result in results:
                if result:
                    return result

if __name__ == '__main__':
    worker = CPUWorker()
    worker.run()
```

---

## Quick Reference

### Common Commands

```bash
# List all VaniKeys droplets
doctl compute droplet list | grep vanikeys

# Check worker status
ssh root@<WORKER_IP> systemctl status vanikeys-*-worker

# View worker logs
ssh root@<WORKER_IP> journalctl -u vanikeys-gpu-worker -f

# Check queue depth
redis-cli -h <REDIS_HOST> llen vanikeys:queue:gpu
redis-cli -h <REDIS_HOST> llen vanikeys:queue:cpu

# Monitor GPU usage
ssh root@<GPU_IP> nvidia-smi -l 1

# Monitor CPU usage
ssh root@<CPU_IP> htop
```

### Troubleshooting

**GPU worker not starting**:
```bash
# Check CUDA installation
nvidia-smi
nvcc --version

# Check GPU libraries
python3 -c "import cupy; print(cupy.cuda.runtime.getDeviceCount())"

# View full logs
journalctl -u vanikeys-gpu-worker --no-pager -n 100
```

**High queue depth**:
```bash
# Check worker health
systemctl status vanikeys-*-worker

# Add more workers
# See "Horizontal Scaling" section above

# Check Redis connection
redis-cli -h <REDIS_HOST> ping
```

**Low performance**:
```bash
# GPU: Check utilization
nvidia-smi

# CPU: Check core usage
htop

# Network: Check bandwidth
iftop

# Optimize worker code (profile with py-spy)
py-spy record -o profile.svg -- python3 -m vanikeys.workers.gpu_worker
```

---

## Next Steps

1. **Deploy MVP** (this week):
   - Create 1x GPU + 1x CPU droplet
   - Setup Redis queue
   - Deploy workers
   - Test end-to-end

2. **Monitor Performance** (week 2):
   - Track keys/sec
   - Measure job completion times
   - Calculate actual costs

3. **Optimize** (week 3):
   - Tune GPU batch sizes
   - Optimize CPU parallelization
   - Reduce network latency

4. **Scale** (month 2+):
   - Add workers based on demand
   - Implement auto-scaling
   - Deploy multi-region

---

## Resources

- **DigitalOcean GPU Docs**: https://www.digitalocean.com/products/gradient/gpu-droplets
- **DigitalOcean CPU Docs**: https://www.digitalocean.com/products/droplets/cpu-optimized
- **doctl CLI Reference**: https://docs.digitalocean.com/reference/doctl/
- **VaniKeys Architecture**: `docs/ARCHITECTURE.md`
- **VaniKeys Deployment**: `docs/DEPLOYMENT_PLAN.md`

---

**Document Status**: Ready for Implementation
**Next Action**: Deploy MVP GPU + CPU workers
**Owner**: VaniKeys Infrastructure Team
**Last Updated**: 2025-11-17
