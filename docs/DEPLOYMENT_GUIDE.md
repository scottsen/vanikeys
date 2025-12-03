# VaniKeys Deployment Guide

**Status**: Draft - To be completed during implementation

Quick reference for deploying VaniKeys through local → staging → production.

---

## Quick Start (Local Development)

```bash
# Setup
cd /home/scottsen/src/projects/vanikeys
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"

# Infrastructure
docker-compose up -d  # PostgreSQL + Redis

# Run
python -m vanikeys.app --reload

# Verify
curl http://localhost:8000/health
```

---

## Environments

### Local Development
- **Purpose**: Rapid development and testing
- **Path**: `/home/scottsen/src/projects/vanikeys`
- **Port**: 8000
- **Database**: Local PostgreSQL (Docker)
- **Redis**: Local Redis (Docker)

### Staging (tia-dev)
- **Purpose**: Pre-production validation
- **Server**: tia-dev
- **Domain**: TBD
- **Port**: TBD
- **Minimum validation**: 3 days before production

### Production (tia-apps)
- **Purpose**: Live business operations
- **Server**: tia-apps
- **Domain**: TBD
- **Port**: TBD
- **Deployment strategy**: Blue-green (zero downtime)

---

## Deployment Scripts

### Staging Deployment
```bash
./deployment/deploy-staging.sh
```

### Production Deployment
```bash
./deployment/deploy-production.sh v1.0.0
```

### Rollback
```bash
./deployment/rollback.sh
```

---

## Infrastructure

### Required Services
- **PostgreSQL 14+**: User data, pulls, transactions
- **Redis 7+**: Job queue, caching
- **RunPod Serverless**: GPU compute (gacha mode)
- **Modal**: GPU compute (guaranteed mode)
- **Stripe**: Payment processing
- **Together.ai**: AI features

### Infrastructure Cost (MVP)
```yaml
RunPod: $24/month (100 jobs/day)
Together.ai: $13/month (AI features)
Hosting: $12/month
Redis: $20/month
Total: $69/month
```

---

## Health Checks

### Endpoints
```bash
# Local
curl http://localhost:8000/health

# Staging
curl http://[staging-domain]/health

# Production
curl https://[production-domain]/health
```

### Expected Response
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "environment": "production",
  "uptime_seconds": 86400,
  "database": "connected",
  "redis": "connected"
}
```

---

## Monitoring

### Key Metrics
- Response time: <500ms (p95)
- Error rate: <0.1%
- Uptime: >99.9%
- Pull success rate: >95%

### Logs
```bash
# View logs (production)
ssh tia-apps 'tail -f /opt/vanikeys/logs/app.log'

# Using TIA process management
tia process logs vanikeys-production --tail
```

---

## Rollback Procedures

### Blue-Green Rollback (Instant)
```bash
# Switch traffic back to previous environment
./deployment/rollback.sh
```

### Verify Rollback
```bash
curl https://[production-domain]/health
```

---

## Next Steps

This is a scaffold deployment guide. Complete sections during implementation:

- [ ] Add actual server IPs and domains
- [ ] Create deployment scripts
- [ ] Document database migration process
- [ ] Add RunPod/Modal setup instructions
- [ ] Document Stripe integration
- [ ] Add monitoring setup (alerts, dashboards)
- [ ] Test rollback procedures
- [ ] Document disaster recovery

**Reference**: Use TIA Deployment Guide Template (`/home/scottsen/src/tia/docs/guides/deployment/TIA_DEPLOYMENT_GUIDE_TEMPLATE.md`) for complete structure.

---

**Version**: 0.1.0 (Scaffold)
**Status**: Draft - Complete during Phase 2 implementation
**Last Updated**: 2025-12-03
