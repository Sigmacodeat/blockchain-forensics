#!/bin/bash
# Quick Start Script für Top 3 AppSumo Produkte

echo "🚀 Starting Top 3 AppSumo Products"
echo "===================================="
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to start a product
start_product() {
    local name=$1
    local folder=$2
    local backend_port=$3
    local frontend_port=$4
    
    echo -e "${BLUE}Starting $name...${NC}"
    
    # Start Backend
    cd "$folder/backend"
    echo "  Backend on port $backend_port"
    python -m app.main > /tmp/$folder-backend.log 2>&1 &
    echo $! > /tmp/$folder-backend.pid
    
    # Start Frontend
    cd "../frontend"
    echo "  Frontend on port $frontend_port"
    npm run dev > /tmp/$folder-frontend.log 2>&1 &
    echo $! > /tmp/$folder-frontend.pid
    
    cd ../..
    echo -e "${GREEN}✅ $name started${NC}"
    echo ""
}

# Check if shared modules exist
if [ ! -d "shared" ]; then
    echo -e "${YELLOW}⚠️  Warning: shared/ directory not found${NC}"
    echo "Please make sure you're in the appsumo-products directory"
    exit 1
fi

# Start all 3 products
start_product "ChatBot Pro" "chatbot-pro" "8001" "3001"
start_product "Wallet Guardian" "wallet-guardian" "8002" "3002"
start_product "Analytics Pro" "analytics-pro" "8003" "3003"

echo "===================================="
echo -e "${GREEN}🎉 All products started!${NC}"
echo ""
echo "📝 Access URLs:"
echo "  • ChatBot Pro:      http://localhost:3001"
echo "  • Wallet Guardian:  http://localhost:3002"
echo "  • Analytics Pro:    http://localhost:3003"
echo ""
echo "🔑 Activation Pages:"
echo "  • ChatBot Pro:      http://localhost:3001/activate"
echo "  • Wallet Guardian:  http://localhost:3002/activate"
echo "  • Analytics Pro:    http://localhost:3003/activate"
echo ""
echo "🧪 Test License Keys:"
echo "  • Tier 1: TEST-TEST-TEST-TES1"
echo "  • Tier 2: ABCD-EFGH-IJKL-MNO2"
echo "  • Tier 3: XXXX-YYYY-ZZZZ-WWW3"
echo ""
echo "📋 Logs in /tmp/*-{backend,frontend}.log"
echo "🛑 To stop: ./STOP_ALL_TOP3.sh"
echo ""
echo "✅ Ready for AppSumo! 🚀"
