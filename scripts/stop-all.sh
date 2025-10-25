#!/bin/bash

# 🛑 STOP ALL SERVICES
# Gracefully stops all Docker containers
# Version: 1.0.0

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════════════════╗"
echo "║   🛑 STOPPING ALL SERVICES                           ║"
echo "╚═══════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Function to stop service
stop_service() {
    local dir=$1
    local name=$2
    
    if [ -d "$dir" ] && [ -f "$dir/docker-compose.yml" ]; then
        echo -e "${YELLOW}Stopping ${name}...${NC}"
        cd "$dir"
        docker-compose down
        cd - > /dev/null
        echo -e "${GREEN}✅ ${name} stopped${NC}"
    else
        echo -e "${YELLOW}⚠️  ${name} not found, skipping${NC}"
    fi
}

# Stop all services
stop_service "." "Main Platform"
stop_service "appsumo-products/wallet-guardian" "Wallet Guardian"
stop_service "appsumo-products/transaction-inspector" "Transaction Inspector"
stop_service "appsumo-products/analytics-pro" "Analytics Pro"
stop_service "appsumo-chatbot-pro" "ChatBot Pro"

echo ""
echo -e "${GREEN}🎉 All services stopped successfully!${NC}"
echo ""
echo -e "${YELLOW}To restart:${NC}"
echo "  ./scripts/deploy-all.sh"
