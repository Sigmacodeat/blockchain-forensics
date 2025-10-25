#!/bin/bash

# 🏥 HEALTH CHECK SCRIPT
# Checks all services and reports status
# Version: 1.0.0

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Function to check HTTP endpoint
check_endpoint() {
    local url=$1
    local name=$2
    local timeout=5
    
    echo -n "  Checking ${name}... "
    
    if curl -s -f -m $timeout "${url}" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ OK${NC}"
        return 0
    else
        echo -e "${RED}❌ FAILED${NC}"
        return 1
    fi
}

# Function to check Docker container
check_container() {
    local container=$1
    local name=$2
    
    echo -n "  Checking ${name}... "
    
    if docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
        local status=$(docker inspect -f '{{.State.Status}}' "${container}")
        if [ "$status" = "running" ]; then
            echo -e "${GREEN}✅ Running${NC}"
            return 0
        else
            echo -e "${RED}❌ ${status}${NC}"
            return 1
        fi
    else
        echo -e "${RED}❌ Not found${NC}"
        return 1
    fi
}

# Function to check database
check_database() {
    local container=$1
    local name=$2
    
    echo -n "  Checking ${name}... "
    
    if docker exec "${container}" pg_isready > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Responding${NC}"
        return 0
    else
        echo -e "${RED}❌ Not responding${NC}"
        return 1
    fi
}

# Banner
echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════════════════╗"
echo "║   🏥 SYSTEM HEALTH CHECK                             ║"
echo "╚═══════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Track results
TOTAL=0
SUCCESS=0
FAILED=0

# Main Platform
echo -e "${BLUE}━━━ Main Platform ━━━${NC}"

((TOTAL++))
if check_endpoint "http://localhost:8000/health" "Backend API"; then ((SUCCESS++)); else ((FAILED++)); fi

((TOTAL++))
if check_endpoint "http://localhost:3000" "Frontend"; then ((SUCCESS++)); else ((FAILED++)); fi

((TOTAL++))
if check_container "forensics_backend" "Backend Container"; then ((SUCCESS++)); else ((FAILED++)); fi

((TOTAL++))
if check_database "forensics_db" "PostgreSQL"; then ((SUCCESS++)); else ((FAILED++)); fi

((TOTAL++))
if check_container "forensics_redis" "Redis"; then ((SUCCESS++)); else ((FAILED++)); fi

((TOTAL++))
if check_container "forensics_neo4j" "Neo4j"; then ((SUCCESS++)); else ((FAILED++)); fi

# Wallet Guardian
echo ""
echo -e "${BLUE}━━━ Wallet Guardian ━━━${NC}"

((TOTAL++))
if check_endpoint "http://localhost:8001/health" "API"; then ((SUCCESS++)); else ((FAILED++)); fi

((TOTAL++))
if check_endpoint "http://localhost:3001" "Frontend"; then ((SUCCESS++)); else ((FAILED++)); fi

# Transaction Inspector
echo ""
echo -e "${BLUE}━━━ Transaction Inspector ━━━${NC}"

((TOTAL++))
if check_endpoint "http://localhost:8002/health" "API"; then ((SUCCESS++)); else ((FAILED++)); fi

((TOTAL++))
if check_endpoint "http://localhost:3002" "Frontend"; then ((SUCCESS++)); else ((FAILED++)); fi

# Analytics Pro
echo ""
echo -e "${BLUE}━━━ Analytics Pro ━━━${NC}"

((TOTAL++))
if check_endpoint "http://localhost:8003/health" "API"; then ((SUCCESS++)); else ((FAILED++)); fi

((TOTAL++))
if check_endpoint "http://localhost:3003" "Frontend"; then ((SUCCESS++)); else ((FAILED++)); fi

((TOTAL++))
if check_endpoint "http://localhost:3001" "Grafana"; then ((SUCCESS++)); else ((FAILED++)); fi

# Summary
echo ""
echo -e "${BLUE}╔═══════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  HEALTH CHECK SUMMARY                 ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════╝${NC}"
echo -e "Total Checks: ${TOTAL}"
echo -e "${GREEN}Passed: ${SUCCESS}${NC}"
echo -e "${RED}Failed: ${FAILED}${NC}"

# Calculate percentage
PERCENTAGE=$((SUCCESS * 100 / TOTAL))
echo ""
echo -e "Overall Health: ${PERCENTAGE}%"

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 ALL SYSTEMS OPERATIONAL!${NC}"
    exit 0
elif [ $PERCENTAGE -ge 80 ]; then
    echo -e "${YELLOW}⚠️  DEGRADED (Some services down)${NC}"
    exit 1
else
    echo -e "${RED}❌ CRITICAL (Multiple services down)${NC}"
    exit 2
fi
