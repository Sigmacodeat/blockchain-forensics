#!/bin/bash
# Quick Setup Script für Blockchain Forensics Platform
# Führt alle notwendigen Setup-Schritte automatisch aus

set -e  # Exit on error

echo "🚀 Blockchain Forensics Platform - Quick Setup"
echo "=============================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check prerequisites
echo "📋 Checking prerequisites..."

if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker nicht gefunden. Bitte installieren Sie Docker.${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose nicht gefunden.${NC}"
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 nicht gefunden.${NC}"
    exit 1
fi

if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js nicht gefunden.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Alle Voraussetzungen erfüllt${NC}"
echo ""

# Environment Setup
echo "🔧 Setting up environment..."

if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        cp .env.example .env
        echo -e "${YELLOW}⚠️  .env erstellt aus .env.example${NC}"
        echo -e "${YELLOW}⚠️  Bitte bearbeiten Sie .env und fügen Sie Ihre API-Keys hinzu:${NC}"
        echo "   - ETHEREUM_RPC_URL"
        echo "   - OPENAI_API_KEY"
        echo "   - JWT_SECRET (generiere mit: openssl rand -hex 32)"
        echo ""
        read -p "Drücken Sie Enter, wenn Sie bereit sind fortzufahren..."
    else
        echo -e "${RED}❌ .env.example nicht gefunden${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✅ .env bereits vorhanden${NC}"
fi

# Infrastructure
echo ""
echo "🐳 Starting Docker infrastructure..."
docker-compose up -d

echo -e "${YELLOW}⏳ Warte 30 Sekunden bis alle Services laufen...${NC}"
sleep 30

# Check services
echo ""
echo "📊 Checking services..."
docker-compose ps

# Backend Setup
echo ""
echo "🐍 Setting up Backend..."

cd backend

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo -e "${GREEN}✅ Backend setup complete${NC}"

# Database Migrations
echo ""
echo "🗄️  Running database migrations..."
alembic upgrade head || echo -e "${YELLOW}⚠️  Migrations skipped (optional)${NC}"

cd ..

# Frontend Setup
echo ""
echo "⚛️  Setting up Frontend..."

cd frontend

if [ ! -f .env.local ]; then
    echo "Creating frontend .env.local..."
    cat > .env.local << EOF
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
EOF
    echo -e "${GREEN}✅ Frontend .env.local created${NC}"
fi

echo "Installing Node dependencies..."
npm install

# Install graph visualization
echo "Installing vis-network for graph visualization..."
npm install vis-network vis-data

# Install UI dependencies
echo "Installing UI components..."
npm install @radix-ui/react-dialog @radix-ui/react-tabs @radix-ui/react-select

echo -e "${GREEN}✅ Frontend setup complete${NC}"

cd ..

# Success message
echo ""
echo "=============================================="
echo -e "${GREEN}🎉 Setup erfolgreich abgeschlossen!${NC}"
echo "=============================================="
echo ""
echo "📝 Nächste Schritte:"
echo ""
echo "1️⃣  Backend starten (Terminal 1):"
echo "   cd backend"
echo "   source venv/bin/activate"
echo "   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "2️⃣  Frontend starten (Terminal 2):"
echo "   cd frontend"
echo "   npm run dev"
echo ""
echo "3️⃣  Zugriff:"
echo "   🌐 Frontend:  http://localhost:3000"
echo "   📚 Backend:   http://localhost:8000/docs"
echo "   🔍 Neo4j:     http://localhost:7474"
echo ""
echo "📖 Dokumentation:"
echo "   - Installation:      ./INSTALLATION.md"
echo "   - Frontend-Features: ./FRONTEND_FEATURES.md"
echo "   - API-Docs:          http://localhost:8000/docs"
echo ""
echo -e "${YELLOW}⚠️  Vergessen Sie nicht, Ihre .env zu konfigurieren!${NC}"
echo ""
