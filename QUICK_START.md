# Quick Start Guide

**Get up and running in 10 minutes** ⚡

## Prerequisites

- Docker & Docker Compose
- Node.js 18+ (for frontend)
- Python 3.10+ (for backend)
- Git

## 🚀 Installation

### 1. Clone Repository
```bash
git clone https://github.com/yourusername/blockchain-forensics.git
cd blockchain-forensics
```

### 2. Environment Setup
```bash
# Copy example environment
cp .env.example .env

# Edit .env and set:
# - SECRET_KEY (generate: openssl rand -hex 32)
# - JWT_SECRET (generate: openssl rand -hex 32)
# - ETHEREUM_RPC_URL (get free key from Infura/Alchemy)
# - OPENAI_API_KEY (for AI features)
```

### 3. Start Infrastructure
```bash
# Start databases (Postgres, Neo4j, Redis, Kafka)
docker-compose up -d postgres neo4j redis kafka

# Wait ~30 seconds for services to be healthy
docker-compose ps
```

### 4. Backend Setup
```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start backend
uvicorn app.main:app --reload --port 8000
```

Backend now running at: `http://localhost:8000`

### 5. Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

Frontend now running at: `http://localhost:5173`

## ✅ Verify Installation

### Check Backend
```bash
curl http://localhost:8000/health
# Expected: {"status":"healthy","version":"2.0.0"}
```

### Check Frontend
Open browser: `http://localhost:5173`

### Check Databases
```bash
# PostgreSQL
docker exec -it blockchain-forensics-postgres-1 psql -U forensics -d blockchain_forensics -c "SELECT 1"

# Neo4j
docker exec -it blockchain-forensics-neo4j-1 cypher-shell -u neo4j -p forensics_password_change_me "RETURN 1"

# Redis
docker exec -it blockchain-forensics-redis-1 redis-cli ping
```

## 🎯 First Steps

### 1. Create Account
- Navigate to `http://localhost:5173/register`
- Sign up with email + password
- Default plan: Community (free)

### 2. Try Transaction Tracing
```bash
# API Example
curl -X POST http://localhost:8000/api/v1/trace/start \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "source_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
    "chain": "ethereum",
    "max_depth": 3
  }'
```

Or use the UI:
1. Login at `/login`
2. Go to `/trace`
3. Enter Ethereum address
4. Click "Start Trace"

### 3. Explore AI Chat
- Click chat icon (bottom right)
- Try: "What are your features?"
- Try: "Check risk for 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"

## 🔧 Configuration

### Essential Environment Variables

```bash
# Backend (.env)
SECRET_KEY=<random-256-bit-string>
JWT_SECRET=<random-256-bit-string>
POSTGRES_URL=postgresql://forensics:forensics_pass@localhost:5435/blockchain_forensics
NEO4J_URI=bolt://localhost:7688
REDIS_URL=redis://localhost:6381/0
ETHEREUM_RPC_URL=https://mainnet.infura.io/v3/YOUR_KEY
OPENAI_API_KEY=sk-...

# Frontend (.env)
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

### Optional Features

```bash
# AI Agents
ENABLE_AI_AGENTS=true
OPENAI_MODEL=gpt-4-turbo-preview

# Crypto Payments (NOWPayments)
NOWPAYMENTS_API_KEY=your_key
NOWPAYMENTS_SANDBOX=true

# Google OAuth
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_secret
```

## 🎮 Development Workflow

### Backend Development
```bash
cd backend
source venv/bin/activate

# Run tests
pytest tests/ -v

# Type checking
mypy app/

# Linting
flake8 app/

# Format
black app/
```

### Frontend Development
```bash
cd frontend

# Run tests
npm test

# Type checking
npm run build  # Also checks types

# Linting
npm run lint

# Format
npx prettier --write src/
```

## 🐛 Troubleshooting

### Backend won't start
```bash
# Check database connections
docker-compose ps

# View backend logs
docker-compose logs backend

# Reset database
docker-compose down -v
docker-compose up -d postgres neo4j redis
alembic upgrade head
```

### Frontend build errors
```bash
# Clear cache
rm -rf node_modules package-lock.json
npm install

# Check Node version
node --version  # Should be 18+
```

### Port conflicts
```bash
# Check what's using ports
lsof -i :8000  # Backend
lsof -i :5173  # Frontend
lsof -i :5432  # Postgres

# Change ports in docker-compose.yml if needed
```

## 📚 Next Steps

- **Documentation**: Check `docs/` folder
- **API Docs**: `http://localhost:8000/docs` (Swagger UI)
- **Features Guide**: `docs/features/`
- **Deployment**: `docs/PRODUCTION_DEPLOYMENT_GUIDE.md`

## 🆘 Getting Help

- **Issues**: GitHub Issues
- **Docs**: `docs/` folder
- **Email**: support@example.com

## 🎉 You're Ready!

The platform is now running locally. Start tracing transactions, exploring the graph, and building your blockchain forensics workflow!

**Pro Tip**: Use the AI chat to learn features interactively 🤖
