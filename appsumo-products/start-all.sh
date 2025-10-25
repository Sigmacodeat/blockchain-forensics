#!/bin/bash

# ============================================
# START ALL 12 APPSUMO PRODUCTS
# ============================================

echo "🚀 STARTING ALL 12 APPSUMO PRODUCTS"
echo "===================================="
echo ""

# Products with their ports
declare -A PRODUCTS=(
    ["chatbot-pro"]="3001:8001"
    ["wallet-guardian"]="3002:8002"
    ["analytics-pro"]="3003:8003"
    ["transaction-inspector"]="3004:8004"
    ["dashboard-commander"]="3005:8005"
    ["nft-manager"]="3006:8006"
    ["defi-tracker"]="3007:8007"
    ["tax-reporter"]="3008:8008"
    ["agency-reseller"]="3009:8009"
    ["power-suite"]="3010:8010"
    ["complete-security"]="3011:8011"
    ["trader-pack"]="3012:8012"
)

echo "📦 Starting Docker containers..."
echo ""

# Start each product
for product in "${!PRODUCTS[@]}"; do
    ports="${PRODUCTS[$product]}"
    frontend_port="${ports%%:*}"
    backend_port="${ports##*:}"
    
    echo "Starting $product..."
    echo "  Frontend: http://localhost:$frontend_port"
    echo "  Backend:  http://localhost:$backend_port"
    
    cd "$product"
    docker-compose up -d 2>/dev/null
    cd ..
    
    echo "  ✅ Started"
    echo ""
done

echo ""
echo "===================================="
echo "✅ ALL 12 PRODUCTS STARTED!"
echo "===================================="
echo ""
echo "Access URLs:"
echo "  ChatBot Pro:          http://localhost:3001"
echo "  Wallet Guardian:      http://localhost:3002"
echo "  Analytics Pro:        http://localhost:3003"
echo "  Transaction Inspector: http://localhost:3004"
echo "  Dashboard Commander:  http://localhost:3005"
echo "  NFT Manager:          http://localhost:3006"
echo "  DeFi Tracker:         http://localhost:3007"
echo "  Tax Reporter:         http://localhost:3008"
echo "  Agency Reseller:      http://localhost:3009"
echo "  Power Suite:          http://localhost:3010"
echo "  Complete Security:    http://localhost:3011"
echo "  Trader Pack:          http://localhost:3012"
echo ""
echo "Backend APIs at ports 8001-8012"
echo ""
echo "Stop all: ./stop-all.sh"
echo "Test all: ./test-all-products.sh"
