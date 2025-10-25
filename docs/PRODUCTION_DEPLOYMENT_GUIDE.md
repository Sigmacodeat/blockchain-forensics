# Production Deployment Guide

**Version**: 2.0.0  
**Last Updated**: 2025-10-20  
**Status**: ✅ Launch Ready

## 🚀 Pre-Deployment Checklist

### 1. Environment Configuration

#### Required .env Variables (Backend)
```bash
# Critical - MUST be set
SECRET_KEY=<256-bit-random-string>          # ⚠️ Generate: openssl rand -hex 32
JWT_SECRET=<256-bit-random-string>          # ⚠️ Generate: openssl rand -hex 32
POSTGRES_PASSWORD=<strong-password>         # ⚠️ Change from default
NEO4J_PASSWORD=<strong-password>            # ⚠️ Change from default
NOWPAYMENTS_API_KEY=<production-key>        # ⚠️ Get from NOWPayments
NOWPAYMENTS_IPN_SECRET=<webhook-secret>     # ⚠️ From NOWPayments dashboard

# Blockchain RPCs - MUST use production endpoints
ETHEREUM_RPC_URL=https://mainnet.infura.io/v3/<KEY>
ETHEREUM_WS_URL=wss://mainnet.infura.io/ws/v3/<KEY>
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com

# AI Services
OPENAI_API_KEY=sk-...                       # ⚠️ Production key

# OAuth (Optional but recommended)
GOOGLE_CLIENT_ID=<google-oauth-id>
GOOGLE_CLIENT_SECRET=<google-oauth-secret>

# Monitoring (Optional but recommended)
SENTRY_DSN=https://...@sentry.io/...
```

#### Environment-Specific Settings
```bash
# Production overrides
ENVIRONMENT=production
DEBUG=false
JSON_LOGS=true
LOG_LEVEL=INFO
CORS_ORIGINS=https://your-domain.com,https://www.your-domain.com

# Security
NOWPAYMENTS_SANDBOX=false                   # ⚠️ CRITICAL: Must be false in production
ENABLE_AGENT_TOOL_RBAC=true                 # Recommended for security
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000

# Performance
ENABLE_ML_CLUSTERING=true
ENABLE_KAFKA_STREAMING=true
```

### 2. Database Setup

#### PostgreSQL (TimescaleDB)
```bash
# Port 5432 internally, exposed as needed
# Database: blockchain_forensics
# User: forensics
# ⚠️ Change default password!

# Apply migrations
cd backend
alembic upgrade head
```

#### Neo4j
```bash
# Port 7687 (Bolt)
# Default: neo4j / forensics_password_change_me
# ⚠️ Change password in production!

# Memory configuration (adjust for your server)
NEO4J_dbms_memory_heap_max__size=4G
NEO4J_dbms_memory_pagecache_size=2G
```

#### Redis
```bash
# Port 6379 internally
# Used for: Session storage, rate limiting, caching
# ⚠️ Enable persistence in production
```

### 3. Docker Compose Services

#### Start Infrastructure Services
```bash
# Start databases first
docker-compose up -d postgres neo4j redis kafka

# Wait for health checks (check with)
docker-compose ps

# All should show "healthy" status
```

#### Verify Services
```bash
# PostgreSQL
docker exec -it blockchain-forensics-postgres-1 psql -U forensics -d blockchain_forensics -c "SELECT 1"

# Neo4j
docker exec -it blockchain-forensics-neo4j-1 cypher-shell -u neo4j -p <PASSWORD> "RETURN 1"

# Redis
docker exec -it blockchain-forensics-redis-1 redis-cli ping
```

### 4. Application Deployment

#### Backend
```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start with production settings
uvicorn app.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4 \
  --log-level info \
  --no-access-log  # Use structured logs instead
```

#### Frontend
```bash
cd frontend

# Install dependencies
npm ci  # Use ci for production (faster, deterministic)

# Build for production
npm run build

# Serve with nginx or CDN
# See: infra/nginx/nginx.conf
```

### 5. Health Checks

All services have health check endpoints:

#### Backend API
```bash
curl http://localhost:8000/health
# Expected: {"status":"healthy","version":"2.0.0"}

curl http://localhost:8000/api/healthz
# Expected: Detailed service status
```

#### Monitoring
```bash
# Prometheus
curl http://localhost:9090/-/healthy

# Grafana
curl http://localhost:3003/api/health
```

### 6. Security Hardening

#### SSL/TLS
```bash
# ⚠️ CRITICAL: Use HTTPS in production
# Configure at reverse proxy (nginx/Traefik)
# Cert: Let's Encrypt via certbot

# Backend: Set FORCE_HTTPS_REDIRECT=true
# Frontend: Serve only via HTTPS
```

#### Firewall Rules
```bash
# Allow only necessary ports
# Production: 80 (HTTP→HTTPS), 443 (HTTPS)
# Monitoring: 9090 (Prometheus - internal only)
# Database ports: Internal Docker network only
```

#### Secrets Management
```bash
# ⚠️ NEVER commit .env to git
# Use secret management: Vault, AWS Secrets Manager, etc.
# Rotate secrets quarterly

# Verify no secrets in codebase
git secrets --scan
```

### 7. Monitoring Setup

#### Prometheus + Grafana
```bash
# Start monitoring stack
docker-compose up -d prometheus grafana

# Access Grafana
http://localhost:3003
# Default: admin / admin (⚠️ Change immediately!)

# Import dashboards from:
monitoring/grafana-dashboard*.json
```

#### Sentry (Errors)
```bash
# Set SENTRY_DSN in .env
# All uncaught exceptions will be reported
# Review Sentry dashboard daily
```

### 8. Performance Optimization

#### Database Indexing
```sql
-- Run after initial data load
-- See: backend/app/db/optimizations.py

-- Neo4j
CREATE INDEX ON :Address(address);
CREATE INDEX ON :Transaction(hash);

-- PostgreSQL
CREATE INDEX idx_cases_created_at ON cases(created_at);
CREATE INDEX idx_crypto_payments_status ON crypto_payments(payment_status);
```

#### Caching Strategy
```python
# Redis caching enabled by default
# Cache TTL: 300s (5 min) for most queries
# Adjust in: backend/app/services/performance_cache.py
```

### 9. Backup Strategy

#### Database Backups
```bash
# PostgreSQL (daily)
docker exec blockchain-forensics-postgres-1 \
  pg_dump -U forensics blockchain_forensics \
  > backup_$(date +%Y%m%d).sql

# Neo4j (weekly)
docker exec blockchain-forensics-neo4j-1 \
  neo4j-admin dump --database=neo4j \
  --to=/backups/neo4j_$(date +%Y%m%d).dump
```

#### Retention Policy
- Daily backups: Keep 7 days
- Weekly backups: Keep 4 weeks
- Monthly backups: Keep 12 months

### 10. Post-Deployment Verification

#### Smoke Tests
```bash
# Backend API
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test"}'

# AI Chat
curl http://localhost:8000/api/v1/chat

# Crypto Payments
curl http://localhost:8000/api/v1/crypto-payments/currencies
```

#### E2E Tests (Post-Deploy)
```bash
cd frontend
PLAYWRIGHT_BASE_URL=https://your-domain.com npm run test:e2e
# Expected: 5/5 pass
```

#### Load Test (Optional)
```bash
# Use k6 or Apache Bench
k6 run scripts/load-test.js
# Target: <200ms p95, <500ms p99
```

## 🔥 Rollback Procedure

If deployment fails:

1. **Stop new version**
   ```bash
   docker-compose down
   ```

2. **Restore previous version**
   ```bash
   git checkout <previous-tag>
   docker-compose up -d
   ```

3. **Restore database** (if migrations ran)
   ```bash
   # PostgreSQL
   psql -U forensics blockchain_forensics < backup_latest.sql
   
   # Neo4j
   neo4j-admin load --from=backup_latest.dump
   ```

4. **Verify health checks** pass

5. **Investigate issues** before next deploy

## 📊 Production Monitoring

### Key Metrics to Watch

- **API Latency**: p50 <50ms, p95 <200ms, p99 <500ms
- **Error Rate**: <0.1%
- **Database Connections**: <50% pool size
- **Redis Hit Rate**: >80%
- **Kafka Lag**: <1000 messages
- **Disk Usage**: <70%
- **Memory Usage**: <80%

### Alert Thresholds

- Error rate >1%: **Page immediately**
- API latency p99 >1s: **Warn**
- Database connections >80%: **Warn**
- Disk usage >85%: **Critical**

## 🆘 Emergency Contacts

- **DevOps Lead**: [Contact Info]
- **Backend Lead**: [Contact Info]
- **On-Call**: [PagerDuty/OpsGenie]
- **Hosting Provider**: [AWS/GCP Support]

## 📚 Additional Documentation

- Network Architecture: `docs/ARCHITECTURE.md`
- API Documentation: `/docs` endpoint (production disabled, use `/api/v1/openapi.json`)
- Troubleshooting: `docs/TROUBLESHOOTING.md`
- Runbooks: `docs/runbooks/`

---

**Deployment Verified**: [Date]  
**Deployed By**: [Name]  
**Next Review**: 1 week post-launch
