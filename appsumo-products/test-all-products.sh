#!/bin/bash

echo "🧪 TESTING ALL 12 APPSUMO PRODUCTS"
echo "===================================="
echo ""

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

products=(
    "8001:ChatBot Pro"
    "8002:Wallet Guardian"
    "8003:Analytics Pro"
    "8004:Transaction Inspector"
    "8005:Dashboard Commander"
    "8006:NFT Manager"
    "8007:DeFi Tracker"
    "8008:Tax Reporter"
    "8009:Agency Reseller"
    "8010:Power Suite"
    "8011:Complete Security"
    "8012:Trader Pack"
)

passed=0
failed=0

for item in "${products[@]}"; do
    port="${item%%:*}"
    name="${item##*:}"
    
    echo -n "Testing $name (port $port)... "
    
    # Try to connect to backend
    response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:$port/health 2>/dev/null)
    
    if [ "$response" = "200" ]; then
        echo -e "${GREEN}✅ PASS${NC}"
        ((passed++))
    else
        echo -e "${RED}❌ FAIL (not running)${NC}"
        ((failed++))
    fi
done

echo ""
echo "===================================="
echo -e "Results: ${GREEN}$passed passed${NC}, ${RED}$failed failed${NC}"
echo "===================================="

if [ $failed -eq 0 ]; then
    echo -e "${GREEN}🎉 ALL PRODUCTS HEALTHY!${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠️  Some products are not running. Start them with docker-compose.${NC}"
    exit 1
fi
