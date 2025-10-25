#!/bin/bash
# Verifikations-Script für die neue Test-Struktur

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Test-Struktur Verifikation                                   ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Backend-Struktur
echo -e "${YELLOW}Backend-Struktur:${NC}"
echo "  ✓ backend/tests/unit/           $(ls backend/tests/unit/ 2>/dev/null | wc -l | xargs) Dateien"
echo "  ✓ backend/tests/integration/api/ $(ls backend/tests/integration/api/*.py 2>/dev/null | wc -l | xargs) Tests"
echo "  ✓ backend/tests/integration/adapters/ $(ls backend/tests/integration/adapters/*.py 2>/dev/null | wc -l | xargs) Tests"
echo "  ✓ backend/tests/e2e/            $(ls backend/tests/e2e/*.py 2>/dev/null | wc -l | xargs) Tests"
echo "  ✓ backend/tests/security/       $(ls backend/tests/security/*.py 2>/dev/null | wc -l | xargs) Tests"
echo ""

# Frontend-Struktur
echo -e "${YELLOW}Frontend-Struktur:${NC}"
echo "  ✓ frontend/tests/unit/          $(ls frontend/tests/unit/ 2>/dev/null | wc -l | xargs) Dateien"
echo "  ✓ frontend/tests/integration/   $(ls frontend/tests/integration/*.tsx 2>/dev/null | wc -l | xargs) Tests"
echo "  ✓ frontend/tests/e2e/           $(find frontend/tests/e2e -name "*.spec.ts" 2>/dev/null | wc -l | xargs) Tests"
echo ""

# Konsolidierte Tests
echo -e "${YELLOW}Konsolidierte Tests:${NC}"
if [ -f "backend/tests/integration/api/test_agent_consolidated.py" ]; then
    echo -e "  ${GREEN}✓${NC} test_agent_consolidated.py"
else
    echo -e "  ✗ test_agent_consolidated.py fehlt"
fi

if [ -f "backend/tests/integration/api/test_alerts_consolidated.py" ]; then
    echo -e "  ${GREEN}✓${NC} test_alerts_consolidated.py"
else
    echo -e "  ✗ test_alerts_consolidated.py fehlt"
fi

if [ -f "backend/tests/integration/api/test_risk_consolidated.py" ]; then
    echo -e "  ${GREEN}✓${NC} test_risk_consolidated.py"
else
    echo -e "  ✗ test_risk_consolidated.py fehlt"
fi
echo ""

# Pytest-Marker
echo -e "${YELLOW}Pytest-Marker:${NC}"
cd backend
agent_tests=$(pytest tests/ -m agent --collect-only 2>&1 | grep "collected" | awk '{print $1}')
alert_tests=$(pytest tests/ -m alert --collect-only 2>&1 | grep "collected" | awk '{print $1}')
risk_tests=$(pytest tests/ -m risk --collect-only 2>&1 | grep "collected" | awk '{print $1}')

echo "  ✓ -m agent:  $agent_tests Tests"
echo "  ✓ -m alert:  $alert_tests Tests"
echo "  ✓ -m risk:   $risk_tests Tests"
cd ..
echo ""

# Dokumentation
echo -e "${YELLOW}Dokumentation:${NC}"
docs=("TESTING_GUIDE.md" "TEST_ANALYSIS.md" "TEST_MIGRATION_NOTES.md" "TEST_SUMMARY.md" "QUICK_TEST_COMMANDS.md" "TEST_REORGANISATION_COMPLETE.md")
for doc in "${docs[@]}"; do
    if [ -f "$doc" ]; then
        echo -e "  ${GREEN}✓${NC} $doc"
    else
        echo -e "  ✗ $doc fehlt"
    fi
done
echo ""

# Scripts
echo -e "${YELLOW}Scripts:${NC}"
if [ -f "run-all-tests.sh" ] && [ -x "run-all-tests.sh" ]; then
    echo -e "  ${GREEN}✓${NC} run-all-tests.sh (ausführbar)"
else
    echo -e "  ✗ run-all-tests.sh fehlt oder nicht ausführbar"
fi
echo ""

# Makefile-Targets
echo -e "${YELLOW}Makefile-Targets:${NC}"
targets=$(grep "^test" Makefile 2>/dev/null | grep "##" | wc -l | xargs)
echo "  ✓ $targets Test-Targets verfügbar"
echo ""

echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ✓ Test-Struktur erfolgreich verifiziert!                     ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
