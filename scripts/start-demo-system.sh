#!/bin/bash
# Quick Start Script for Two-Tier Demo System (Development)
# ==========================================================

set -e  # Exit on error

echo "🚀 Starting Two-Tier Demo System..."
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

echo -e "${BLUE}📂 Project Root: $PROJECT_ROOT${NC}"
echo ""

# Step 1: Check if Docker is running
echo -e "${YELLOW}1️⃣  Checking Docker...${NC}"
if docker info > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Docker is running${NC}"
else
    echo "❌ Docker is not running. Please start Docker Desktop."
    exit 1
fi
echo ""

# Step 2: Start Database & Redis
echo -e "${YELLOW}2️⃣  Starting PostgreSQL & Redis...${NC}"
cd "$PROJECT_ROOT"
docker-compose up -d postgres redis
sleep 3
echo -e "${GREEN}✓ Database & Redis started${NC}"
echo ""

# Step 3: Run Database Migration
echo -e "${YELLOW}3️⃣  Running Database Migration...${NC}"
if [ -f "backend/migrations/versions/007_add_demo_user_fields.sql" ]; then
    docker-compose exec -T postgres psql -U postgres -d blockchain_forensics \
      < backend/migrations/versions/007_add_demo_user_fields.sql 2>&1 | grep -v "already exists" || true
    echo -e "${GREEN}✓ Migration completed${NC}"
else
    echo -e "${YELLOW}⚠ Migration file not found, skipping${NC}"
fi
echo ""

# Step 4: Install Backend Dependencies (optional)
echo -e "${YELLOW}4️⃣  Backend Dependencies...${NC}"
if [ -f "backend/requirements.txt" ]; then
    echo "  Checking Python dependencies..."
    # Check if virtual env exists
    if [ ! -d "backend/venv" ]; then
        echo "  Creating virtual environment..."
        cd backend && python3 -m venv venv && cd ..
    fi
    echo -e "${GREEN}✓ Backend dependencies ready${NC}"
else
    echo -e "${YELLOW}⚠ requirements.txt not found${NC}"
fi
echo ""

# Step 5: Start Backend
echo -e "${YELLOW}5️⃣  Starting Backend Server...${NC}"
cd "$PROJECT_ROOT/backend"

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "  Creating .env from .env.example..."
    cp .env.example .env 2>/dev/null || echo "# Auto-generated" > .env
fi

# Start backend in background
echo "  Starting FastAPI server..."
nohup uvicorn app.main:app --reload --port 8000 > /tmp/backend.log 2>&1 &
BACKEND_PID=$!
echo "  Backend PID: $BACKEND_PID"
sleep 3

# Check if backend is running
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Backend started on http://localhost:8000${NC}"
else
    echo -e "${YELLOW}⚠ Backend may still be starting...${NC}"
fi
echo ""

# Step 6: Install Frontend Dependencies
echo -e "${YELLOW}6️⃣  Frontend Dependencies...${NC}"
cd "$PROJECT_ROOT/frontend"
if [ ! -d "node_modules" ]; then
    echo "  Installing npm packages..."
    npm install --silent
else
    echo "  npm packages already installed"
fi
echo -e "${GREEN}✓ Frontend dependencies ready${NC}"
echo ""

# Step 7: Start Frontend
echo -e "${YELLOW}7️⃣  Starting Frontend Dev Server...${NC}"

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "  Creating .env..."
    echo "VITE_API_URL=http://localhost:8000" > .env
    echo "VITE_CHAT_WS_URL=ws://localhost:8000/api/v1/ws/chat" >> .env
fi

echo "  Starting Vite dev server..."
nohup npm run dev > /tmp/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "  Frontend PID: $FRONTEND_PID"
sleep 5

echo -e "${GREEN}✓ Frontend started on http://localhost:5173${NC}"
echo ""

# Step 8: Start CRON cleanup (in background)
echo -e "${YELLOW}8️⃣  Starting Demo Cleanup Service...${NC}"
cd "$PROJECT_ROOT/backend"

# Start cleanup loop
nohup bash -c 'while true; do python scripts/demo_cleanup.py; sleep 300; done' > /tmp/demo_cleanup.log 2>&1 &
CLEANUP_PID=$!
echo "  Cleanup PID: $CLEANUP_PID"
echo -e "${GREEN}✓ Cleanup service started (runs every 5 min)${NC}"
echo ""

# Summary
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}✅ Two-Tier Demo System is LIVE!${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🌐 Frontend:  http://localhost:5173"
echo "🔧 Backend:   http://localhost:8000"
echo "📚 API Docs:  http://localhost:8000/docs"
echo ""
echo "🎯 Demo URLs:"
echo "   Sandbox:   http://localhost:5173/en/demo/sandbox"
echo "   Live:      http://localhost:5173/en/demo/live"
echo ""
echo "📊 Process IDs:"
echo "   Backend:   $BACKEND_PID"
echo "   Frontend:  $FRONTEND_PID"
echo "   Cleanup:   $CLEANUP_PID"
echo ""
echo "📝 Logs:"
echo "   Backend:   tail -f /tmp/backend.log"
echo "   Frontend:  tail -f /tmp/frontend.log"
echo "   Cleanup:   tail -f /tmp/demo_cleanup.log"
echo ""
echo "🛑 To stop all services:"
echo "   kill $BACKEND_PID $FRONTEND_PID $CLEANUP_PID"
echo "   docker-compose down"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Save PIDs for cleanup script
echo "export BACKEND_PID=$BACKEND_PID" > /tmp/demo_system_pids.sh
echo "export FRONTEND_PID=$FRONTEND_PID" >> /tmp/demo_system_pids.sh
echo "export CLEANUP_PID=$CLEANUP_PID" >> /tmp/demo_system_pids.sh

echo -e "${BLUE}💡 Tip: Run './scripts/stop-demo-system.sh' to stop all services${NC}"
echo ""
