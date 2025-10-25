# nft-manager

## Status: Production Ready ✅

Features implemented:
- Full Dashboard
- Real Features
- API Integration
- Beautiful UI

Launch: http://localhost:300X

## Optional: Main Backend Integration (Portfolio Risk Assessment)

Enable proxy to the main platform for real wallet risk analysis:

1) Configure env in `backend/.env`:
```
MAIN_BACKEND_URL=http://host.docker.internal:8001
# Optional if protected:
MAIN_BACKEND_API_KEY=your-api-key
MAIN_BACKEND_JWT=your-jwt
```

2) Available proxy endpoint:
```
POST  /api/portfolio/risk    # NFT portfolio risk assessment
```
