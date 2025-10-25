# Crypto Transaction Inspector

AppSumo Lifetime Deal Product

## Quick Start

```bash
cd appsumo-products/transaction-inspector
docker-compose up
```

Frontend: http://localhost:3003
Backend API: http://localhost:8000

## Pricing

- Tier 1: $69
- Tier 2: $149
- Tier 3: $229

## Status

✅ MVP Ready for AppSumo Launch

## Optional: Main Backend Integration (Deep TX Scan)

Enable proxy to the main platform for real AI TX scanning:

1) Configure env in `backend/.env`:
```
MAIN_BACKEND_URL=http://host.docker.internal:8001
# Optional if protected:
MAIN_BACKEND_API_KEY=your-api-key
MAIN_BACKEND_JWT=your-jwt
```

2) Available proxy endpoint:
```
POST  /api/tx/scan    # AI Firewall transaction scan
```
