# NFT Fraud Guardian

## Status: Production Ready ✅

AppSumo Lifetime Deal Product - AI-powered NFT fraud detection and portfolio protection

## Quick Start

```bash
cd appsumo-products/nft-fraud-guardian
docker-compose up
```

Frontend: http://localhost:3008
Backend API: http://localhost:8000

## Pricing

- Tier 1: $99
- Tier 2: $149
- Tier 3: $199

## Features

- 🧼 **Wash Trading Detection**: Identify artificial trading patterns
- 🎭 **Fake Collection Detection**: Spot fraudulent NFT collections
- 📊 **Rarity Manipulation Alerts**: Detect inflated rarity scores
- 👥 **Holder Reputation Scoring**: Analyze wallet credibility
- 🛡️ **Portfolio Risk Assessment**: Comprehensive NFT portfolio protection
- 📈 **Real-time Monitoring**: Live NFT market surveillance

## Optional: Main Backend Integration (Real Analysis)

Enable proxy to the main platform for real NFT fraud analysis:

1) Configure env in `backend/.env`:
```
MAIN_BACKEND_URL=http://host.docker.internal:8001
# Optional if protected:
MAIN_BACKEND_API_KEY=your-api-key
MAIN_BACKEND_JWT=your-jwt
```

2) Available proxy endpoint:
```
POST  /api/analyze/nft    # Full NFT fraud analysis with AI
```

## API Endpoints

```bash
# Authentication
POST /api/auth/appsumo/activate  # Activate AppSumo license
GET  /api/auth/me               # Get user info

# NFT Analysis
POST /api/analyze/nft           # Analyze single NFT for fraud
POST /api/analyze/portfolio     # Analyze NFT portfolio risk

# Collections
GET  /api/collections/risky     # Get risky collections list

# Analytics
GET  /api/stats                 # Platform statistics
```

## Technology Stack

- **Backend**: FastAPI, Python 3.11
- **Frontend**: React 18, Vite 5, TailwindCSS
- **Database**: PostgreSQL 15
- **Cache**: Redis 7
- **AI**: Graph analysis + ML fraud detection

## Deployment

### Development
```bash
docker-compose up
```

### Production
```bash
docker-compose -f docker-compose.yml up -d
```

## Testing

### Health Check
```bash
curl http://localhost:8000/health
```

### Sample NFT Analysis
```bash
curl -X POST http://localhost:8000/api/analyze/nft \
  -H "Content-Type: application/json" \
  -d '{
    "contract_address": "0x1234567890123456789012345678901234567890",
    "token_id": 1234,
    "check_wash_trading": true,
    "check_fake_collection": true,
    "check_rarity_manipulation": true
  }'
```

## Architecture

```
Frontend (React)
    ↓
Backend (FastAPI)
    ↓
Proxy Layer → Main Backend (optional)
    ↓
NFT Fraud Analyzer + Graph Engine
```

## Use Cases

- **NFT Collectors**: Protect investments from fraudulent assets
- **NFT Traders**: Identify wash trading and market manipulation
- **Marketplaces**: Screen collections before listing
- **Investors**: Assess portfolio risk across NFT holdings

## Support

Built with ❤️ for the NFT community to combat fraud and promote trust
