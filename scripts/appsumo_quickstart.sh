#!/bin/bash
# AppSumo Quick-Start Script
# Führt alle notwendigen Setup-Schritte aus

set -e  # Exit on error

echo "🚀 AppSumo Multi-Product System - Quick Start"
echo "================================================"
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo -e "${RED}❌ Error: Must be run from project root${NC}"
    exit 1
fi

echo -e "${BLUE}Step 1: Checking Backend...${NC}"
cd backend

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate venv
source venv/bin/activate

# Check Python syntax
echo "Validating Python code..."
python -m py_compile app/models/appsumo.py
python -m py_compile app/services/appsumo_service.py
python -m py_compile app/api/v1/appsumo.py
echo -e "${GREEN}✅ Backend code validated${NC}"

# Check if DB is running
echo ""
echo -e "${BLUE}Step 2: Checking Database...${NC}"
if pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
    echo -e "${GREEN}✅ PostgreSQL is running${NC}"
    
    # Run migration
    echo "Running database migration..."
    alembic upgrade head
    echo -e "${GREEN}✅ Migration complete${NC}"
else
    echo -e "${RED}⚠️  PostgreSQL is not running${NC}"
    echo "Please start PostgreSQL first:"
    echo "  docker-compose up -d postgres"
    echo "  OR"
    echo "  brew services start postgresql"
    cd ..
    exit 1
fi

cd ..

echo ""
echo -e "${BLUE}Step 3: Checking Frontend...${NC}"
cd frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "Installing npm dependencies..."
    npm install
fi

echo -e "${GREEN}✅ Frontend ready${NC}"

cd ..

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Next steps:"
echo ""
echo "1. Start Backend:"
echo "   cd backend && uvicorn app.main:app --reload"
echo ""
echo "2. Start Frontend:"
echo "   cd frontend && npm run dev"
echo ""
echo "3. Test Admin Dashboard:"
echo "   Open: http://localhost:5173/en/admin/appsumo"
echo "   Generate test codes"
echo ""
echo "4. Test Redemption:"
echo "   Open: http://localhost:5173/en/redeem/appsumo"
echo "   Use a generated code"
echo ""
echo "API Documentation: http://localhost:8000/docs"
echo ""
echo -e "${GREEN}🎉 Ready to go!${NC}"
