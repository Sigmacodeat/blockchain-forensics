#!/bin/bash
# Production Build Verification Script
# Tests all critical builds before deployment

set -e  # Exit on error

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🔍 Production Build Verification"
echo "=================================="
echo ""

# Track results
ERRORS=0
WARNINGS=0

# Function to check command exists
command_exists() {
  command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo "📋 Checking Prerequisites..."
MISSING_DEPS=()

if ! command_exists docker; then MISSING_DEPS+=("docker"); fi
if ! command_exists node; then MISSING_DEPS+=("node"); fi
if ! command_exists python3; then MISSING_DEPS+=("python3"); fi
if ! command_exists npm; then MISSING_DEPS+=("npm"); fi

if [ ${#MISSING_DEPS[@]} -ne 0 ]; then
  echo -e "${RED}✗ Missing dependencies: ${MISSING_DEPS[*]}${NC}"
  exit 1
fi

echo -e "${GREEN}✓ All prerequisites found${NC}"
echo ""

# Backend Python Syntax Check
echo "🐍 Backend: Python Syntax Check..."
cd backend
if python3 -m py_compile app/main.py 2>/dev/null; then
  echo -e "${GREEN}✓ Python syntax valid${NC}"
else
  echo -e "${RED}✗ Python syntax errors found${NC}"
  ERRORS=$((ERRORS + 1))
fi

# Backend Type Checking (optional but recommended)
echo "🔍 Backend: Type Checking..."
if command_exists mypy; then
  if mypy app/ --ignore-missing-imports --no-error-summary 2>/dev/null | grep -q "error"; then
    echo -e "${YELLOW}⚠ Type warnings found (non-blocking)${NC}"
    WARNINGS=$((WARNINGS + 1))
  else
    echo -e "${GREEN}✓ Type checks passed${NC}"
  fi
else
  echo -e "${YELLOW}⚠ mypy not installed, skipping type check${NC}"
  WARNINGS=$((WARNINGS + 1))
fi

# Backend Import Check
echo "📦 Backend: Import Verification..."
if python3 -c "from app.main import app; print('OK')" 2>/dev/null | grep -q "OK"; then
  echo -e "${GREEN}✓ All imports successful${NC}"
else
  echo -e "${RED}✗ Import errors detected${NC}"
  ERRORS=$((ERRORS + 1))
fi

cd ..

# Frontend Build
echo ""
echo "⚛️  Frontend: Production Build..."
cd frontend

# Check Node version
NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
  echo -e "${RED}✗ Node version must be 18+ (found: $NODE_VERSION)${NC}"
  ERRORS=$((ERRORS + 1))
  cd ..
  exit 1
fi

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
  echo "📦 Installing frontend dependencies..."
  npm ci --silent
fi

# TypeScript Check
echo "🔍 Frontend: TypeScript Check..."
if npx tsc --noEmit 2>&1 | grep -q "error TS"; then
  echo -e "${RED}✗ TypeScript errors found${NC}"
  ERRORS=$((ERRORS + 1))
else
  echo -e "${GREEN}✓ TypeScript checks passed${NC}"
fi

# Build Frontend
echo "🏗️  Frontend: Building..."
if npm run build > /tmp/frontend-build.log 2>&1; then
  echo -e "${GREEN}✓ Frontend build successful${NC}"
  
  # Check build size
  BUILD_SIZE=$(du -sh dist | cut -f1)
  echo "   Build size: $BUILD_SIZE"
  
  # Check if dist folder exists
  if [ ! -d "dist" ]; then
    echo -e "${RED}✗ Build output missing${NC}"
    ERRORS=$((ERRORS + 1))
  fi
else
  echo -e "${RED}✗ Frontend build failed${NC}"
  echo "   See: /tmp/frontend-build.log for details"
  ERRORS=$((ERRORS + 1))
fi

cd ..

# Docker Build Test (optional, takes time)
if [ "${SKIP_DOCKER:-0}" == "0" ]; then
  echo ""
  echo "🐳 Docker: Build Verification..."
  
  # Backend Docker Build
  echo "   Building backend image..."
  if docker build -f Dockerfile.backend -t blockchain-forensics-backend:test backend/ > /tmp/docker-backend.log 2>&1; then
    echo -e "${GREEN}✓ Backend Docker build successful${NC}"
  else
    echo -e "${RED}✗ Backend Docker build failed${NC}"
    echo "   See: /tmp/docker-backend.log"
    ERRORS=$((ERRORS + 1))
  fi
  
  # Frontend Docker Build
  echo "   Building frontend image..."
  if docker build -f Dockerfile.frontend -t blockchain-forensics-frontend:test frontend/ > /tmp/docker-frontend.log 2>&1; then
    echo -e "${GREEN}✓ Frontend Docker build successful${NC}"
  else
    echo -e "${RED}✗ Frontend Docker build failed${NC}"
    echo "   See: /tmp/docker-frontend.log"
    ERRORS=$((ERRORS + 1))
  fi
  
  # Cleanup test images
  docker rmi blockchain-forensics-backend:test blockchain-forensics-frontend:test 2>/dev/null || true
else
  echo ""
  echo -e "${YELLOW}⚠ Docker builds skipped (set SKIP_DOCKER=0 to enable)${NC}"
  WARNINGS=$((WARNINGS + 1))
fi

# Configuration Validation
echo ""
echo "⚙️  Configuration: Validation..."

# Check .env.example exists
if [ -f ".env.example" ]; then
  echo -e "${GREEN}✓ .env.example found${NC}"
else
  echo -e "${RED}✗ .env.example missing${NC}"
  ERRORS=$((ERRORS + 1))
fi

# Check docker-compose.yml syntax
if docker-compose config > /dev/null 2>&1; then
  echo -e "${GREEN}✓ docker-compose.yml valid${NC}"
else
  echo -e "${RED}✗ docker-compose.yml has syntax errors${NC}"
  ERRORS=$((ERRORS + 1))
fi

# Security Checks
echo ""
echo "🔒 Security: Basic Checks..."

# Check for hardcoded secrets
echo "   Scanning for hardcoded secrets..."
SECRETS_FOUND=0

# Check for common secret patterns
if grep -r "sk-[a-zA-Z0-9]\{48\}" backend/ frontend/ --exclude-dir={node_modules,venv,.venv,dist,build} 2>/dev/null; then
  echo -e "${RED}✗ OpenAI API keys found in code${NC}"
  SECRETS_FOUND=1
fi

if grep -r "AIza[0-9A-Za-z_-]\{35\}" backend/ frontend/ --exclude-dir={node_modules,venv,.venv,dist,build} 2>/dev/null; then
  echo -e "${RED}✗ Google API keys found in code${NC}"
  SECRETS_FOUND=1
fi

if [ $SECRETS_FOUND -eq 0 ]; then
  echo -e "${GREEN}✓ No obvious secrets in code${NC}"
else
  ERRORS=$((ERRORS + 1))
fi

# Check for console.log in production code (frontend)
echo "   Checking for console.log statements..."
CONSOLE_COUNT=$(find frontend/src -name "*.tsx" -o -name "*.ts" | xargs grep -c "console\.log" 2>/dev/null | awk -F: '{sum+=$2} END {print sum}')
if [ "${CONSOLE_COUNT:-0}" -gt 50 ]; then
  echo -e "${YELLOW}⚠ Found $CONSOLE_COUNT console.log statements (run scripts/remove-console-logs.sh)${NC}"
  WARNINGS=$((WARNINGS + 1))
else
  echo -e "${GREEN}✓ Console.log usage acceptable${NC}"
fi

# Final Summary
echo ""
echo "=================================="
echo "📊 Build Verification Summary"
echo "=================================="

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
  echo -e "${GREEN}✅ ALL CHECKS PASSED!${NC}"
  echo ""
  echo "🚀 Your SaaS is production-ready and can go online!"
  echo ""
  exit 0
elif [ $ERRORS -eq 0 ]; then
  echo -e "${YELLOW}⚠️  PASSED WITH WARNINGS${NC}"
  echo "   Errors: $ERRORS"
  echo "   Warnings: $WARNINGS"
  echo ""
  echo "✓ Build is functional but has non-critical warnings"
  echo "  Review warnings above before deploying to production"
  echo ""
  exit 0
else
  echo -e "${RED}❌ BUILD VERIFICATION FAILED${NC}"
  echo "   Errors: $ERRORS"
  echo "   Warnings: $WARNINGS"
  echo ""
  echo "Please fix the errors above before deploying"
  echo ""
  exit 1
fi
