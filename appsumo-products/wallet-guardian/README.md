# Web3 Wallet Guardian

AppSumo Lifetime Deal Product

## Quick Start

```bash
cd appsumo-products/wallet-guardian
docker-compose up
```

Frontend: http://localhost:3002
Backend API: http://localhost:8000

## Pricing

- Tier 1: $79
- Tier 2: $149
- Tier 3: $249

## Status

✅ MVP Ready for AppSumo Launch

## Optional: Main Backend Integration (Deep Protection)

Enable proxy to the main platform for real AI/Forensics features:

1) Configure env in `backend/.env`:
```
MAIN_BACKEND_URL=http://host.docker.internal:8000
# Optional if protected:
MAIN_BACKEND_API_KEY=your-api-key
MAIN_BACKEND_JWT=your-jwt
```

2) Available proxy endpoints:
```
POST  /api/scan/deep            # Address deep scan (forensics-backed)
POST  /api/tx/scan              # AI Firewall transaction scan
POST  /api/trace/start          # Start forensic trace
GET   /api/trace/{id}/report    # Download JSON/CSV/PDF report
```
