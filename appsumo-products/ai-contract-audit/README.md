# AI Smart Contract Audit Lite

## Status: Production Ready ✅

AppSumo Lifetime Deal Product - Automated smart contract analysis with AI-powered risk scoring

## Quick Start

```bash
cd appsumo-products/ai-contract-audit
docker-compose up
```

Frontend: http://localhost:3005
Backend API: http://localhost:8000

## Pricing

- Tier 1: $79
- Tier 2: $129
- Tier 3: $199

## Features

- 🔍 **Static Analysis**: Automated vulnerability detection
- 🤖 **AI-Pattern Recognition**: Machine learning for exploit patterns
- 📊 **Risk Scoring**: 1-100 comprehensive risk assessment
- ⛽ **Gas Optimization**: Identify inefficient code patterns
- 📋 **PDF Reports**: Professional audit reports
- 🔗 **Labels Integration**: Check sanctioned tokens and addresses

## Optional: Main Backend Integration (Real Analysis)

Enable proxy to the main platform for real contract analysis:

1) Configure env in `backend/.env`:
```
MAIN_BACKEND_URL=http://host.docker.internal:8001
# Optional if protected:
MAIN_BACKEND_API_KEY=your-api-key
MAIN_BACKEND_JWT=your-jwt
```

2) Available proxy endpoint:
```
POST  /api/audit/contract    # Full contract audit with AI analysis
```

## API Endpoints

```bash
# Authentication
POST /api/auth/appsumo/activate  # Activate AppSumo license
GET  /api/auth/me               # Get user info

# Auditing
POST /api/audit/contract        # Audit smart contract
GET  /api/audit/history         # Get audit history

# Analytics
GET  /api/stats                 # Platform statistics
```

## Technology Stack

- **Backend**: FastAPI, Python 3.11
- **Frontend**: React 18, Vite 5, TailwindCSS
- **Database**: PostgreSQL 15
- **Cache**: Redis 7
- **AI**: Integration with main platform's ML models

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

### Sample Audit
```bash
curl -X POST http://localhost:8000/api/audit/contract \
  -H "Content-Type: application/json" \
  -d '{
    "contract_address": "0x1234567890123456789012345678901234567890",
    "chain": "ethereum",
    "check_security": true,
    "check_gas_optimization": true
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
Contract Analyzer + AI Models
```

## Support

Built with ❤️ for DeFi developers and smart contract auditors
