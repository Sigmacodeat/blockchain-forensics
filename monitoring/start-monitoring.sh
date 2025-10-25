#!/bin/bash
#
# Quick Start Script für Monitoring Stack
# Startet Prometheus + Grafana und verifiziert Health
#

set -e

echo "🚀 Starting Blockchain Forensics Monitoring Stack..."
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check Prerequisites
echo "📋 Checking prerequisites..."

if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker not found. Please install Docker first.${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ docker-compose not found. Please install docker-compose first.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker found${NC}"

# Check if backend is running
echo ""
echo "🔍 Checking if backend is running..."
if curl -s http://localhost:8000/health > /dev/null; then
    echo -e "${GREEN}✅ Backend is running${NC}"
else
    echo -e "${YELLOW}⚠️  Backend not running. Starting it first...${NC}"
    cd ..
    docker-compose up -d backend
    echo "⏳ Waiting for backend to be healthy (40s)..."
    sleep 40
    cd monitoring
fi

# Start Monitoring Stack
echo ""
echo "🚀 Starting Prometheus + Grafana..."
cd ..
docker-compose up -d --no-deps prometheus grafana
cd monitoring

echo ""
echo "⏳ Waiting for services to start..."
sleep 10

# Health Checks
echo ""
echo "🏥 Running health checks..."

# Check Prometheus
echo -n "  Prometheus: "
if curl -s http://localhost:9090/-/healthy > /dev/null; then
    echo -e "${GREEN}✅ Healthy${NC}"
else
    echo -e "${RED}❌ Not responding${NC}"
fi

# Check Grafana
echo -n "  Grafana:    "
if curl -s http://localhost:3001/api/health > /dev/null; then
    echo -e "${GREEN}✅ Healthy${NC}"
else
    echo -e "${RED}❌ Not responding${NC}"
fi

# Check Backend Metrics
echo -n "  Metrics:    "
if curl -s http://localhost:8000/metrics | head -1 > /dev/null; then
    echo -e "${GREEN}✅ Available${NC}"
else
    echo -e "${RED}❌ Not available${NC}"
fi

# Summary
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}🎉 Monitoring Stack Started!${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📊 Access Dashboards:"
echo ""
echo "  Prometheus:  http://localhost:9090"
echo "  Grafana:     http://localhost:3001 (admin/admin)"
echo "  Metrics:     http://localhost:8000/metrics"
echo "  Health:      http://localhost:8000/api/health/detailed"
echo ""
echo "📖 Documentation:"
echo ""
echo "  Full Guide:  ./MONITORING.md"
echo "  Examples:    ./monitoring/EXAMPLES.md"
echo ""
echo "🔧 Quick Commands:"
echo ""
echo "  # View Logs"
echo "  docker-compose logs -f prometheus grafana"
echo ""
echo "  # Reload Prometheus Config"
echo "  curl -X POST http://localhost:9090/-/reload"
echo ""
echo "  # Check Alerts"
echo "  curl http://localhost:9090/api/v1/alerts | jq"
echo ""
echo "  # Import Dashboard"
echo "  # → Open Grafana → Dashboards → Import → Upload grafana-dashboard.json"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "✨ Happy Monitoring!"
echo ""
