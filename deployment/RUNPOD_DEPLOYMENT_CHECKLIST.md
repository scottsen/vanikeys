# VaniKeys RunPod Deployment Checklist

**Date**: 2025-12-05
**Container**: `registry.mytia.net/vanikeys-runpod:slim` (601MB)
**Status**: Ready to Deploy

---

## Prerequisites ✅

- ✅ Container built and pushed to private registry
- ✅ Handler tested locally (`deployment/runpod_handler.py`)
- ✅ Registry credentials available
- ✅ Deployment decision documented

---

## Step 1: Create RunPod Account

### 1.1 Sign Up
- [ ] Go to https://www.runpod.io/console/serverless
- [ ] Click "Sign Up" (use GitHub or email)
- [ ] Verify email if required

### 1.2 Add Payment Method
- [ ] Dashboard → Billing → Payment Methods
- [ ] Add credit card (no charge until usage)
- [ ] Confirm payment method active

### 1.3 Get API Key
- [ ] Dashboard → Settings → API Keys
- [ ] Click "Create API Key"
- [ ] Name: `vanikeys-production`
- [ ] Copy the key (starts with `RUNPOD_...`)
- [ ] **Save it** - you'll need this in Step 4

---

## Step 2: Create Serverless Endpoint

### 2.1 Navigate to Serverless
- [ ] Go to https://www.runpod.io/console/serverless
- [ ] Click "New Endpoint" or "+ Create Endpoint"

### 2.2 Basic Configuration
- [ ] **Name**: `vanikeys-gacha`
- [ ] **GPU Type**: RTX 4090
  - Cost: $0.0057/minute
  - Optimal for VaniKeys workload
- [ ] **Container Disk**: 10GB

### 2.3 Container Configuration

**Container Image:**
```
registry.mytia.net/vanikeys-runpod:slim
```

**Container Registry Type:** Private Registry

**Registry Configuration:**
```
Registry URL: registry.mytia.net
Username: tia-deploy
Password: qNrP/jpSCisvEeiwKOpQusU94ja5JnTK
```

- [ ] Enter container image path
- [ ] Select "Private Registry"
- [ ] Enter registry URL: `registry.mytia.net`
- [ ] Enter username: `tia-deploy`
- [ ] Enter password: `qNrP/jpSCisvEeiwKOpQusU94ja5JnTK`
- [ ] Click "Test Connection" (if available)

### 2.4 Scaling Configuration

**Workers:**
- [ ] **Min Workers**: 0 (scale to zero when idle)
- [ ] **Max Workers**: 10 (adjust based on traffic)

**Timeouts:**
- [ ] **Idle Timeout**: 5 seconds (fast scale-down)
- [ ] **Max Runtime**: 3600 seconds (1 hour for guaranteed mode)

### 2.5 Advanced Settings (Optional)

**Environment Variables:** (None required - handler uses input params)

**Startup Command:** (Use default - handler auto-starts)

### 2.6 Deploy
- [ ] Review all settings
- [ ] Click "Deploy" or "Create Endpoint"
- [ ] Wait for deployment (1-3 minutes)
- [ ] **Copy the Endpoint ID** (format: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`)

---

## Step 3: Test the Endpoint

### 3.1 Get Credentials
You should now have:
- [ ] RunPod API Key (from Step 1.3)
- [ ] RunPod Endpoint ID (from Step 2.6)

### 3.2 Run Test Script

**Option A: Quick Test (Manual)**

```bash
cd /home/scottsen/src/projects/vanikeys

# Set credentials
export RUNPOD_API_KEY="your-api-key-here"
export RUNPOD_ENDPOINT_ID="your-endpoint-id-here"

# Run test
python deployment/test_runpod.py
```

**Option B: Store in TIA Secrets First** (Recommended)

```bash
# Store credentials
tia secrets set runpod:api_key "your-api-key-here"
tia secrets set runpod:endpoint_id "your-endpoint-id-here"

# Run test (reads from TIA secrets)
export RUNPOD_API_KEY=$(tia secrets get runpod:api_key)
export RUNPOD_ENDPOINT_ID=$(tia secrets get runpod:endpoint_id)
python deployment/test_runpod.py
```

### 3.3 Verify Test Results

Expected output:
```
Testing VaniKeys RunPod Endpoint
================================

Test 1: Gacha Mode (single attempt)
-----------------------------------
Submitting job...
Job ID: xxx-xxx-xxx
Waiting for result...
✓ Success!
  Pattern: GO BE AWE SOME
  Found: True/False
  Score: X.XX
  Path: m/44'/60'/0'/0/xxxxx
  Fingerprint: SHA256:xxxxxxxxxxxxxxxxx
  Attempts: 1
  Duration: X.XXs

Test 2: Guaranteed Mode (limited attempts)
-------------------------------------------
Submitting job...
...
```

- [ ] Test 1 (Gacha) completes in <2 seconds
- [ ] Test 2 (Guaranteed) runs and returns result
- [ ] No errors in output
- [ ] Fingerprints are valid SSH format

---

## Step 4: Store Credentials in TIA Secrets

```bash
# Store RunPod credentials
tia secrets set runpod:api_key "YOUR_API_KEY_HERE"
tia secrets set runpod:endpoint_id "YOUR_ENDPOINT_ID_HERE"

# Verify stored
tia secrets get runpod:api_key
tia secrets get runpod:endpoint_id
```

- [ ] API key stored
- [ ] Endpoint ID stored
- [ ] Verification successful

---

## Step 5: Update Project Documentation

### 5.1 Update VaniKeys README
- [ ] Add deployment status to project README
- [ ] Note: RunPod endpoint active

### 5.2 Commit Deployment Status
```bash
cd /home/scottsen/src/projects/vanikeys

# Add deployment decision doc
git add DEPLOYMENT_DECISION.md
git add deployment/RUNPOD_DEPLOYMENT_CHECKLIST.md

# Commit
git commit -m "docs: Add RunPod deployment decision and checklist"
```

---

## Step 6: Monitor Initial Usage

### 6.1 Check RunPod Dashboard
- [ ] Go to RunPod Console → Serverless
- [ ] Click on `vanikeys-gacha` endpoint
- [ ] Verify metrics:
  - Workers: 0 (idle)
  - Total Runs: 2+ (from tests)
  - Current Cost: ~$0.01-0.02

### 6.2 Monitor for 24 Hours
- [ ] Run occasional test jobs
- [ ] Verify cold start times <500ms
- [ ] Confirm workers scale to 0 after idle timeout
- [ ] Check costs match expectations

---

## Troubleshooting

### Container Pull Failed
**Symptom**: "Failed to pull image" error

**Solutions**:
- Verify registry credentials are correct
- Check registry URL is `registry.mytia.net` (no `https://`)
- Ensure container tag is `:slim` not `:latest`
- Test: `podman pull registry.mytia.net/vanikeys-runpod:slim` on local machine

### Test Job Hangs
**Symptom**: Job status stuck at "IN_QUEUE" or "IN_PROGRESS"

**Solutions**:
- Check RunPod console for error logs
- Verify GPU type is available (try different region)
- Increase max runtime to 3600 seconds
- Check container logs in RunPod dashboard

### Authentication Errors
**Symptom**: "Invalid API key" or "Unauthorized"

**Solutions**:
- Verify API key copied correctly (no spaces)
- Regenerate API key in RunPod dashboard
- Check API key has correct permissions

### Pattern Not Matching
**Symptom**: Test returns `found: false` always

**Solutions**:
- Pattern matching is probabilistic - try multiple tests
- Use fuzzy mode: `fuzzy: true`
- Try simpler pattern: "GO BE"
- Check handler logs in RunPod console

---

## Success Criteria

- [ ] RunPod account created and active
- [ ] Serverless endpoint deployed and running
- [ ] Container pulled successfully from private registry
- [ ] Test jobs complete successfully (both gacha and guaranteed modes)
- [ ] Credentials stored in TIA secrets
- [ ] Workers scale to 0 when idle
- [ ] Cold start <500ms
- [ ] Costs tracking correctly (~$0.01 per test job)

---

## Next Steps (Phase 2)

After successful deployment:

1. **Build VaniKeys Web API** (Week 1-6)
   - Reference: `docs/PHASE2_IMPLEMENTATION_PLAN.md`
   - FastHTML frontend
   - PostgreSQL + Redis
   - Stripe payments
   - Integration with RunPod endpoint

2. **Beta Testing** (Week 7-8)
   - 10-50 users
   - Real money transactions
   - Monitor costs vs projections

3. **Production Launch** (Week 9+)
   - Product Hunt launch
   - Social media marketing
   - Scale monitoring

---

## Cost Tracking

### Expected MVP Costs (100 jobs/day)
| Service | Cost/month |
|---------|-----------|
| RunPod GPU | $24 |
| Redis (Upstash) | $20 |
| Web Hosting (DO) | $12 |
| AI (Together.ai) | $13 |
| **Total** | **$69** |

### Current Spend (Test Phase)
- Tests run: 0
- Total cost: $0.00
- Next billing: (will update after tests)

---

## Support Resources

- **RunPod Docs**: https://docs.runpod.io/serverless/overview
- **RunPod Discord**: https://discord.gg/runpod
- **VaniKeys Deployment**: `docs/SERVERLESS_GPU_OPTIONS.md`
- **TIA Secrets**: `tia secrets --help`

---

**Status**: Ready to Deploy ✅
**Next Action**: Create RunPod account (Step 1)
**Estimated Time**: 1 hour total
