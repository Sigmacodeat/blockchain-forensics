# CryptoMetrics Analytics Pro

AppSumo Lifetime Deal Product

## Quick Start

```bash
cd appsumo-products/analytics-pro
docker-compose up
```

Frontend: http://localhost:3004
Backend API: http://localhost:8000

## Pricing

- Tier 1: $79
- Tier 2: $149
- Tier 3: $249

## Status

✅ MVP Ready for AppSumo Launch

## Optional: Main Backend Integration (Firewall & Deep Scan)

Enable proxy to the main platform for real security analytics:

1) Configure env in `backend/.env`:
```
MAIN_BACKEND_URL=http://host.docker.internal:8001
# Optional if protected:
MAIN_BACKEND_API_KEY=your-api-key
MAIN_BACKEND_JWT=your-jwt
```

2) Available proxy endpoints:
```
GET   /api/firewall/stats     # AI Firewall statistics
POST  /api/wallet/scan/deep   # Deep wallet scan (forensics-backed)
```
