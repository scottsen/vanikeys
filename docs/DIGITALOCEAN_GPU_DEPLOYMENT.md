# VaniKeys DigitalOcean GPU Deployment Guide

**Last Updated**: 2025-12-05
**Status**: Production-Ready
**Recommended For**: >5K jobs/day (post-MVP scale)

---

## Executive Summary

DigitalOcean GPU Droplets provide dedicated GPU compute for VaniKeys when serverless becomes more expensive (breakeven: ~5K jobs/day).

**When to Use DigitalOcean GPU**:
- ✅ Consistent volume >5K jobs/day
- ✅ Need predictable costs
- ✅ Want control over infrastructure
- ✅ Enterprise compliance requirements

**Cost**: $1,095-$2,995/month depending on GPU tier

---

## GPU Droplet Options

### RTX 4000 Ada Generation (Recommended for VaniKeys)

**Specs**:
- GPU: NVIDIA RTX 4000 Ada (20GB VRAM)
- Performance: ~40M keys/sec
- vCPUs: 8
- RAM: 30GB
- Storage: 200GB NVMe SSD
- **Price**: $1,095/month

**Best For**: VaniKeys production workload (5K-20K jobs/day)

### H100 (Overkill for VaniKeys, but available)

**Specs**:
- GPU: NVIDIA H100 (80GB HBM3)
- Performance: ~200M keys/sec
- vCPUs: 24
- RAM: 200GB
- Storage: 1TB NVMe SSD
- **Price**: $2,995/month

**Best For**: Extreme scale (>50K jobs/day) or research

---

## Architecture: Hybrid GPU + CPU Workers

```
┌─────────────────────────────────────┐
│      VaniKeys Load Balancer         │
│     (HAProxy / Nginx)               │
└─────────────────────────────────────┘
                 │
         ┌───────┴────────┐
         │                │
    ┌────▼────────┐  ┌────▼──────┐
    │   Gacha     │  │ Guaranteed│
    │   Queue     │  │   Queue   │
    └────┬────────┘  └────┬──────┘
         │                │
    ┌────▼─────────────┐  │
    │  GPU Worker Pool │  │
    │  (DigitalOcean)  │  │
    │                  │  │
    │  RTX 4000 Ada    │◄─┘
    │  40M keys/sec    │
    │                  │
    │  Workers: 4-8    │
    │  (multi-process) │
    └──────────────────┘
```

**Key Design**:
- Single GPU droplet running 4-8 worker processes
- Redis queue for job distribution
- FastHTML web app on separate droplet
- Autoscaling: Add more GPU droplets as needed

---

## Deployment Guide

### Step 1: Create GPU Droplet

#### Using DigitalOcean Console

1. Go to https://cloud.digitalocean.com/droplets/new
2. Select:
   - **Region**: NYC3 or SFO3 (GPU availability)
   - **Image**: Ubuntu 22.04 LTS
   - **Plan**: GPU-Optimized
   - **GPU**: RTX 4000 Ada ($1,095/mo)
   - **Authentication**: SSH key
   - **Hostname**: vanikeys-gpu-1

3. Click "Create Droplet"

#### Using doctl CLI

```bash
# Install doctl
brew install doctl  # macOS
# Or: https://docs.digitalocean.com/reference/doctl/how-to/install/

# Authenticate
doctl auth init

# Create GPU droplet
doctl compute droplet create vanikeys-gpu-1 \
  --region nyc3 \
  --size gpu-rtx4000ada-8vcpu-30gb \
  --image ubuntu-22-04-x64 \
  --ssh-keys YOUR_SSH_KEY_ID \
  --wait

# Get droplet IP
doctl compute droplet list --format Name,PublicIPv4
```

### Step 2: Install NVIDIA Drivers & CUDA

SSH into droplet:

```bash
ssh root@YOUR_DROPLET_IP
```

Install drivers:

```bash
# Update system
apt update && apt upgrade -y

# Install NVIDIA drivers
apt install -y nvidia-driver-535

# Reboot to load drivers
reboot

# After reboot, verify
nvidia-smi
# Should show RTX 4000 Ada

# Install CUDA Toolkit
wget https://developer.download.nvidia.com/compute/cuda/12.2.0/local_installers/cuda_12.2.0_535.54.03_linux.run
sh cuda_12.2.0_535.54.03_linux.run --silent --toolkit

# Add to PATH
echo 'export PATH=/usr/local/cuda-12.2/bin:$PATH' >> ~/.bashrc
echo 'export LD_LIBRARY_PATH=/usr/local/cuda-12.2/lib64:$LD_LIBRARY_PATH' >> ~/.bashrc
source ~/.bashrc

# Verify CUDA
nvcc --version
```

### Step 3: Install Dependencies

```bash
# Install Python 3.11
apt install -y software-properties-common
add-apt-repository ppa:deadsnakes/ppa -y
apt update
apt install -y python3.11 python3.11-venv python3.11-dev

# Install Redis (for job queue)
apt install -y redis-server
systemctl enable redis-server
systemctl start redis-server

# Install Git
apt install -y git

# Clone VaniKeys
cd /opt
git clone https://github.com/yourusername/vanikeys.git
cd vanikeys

# Create venv
python3.11 -m venv venv
source venv/bin/activate

# Install VaniKeys
pip install -e .

# Install GPU acceleration libraries (if using GPU version)
pip install cupy-cuda12x  # For GPU-accelerated numpy operations
```

### Step 4: Create Worker Service

Create `/opt/vanikeys/gpu_worker.py`:

```python
#!/usr/bin/env python3
"""
VaniKeys GPU Worker for DigitalOcean GPU Droplet.

Processes jobs from Redis queue using GPU acceleration.
"""

import redis
import json
import sys
import os
import signal
import time
from typing import Dict, Any

sys.path.insert(0, '/opt/vanikeys/src')

from vanikeys.crypto import (
    seed_to_keypair_at_path,
    compute_ssh_fingerprint
)
from vanikeys.matchers.multi_substring import MultiSubstringMatcher

# Redis connection
redis_client = redis.Redis(
    host=os.getenv('REDIS_HOST', 'localhost'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    db=0,
    decode_responses=True
)

# Graceful shutdown
shutdown_requested = False

def signal_handler(signum, frame):
    global shutdown_requested
    print("Shutdown requested, finishing current job...")
    shutdown_requested = True

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

def process_job(job_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process a vanity key job."""
    job_id = job_data['job_id']
    pattern = job_data['pattern']
    mode = job_data.get('mode', 'gacha')
    fuzzy = job_data.get('fuzzy', False)
    seed_hash = job_data['master_seed_hash']

    print(f"[{job_id}] Processing: {pattern} ({mode} mode)")

    substrings = pattern.upper().split()
    matcher = MultiSubstringMatcher(
        substrings=substrings,
        fuzzy=fuzzy,
        case_insensitive=True
    )

    attempts = 0
    max_attempts = 1 if mode == 'gacha' else 10_000_000_000
    start_path = job_data.get('start_path', 0)

    start_time = time.time()

    while attempts < max_attempts and not shutdown_requested:
        path = start_path + attempts

        priv_key, pub_key = seed_to_keypair_at_path(
            seed_hash.encode(),
            path
        )

        fingerprint = compute_ssh_fingerprint(pub_key)
        fingerprint_b58 = fingerprint.split(':')[1]

        match_result = matcher.match(fingerprint_b58)
        attempts += 1

        # Gacha mode: return after 1 attempt
        if mode == 'gacha':
            duration = time.time() - start_time
            result = {
                'status': 'success',
                'job_id': job_id,
                'found': match_result.score > 0,
                'path': path,
                'fingerprint': fingerprint,
                'match_score': match_result.score,
                'attempts': attempts,
                'duration_seconds': duration
            }
            print(f"[{job_id}] Completed in {duration:.2f}s")
            return result

        # Guaranteed mode: continue until exact match
        if match_result.score == 1.0:
            duration = time.time() - start_time
            result = {
                'status': 'success',
                'job_id': job_id,
                'found': True,
                'path': path,
                'fingerprint': fingerprint,
                'match_score': 1.0,
                'attempts': attempts,
                'duration_seconds': duration
            }
            print(f"[{job_id}] Found match after {attempts:,} attempts ({duration:.1f}s)")
            return result

        # Progress updates every 10M attempts
        if attempts % 10_000_000 == 0:
            elapsed = time.time() - start_time
            rate = attempts / elapsed
            print(f"[{job_id}] Progress: {attempts:,} attempts ({rate:.0f} keys/sec)")

            # Update job status in Redis
            redis_client.hset(
                f"job:{job_id}:status",
                mapping={
                    'attempts': attempts,
                    'rate': int(rate),
                    'elapsed': int(elapsed)
                }
            )

    # Shutdown requested or max attempts
    return {
        'status': 'incomplete',
        'job_id': job_id,
        'attempts': attempts,
        'message': 'Worker shutdown' if shutdown_requested else 'Max attempts reached'
    }

def main():
    """Main worker loop."""
    worker_id = os.getenv('WORKER_ID', 'worker-1')
    print(f"VaniKeys GPU Worker {worker_id} starting...")
    print(f"Redis: {os.getenv('REDIS_HOST', 'localhost')}:{os.getenv('REDIS_PORT', 6379)}")

    # Register worker
    redis_client.sadd('vanikeys:workers', worker_id)
    redis_client.hset(f'vanikeys:worker:{worker_id}', 'status', 'idle')

    while not shutdown_requested:
        try:
            # Block waiting for job (30 second timeout)
            job_data_raw = redis_client.brpop('vanikeys:job_queue', timeout=30)

            if job_data_raw is None:
                # No jobs, continue waiting
                continue

            _, job_json = job_data_raw
            job_data = json.loads(job_json)

            # Mark worker as busy
            redis_client.hset(f'vanikeys:worker:{worker_id}', 'status', 'busy')
            redis_client.hset(f'vanikeys:worker:{worker_id}', 'current_job', job_data['job_id'])

            # Process job
            result = process_job(job_data)

            # Store result
            redis_client.set(
                f"job:{job_data['job_id']}:result",
                json.dumps(result),
                ex=3600  # Expire after 1 hour
            )

            # Publish completion event
            redis_client.publish('vanikeys:job_completed', job_data['job_id'])

            # Mark worker as idle
            redis_client.hset(f'vanikeys:worker:{worker_id}', 'status', 'idle')
            redis_client.hdel(f'vanikeys:worker:{worker_id}', 'current_job')

        except Exception as e:
            print(f"Error processing job: {e}")
            redis_client.hset(f'vanikeys:worker:{worker_id}', 'status', 'error')
            time.sleep(5)

    # Cleanup on shutdown
    redis_client.srem('vanikeys:workers', worker_id)
    redis_client.delete(f'vanikeys:worker:{worker_id}')
    print(f"Worker {worker_id} shutdown complete")

if __name__ == '__main__':
    main()
```

### Step 5: Create Systemd Service

Create `/etc/systemd/system/vanikeys-worker@.service`:

```ini
[Unit]
Description=VaniKeys GPU Worker %i
After=network.target redis-server.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/vanikeys
Environment="WORKER_ID=worker-%i"
Environment="REDIS_HOST=localhost"
Environment="REDIS_PORT=6379"
ExecStart=/opt/vanikeys/venv/bin/python /opt/vanikeys/gpu_worker.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start workers (4 workers for RTX 4000 Ada):

```bash
# Enable 4 worker instances
systemctl enable vanikeys-worker@{1..4}

# Start workers
systemctl start vanikeys-worker@{1..4}

# Check status
systemctl status vanikeys-worker@*

# View logs
journalctl -u vanikeys-worker@1 -f
```

### Step 6: Configure Firewall

```bash
# Install UFW
apt install -y ufw

# Allow SSH
ufw allow 22/tcp

# Allow Redis (only from your web server IP)
ufw allow from YOUR_WEB_SERVER_IP to any port 6379

# Enable firewall
ufw enable
```

---

## Monitoring & Metrics

### GPU Monitoring

```bash
# Install nvidia-smi monitoring
watch -n 1 nvidia-smi

# Or use htop with GPU support
apt install -y nvtop
nvtop
```

### Worker Monitoring

```bash
# Check worker status via Redis
redis-cli SMEMBERS vanikeys:workers

# Check individual worker
redis-cli HGETALL vanikeys:worker:worker-1

# Check queue length
redis-cli LLEN vanikeys:job_queue
```

### Create Monitoring Dashboard

```python
# monitor.py - Simple worker monitoring
import redis
import time
import os

redis_client = redis.Redis(host='localhost', decode_responses=True)

while True:
    os.system('clear')
    print("VaniKeys GPU Worker Status")
    print("=" * 60)

    workers = redis_client.smembers('vanikeys:workers')
    print(f"Active Workers: {len(workers)}")

    for worker_id in workers:
        status = redis_client.hgetall(f'vanikeys:worker:{worker_id}')
        print(f"  {worker_id}: {status.get('status', 'unknown')}", end='')
        if status.get('current_job'):
            print(f" (Job: {status['current_job']})")
        else:
            print()

    queue_len = redis_client.llen('vanikeys:job_queue')
    print(f"\nPending Jobs: {queue_len}")

    time.sleep(2)
```

---

## Cost Analysis

### Breakeven Analysis

**Dedicated GPU** (RTX 4000 Ada):
- Fixed cost: $1,095/month
- Performance: 40M keys/sec
- Cost per job: $0.024 (amortized over 45,000 jobs/month)

**RunPod Serverless**:
- Variable cost: $0.008/job
- Breakeven: 136,875 jobs/month (4,562 jobs/day)

**Recommendation**:
- <5K jobs/day: Use serverless
- >5K jobs/day: Use dedicated GPU
- >10K jobs/day: Multiple GPUs or hybrid

---

## Scaling Strategy

### Horizontal Scaling (Multiple GPUs)

```bash
# Create additional GPU droplets
doctl compute droplet create vanikeys-gpu-2 \
  --region nyc3 \
  --size gpu-rtx4000ada-8vcpu-30gb \
  --image ubuntu-22-04-x64 \
  --ssh-keys YOUR_SSH_KEY_ID

# Configure workers to point to central Redis
# Set REDIS_HOST=your-redis-server-ip
```

### Hybrid Architecture (Dedicated + Serverless Burst)

```
Baseline Traffic (5K jobs/day)
    ↓
DigitalOcean GPU (handles baseline)
    ↓
Overflow Traffic (spikes, viral events)
    ↓
RunPod Serverless (handles burst)
```

**Implementation**:
```python
# Smart routing based on queue depth
def route_job(job):
    queue_depth = redis_client.llen('vanikeys:job_queue')

    if queue_depth < 100:
        # Use dedicated GPU
        redis_client.lpush('vanikeys:job_queue', job)
    else:
        # Overflow to serverless
        runpod_service.submit_job(job)
```

---

## Maintenance

### Updates

```bash
# Update VaniKeys code
cd /opt/vanikeys
git pull
source venv/bin/activate
pip install -e .

# Restart workers
systemctl restart vanikeys-worker@*
```

### Backups

```bash
# Backup Redis data
redis-cli --rdb /opt/backups/redis-$(date +%Y%m%d).rdb

# Backup VaniKeys config
tar -czf /opt/backups/vanikeys-config-$(date +%Y%m%d).tar.gz /opt/vanikeys
```

---

## Troubleshooting

### Workers Not Starting

```bash
# Check service logs
journalctl -u vanikeys-worker@1 -n 50

# Check Redis connectivity
redis-cli ping

# Check GPU availability
nvidia-smi
```

### Low Performance

```bash
# Check GPU utilization
nvidia-smi dmon

# Verify CUDA is working
python3 -c "import cupy; print(cupy.cuda.runtime.getDeviceCount())"

# Check for throttling
nvidia-smi -q -d PERFORMANCE
```

---

## Next Steps

1. **Deploy Single GPU** following this guide
2. **Monitor performance** for 1 month
3. **Add more GPUs** if queue depth consistently >100
4. **Consider hybrid** (dedicated + serverless) for optimal cost

**See Also**:
- `SERVERLESS_GPU_OPTIONS.md` - Serverless GPU guide
- `COMPUTE_OPTIONS_COMPARISON.md` - Quick decision matrix

---

**Last Updated**: 2025-12-05
**Author**: VaniKeys Infrastructure Team
**Status**: Production-Ready
