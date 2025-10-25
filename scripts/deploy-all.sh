#!/bin/bash

# 🚀 ONE-COMMAND DEPLOYMENT SCRIPT
# Deploys all systems: Main Platform + 4 AppSumo Products
# Version: 1.0.0
# Author: BlockSigmaKode Team

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Banner
echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════════════════╗"
echo "║   🚀 BLOCKSIGMAKODE DEPLOYMENT SCRIPT               ║"
echo "║   Deploy Main Platform + 4 AppSumo Products         ║"
echo "╚═══════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check if running from project root
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}❌ Error: Must run from project root directory${NC}"
    exit 1
fi

# Function to check if Docker is running
check_docker() {
    echo -e "${YELLOW}🔍 Checking Docker...${NC}"
    if ! docker info > /dev/null 2>&1; then
        echo -e "${RED}❌ Docker is not running. Please start Docker Desktop.${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ Docker is running${NC}"
}

# Function to check if docker-compose exists
check_docker_compose() {
    echo -e "${YELLOW}🔍 Checking docker-compose...${NC}"
    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}❌ docker-compose not found. Please install it.${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ docker-compose found${NC}"
}

# Function to check .env file
check_env() {
    local dir=$1
    local name=$2
    echo -e "${YELLOW}🔍 Checking .env for ${name}...${NC}"
    
    if [ ! -f "${dir}/.env" ]; then
        echo -e "${YELLOW}⚠️  .env not found in ${dir}${NC}"
        if [ -f "${dir}/.env.example" ]; then
            echo -e "${YELLOW}📝 Copying .env.example to .env${NC}"
            cp "${dir}/.env.example" "${dir}/.env"
            echo -e "${RED}⚠️  IMPORTANT: Please edit ${dir}/.env with your credentials!${NC}"
            read -p "Press Enter to continue or Ctrl+C to abort..."
        else
            echo -e "${RED}❌ No .env.example found. Cannot continue.${NC}"
            return 1
        fi
    else
        echo -e "${GREEN}✅ .env exists${NC}"
    fi
}

# Function to deploy a service
deploy_service() {
    local dir=$1
    local name=$2
    local port=$3
    
    echo ""
    echo -e "${BLUE}╔═══════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║  Deploying: ${name}${NC}"
    echo -e "${BLUE}╚═══════════════════════════════════════╝${NC}"
    
    cd "$dir"
    
    # Check .env
    check_env "." "$name" || return 1
    
    # Pull latest images
    echo -e "${YELLOW}📥 Pulling images for ${name}...${NC}"
    docker-compose pull || true
    
    # Build images
    echo -e "${YELLOW}🔨 Building images for ${name}...${NC}"
    docker-compose build --no-cache
    
    # Start services
    echo -e "${YELLOW}🚀 Starting ${name}...${NC}"
    docker-compose up -d
    
    # Wait for health check
    echo -e "${YELLOW}⏳ Waiting for ${name} to be healthy...${NC}"
    sleep 10
    
    # Check if services are running
    if docker-compose ps | grep -q "Up"; then
        echo -e "${GREEN}✅ ${name} deployed successfully!${NC}"
        if [ ! -z "$port" ]; then
            echo -e "${GREEN}   Access at: http://localhost:${port}${NC}"
        fi
    else
        echo -e "${RED}❌ ${name} failed to start${NC}"
        docker-compose logs --tail=20
        return 1
    fi
    
    cd - > /dev/null
}

# Main deployment flow
main() {
    echo -e "${YELLOW}Starting deployment...${NC}"
    echo ""
    
    # Pre-flight checks
    check_docker
    check_docker_compose
    
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════${NC}"
    echo -e "${BLUE}  DEPLOYMENT PLAN${NC}"
    echo -e "${BLUE}═══════════════════════════════════════${NC}"
    echo "1. Main Platform (Port: 3000, 8000)"
    echo "2. Wallet Guardian (Port: 3001, 8001)"
    echo "3. Transaction Inspector (Port: 3002, 8002)"
    echo "4. Analytics Pro (Port: 3003, 8003)"
    echo "5. ChatBot Pro (Port: 3000)"
    echo -e "${BLUE}═══════════════════════════════════════${NC}"
    echo ""
    
    read -p "Deploy all services? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Deployment cancelled${NC}"
        exit 0
    fi
    
    # Track deployment status
    SUCCESS=0
    FAILED=0
    
    # Deploy Main Platform
    echo ""
    if deploy_service "." "Main Platform" "3000"; then
        ((SUCCESS++))
    else
        ((FAILED++))
        echo -e "${RED}⚠️  Main Platform deployment failed, continuing...${NC}"
    fi
    
    # Deploy Wallet Guardian
    if [ -d "appsumo-products/wallet-guardian" ]; then
        if deploy_service "appsumo-products/wallet-guardian" "Wallet Guardian" "3001"; then
            ((SUCCESS++))
        else
            ((FAILED++))
            echo -e "${RED}⚠️  Wallet Guardian deployment failed, continuing...${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  Wallet Guardian directory not found, skipping${NC}"
    fi
    
    # Deploy Transaction Inspector
    if [ -d "appsumo-products/transaction-inspector" ]; then
        if deploy_service "appsumo-products/transaction-inspector" "Transaction Inspector" "3002"; then
            ((SUCCESS++))
        else
            ((FAILED++))
            echo -e "${RED}⚠️  Transaction Inspector deployment failed, continuing...${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  Transaction Inspector directory not found, skipping${NC}"
    fi
    
    # Deploy Analytics Pro
    if [ -d "appsumo-products/analytics-pro" ]; then
        if deploy_service "appsumo-products/analytics-pro" "Analytics Pro" "3003"; then
            ((SUCCESS++))
        else
            ((FAILED++))
            echo -e "${RED}⚠️  Analytics Pro deployment failed, continuing...${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  Analytics Pro directory not found, skipping${NC}"
    fi
    
    # Deploy ChatBot Pro
    if [ -d "appsumo-chatbot-pro" ]; then
        if deploy_service "appsumo-chatbot-pro" "ChatBot Pro" "3000"; then
            ((SUCCESS++))
        else
            ((FAILED++))
            echo -e "${RED}⚠️  ChatBot Pro deployment failed, continuing...${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  ChatBot Pro directory not found, skipping${NC}"
    fi
    
    # Summary
    echo ""
    echo -e "${BLUE}╔═══════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║  DEPLOYMENT SUMMARY                   ║${NC}"
    echo -e "${BLUE}╚═══════════════════════════════════════╝${NC}"
    echo -e "${GREEN}✅ Successful: ${SUCCESS}${NC}"
    echo -e "${RED}❌ Failed: ${FAILED}${NC}"
    echo ""
    
    if [ $FAILED -eq 0 ]; then
        echo -e "${GREEN}🎉 ALL SERVICES DEPLOYED SUCCESSFULLY!${NC}"
        echo ""
        echo -e "${BLUE}Access your services:${NC}"
        echo "  Main Platform:        http://localhost:3000"
        echo "  Wallet Guardian:      http://localhost:3001"
        echo "  Transaction Inspector: http://localhost:3002"
        echo "  Analytics Pro:        http://localhost:3003"
        echo "  ChatBot Pro:          http://localhost:3000"
        echo ""
        echo -e "${YELLOW}📊 View logs:${NC}"
        echo "  docker-compose logs -f"
        echo ""
        echo -e "${YELLOW}🛑 Stop all services:${NC}"
        echo "  ./scripts/stop-all.sh"
    else
        echo -e "${RED}⚠️  Some services failed to deploy${NC}"
        echo -e "${YELLOW}Check logs for details:${NC}"
        echo "  docker-compose logs [service-name]"
    fi
}

# Run main function
main

echo ""
echo -e "${GREEN}Deployment script completed!${NC}"
