#!/bin/bash

# ============================================
# HEALTH MONITORING FOR ALL 12 PRODUCTS
# Runs continuous health checks
# ============================================

echo "🏥 HEALTH MONITOR - ALL 12 PRODUCTS"
echo "===================================="
echo ""

# Products
PRODUCTS=(
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

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Run once or continuously
MODE=${1:-once}
INTERVAL=${2:-60}

health_check() {
    healthy=0
    unhealthy=0
    
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Health Check"
    echo "----------------------------------------"
    
    for item in "${PRODUCTS[@]}"; do
        port="${item%%:*}"
        name="${item##*:}"
        
        response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:$port/health 2>/dev/null)
        
        if [ "$response" = "200" ]; then
            echo -e "${GREEN}✅${NC} $name (port $port) - HEALTHY"
            ((healthy++))
        else
            echo -e "${RED}❌${NC} $name (port $port) - UNHEALTHY"
            ((unhealthy++))
        fi
    done
    
    echo ""
    echo "Summary: ${GREEN}$healthy healthy${NC}, ${RED}$unhealthy unhealthy${NC}"
    echo ""
}

if [ "$MODE" = "continuous" ]; then
    echo "Running continuous monitoring (every ${INTERVAL}s)"
    echo "Press Ctrl+C to stop"
    echo ""
    
    while true; do
        health_check
        sleep $INTERVAL
    done
else
    health_check
fi
