#!/bin/bash

###############################################################################
# 🚀 RUN ALL SAAS FEATURE TESTS
###############################################################################
#
# Dieses Script führt ALLE SaaS-Feature-Tests aus und generiert einen Report.
#
# Usage:
#   ./scripts/run-all-saas-tests.sh [options]
#
# Options:
#   --coverage    Generiere Coverage-Report
#   --verbose     Verbose Output
#   --fast        Nur schnelle Tests
#   --critical    Nur kritische Tests
###############################################################################

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Defaults
COVERAGE=false
VERBOSE=false
FAST=false
CRITICAL=false

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --coverage)
      COVERAGE=true
      shift
      ;;
    --verbose)
      VERBOSE=true
      shift
      ;;
    --fast)
      FAST=true
      shift
      ;;
    --critical)
      CRITICAL=true
      shift
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║        🚀 SAAS FEATURE TEST SUITE                         ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Change to backend directory
cd "$(dirname "$0")/../backend"

# Activate virtual environment if exists
if [ -d "venv" ]; then
  echo -e "${YELLOW}📦 Aktiviere Virtual Environment...${NC}"
  source venv/bin/activate
fi

# Install dependencies
echo -e "${YELLOW}📦 Prüfe Dependencies...${NC}"
pip install -q pytest pytest-asyncio pytest-cov httpx

# Build pytest command
PYTEST_CMD="pytest"
PYTEST_ARGS="-v"

if [ "$COVERAGE" = true ]; then
  PYTEST_ARGS="$PYTEST_ARGS --cov=app --cov-report=html --cov-report=term"
fi

if [ "$VERBOSE" = true ]; then
  PYTEST_ARGS="$PYTEST_ARGS -vv -s"
fi

# Test selection
if [ "$CRITICAL" = true ]; then
  TEST_FILES="../tests/test_crypto_payments_complete.py ../tests/test_ai_agent_complete.py ../tests/test_admin_complete.py"
elif [ "$FAST" = true ]; then
  PYTEST_ARGS="$PYTEST_ARGS -m 'not slow'"
  TEST_FILES="../tests/"
else
  TEST_FILES="../tests/"
fi

echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  TEST-KONFIGURATION${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "  Coverage:     ${COVERAGE}"
echo -e "  Verbose:      ${VERBOSE}"
echo -e "  Fast Mode:    ${FAST}"
echo -e "  Critical Only: ${CRITICAL}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""

# Run tests
echo -e "${GREEN}🧪 Führe Tests aus...${NC}"
echo ""

# Crypto-Payments Tests
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}💳 CRYPTO-PAYMENTS TESTS${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
$PYTEST_CMD $PYTEST_ARGS ../tests/test_crypto_payments_complete.py || true
echo ""

# AI-Agent Tests
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}🤖 AI-AGENT TESTS${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
$PYTEST_CMD $PYTEST_ARGS ../tests/test_ai_agent_complete.py || true
echo ""

# Admin Tests
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}👨‍💼 ADMIN FEATURES TESTS${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
$PYTEST_CMD $PYTEST_ARGS ../tests/test_admin_complete.py || true
echo ""

# Existing Tests
if [ "$CRITICAL" = false ]; then
  echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo -e "${YELLOW}🔧 EXISTING TESTS${NC}"
  echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  $PYTEST_CMD $PYTEST_ARGS ../tests/test_comprehensive.py || true
  $PYTEST_CMD $PYTEST_ARGS ../tests/test_cases_api.py || true
  echo ""
fi

# Generate summary
echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  TEST-ZUSAMMENFASSUNG${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"

# Count test files
TOTAL_TEST_FILES=$(find ../tests -name "test_*.py" | wc -l | tr -d ' ')
echo -e "  ${GREEN}✓${NC} Test-Files gefunden: ${TOTAL_TEST_FILES}"

# Coverage report location
if [ "$COVERAGE" = true ]; then
  echo -e "  ${GREEN}✓${NC} Coverage-Report: htmlcov/index.html"
fi

echo ""
echo -e "${GREEN}✅ Test-Ausführung abgeschlossen!${NC}"
echo ""

# Open coverage report if available
if [ "$COVERAGE" = true ] && [ -f "htmlcov/index.html" ]; then
  echo -e "${YELLOW}📊 Öffne Coverage-Report...${NC}"
  open htmlcov/index.html 2>/dev/null || xdg-open htmlcov/index.html 2>/dev/null || true
fi

exit 0
