#!/bin/bash
# Master Test Runner für Blockchain Forensics Platform
# Führt alle Tests systematisch aus: Backend, Frontend, Security

# Keine globale Abbruchlogik; Fehler werden gesammelt und am Ende ausgewertet

# Farben für Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fortschritts-Tracking
TOTAL_SECTIONS=10   # Basis: 8 Backend + 2 Frontend Abschnitte

# Optional hinzukommende Abschnitte vorab berücksichtigen
if [ -d "backend/tests/e2e" ] && [ "$(ls -A backend/tests/e2e 2>/dev/null)" ]; then
    if [ "${ENABLE_BACKEND_E2E}" = "1" ]; then
        TOTAL_SECTIONS=$((TOTAL_SECTIONS + 1))
    fi
fi

if [ "$RUN_SECURITY_SCANS" = "true" ]; then
    TOTAL_SECTIONS=$((TOTAL_SECTIONS + 2))
fi

COMPLETED_SECTIONS=0

show_progress() {
    local section_name=$1

    if [ "$TOTAL_SECTIONS" -le 0 ]; then
        return
    fi

    COMPLETED_SECTIONS=$((COMPLETED_SECTIONS + 1))
    local percent=$((COMPLETED_SECTIONS * 100 / TOTAL_SECTIONS))

    echo -e "${BLUE}🔄 Fortschritt: ${COMPLETED_SECTIONS}/${TOTAL_SECTIONS} (${percent}%) – ${section_name}${NC}"
    echo ""
}

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Blockchain Forensics Platform - Master Test Suite            ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Konfiguration
BACKEND_DIR="backend"
FRONTEND_DIR="frontend"
COVERAGE_MIN=80
FAILED_TESTS=0

# Funktion für Test-Abschnitte
run_test_section() {
    local section_name=$1
    local command=$2
    local result=0

    echo -e "${YELLOW}┌─────────────────────────────────────────────────────────────┐${NC}"
    echo -e "${YELLOW}│ ${section_name}${NC}"
    echo -e "${YELLOW}└─────────────────────────────────────────────────────────────┘${NC}"
    echo ""
    # Führe den Befehl aus und werte Exit-Codes aus
    # set -e würde hier sonst sofort abbrechen; daher temporär deaktivieren
    set +e
    bash -c "$command"
    local ec=$?
    set -e
    if [ $ec -eq 0 ]; then
        echo -e "${GREEN}✓ ${section_name} erfolgreich${NC}"
        echo ""
        result=0
    elif [ $ec -eq 5 ]; then
        # Pytest Exit-Code 5: Keine Tests gesammelt -> als übersprungen werten
        echo -e "${YELLOW}↷ ${section_name} übersprungen (keine Tests gefunden)${NC}"
        echo ""
        result=0
    else
        echo -e "${RED}✗ ${section_name} fehlgeschlagen (Exit-Code $ec)${NC}"
        echo ""
        FAILED_TESTS=$((FAILED_TESTS + 1))
        result=1
    fi

    show_progress "$section_name"
    return $result
}

# ============================================================================
# BACKEND TESTS
# ============================================================================

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  BACKEND TESTS${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

cd "$BACKEND_DIR"

# 1. Unit Tests (schnell)
run_test_section "Backend Unit Tests" \
    "pytest tests/unit -v -m unit --tb=short"

# 2. Integration Tests (mit DB)
run_test_section "Backend Integration Tests - API" \
    "pytest tests/integration/api -v -m integration --tb=short"

run_test_section "Backend Integration Tests - Adapters" \
    "pytest tests/integration/adapters -v -m 'integration and adapter' --tb=short"

run_test_section "Backend Integration Tests - Workers" \
    "pytest tests/integration/workers -v -m integration --tb=short"

# 3. Security Tests
run_test_section "Backend Security Tests" \
    "pytest tests/security -v -m security --tb=short"

# 4. E2E Tests (optional via ENABLE_BACKEND_E2E=1)
if [ -d "tests/e2e" ] && [ "$(ls -A tests/e2e)" ]; then
  if [ "${ENABLE_BACKEND_E2E}" = "1" ]; then
    run_test_section "Backend E2E Tests" \
        "pytest tests/e2e -v -m e2e --tb=short"
  else
    echo -e "${YELLOW}↷ Backend E2E Tests übersprungen (ENABLE_BACKEND_E2E!=1)${NC}"
    echo ""
  fi
fi

# 5. Spezialisierte Tests
run_test_section "Backend Bridge Detection Tests" \
    "pytest tests -v -m bridge --tb=short"

run_test_section "Backend Clustering Tests" \
    "pytest tests -v -m clustering --tb=short"

# 6. Coverage Report
run_test_section "Backend Coverage Report" \
    "pytest tests -v --cov=app --cov-report=html --cov-report=term-missing --cov-fail-under=$COVERAGE_MIN"
if [ -f "htmlcov/index.html" ]; then
  echo -e "${GREEN}✓ Coverage Report: backend/htmlcov/index.html${NC}"
  echo ""
fi

cd ..

# ============================================================================
# FRONTEND TESTS
# ============================================================================

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  FRONTEND TESTS${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

cd "$FRONTEND_DIR"

# 1. Vitest Unit/Integration Tests
run_test_section "Frontend Unit & Integration Tests" \
    "npm run test"

# 2. Playwright E2E Tests
echo -e "${YELLOW}Starte Build für E2E Tests...${NC}"
npm run build
echo ""

run_test_section "Frontend E2E Tests (Playwright)" \
    "npm run test:e2e"

cd ..

# ============================================================================
# SECURITY SCANS (Optional)
# ============================================================================

if [ "$RUN_SECURITY_SCANS" = "true" ]; then
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  SECURITY SCANS${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    cd "$BACKEND_DIR"
    
    run_test_section "Bandit Security Scan" \
        "bandit -r app/ -f txt || true"
    
    run_test_section "Safety Dependency Check" \
        "safety check || true"
    
    cd ..
fi

# ============================================================================
# ZUSAMMENFASSUNG
# ============================================================================

echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  TEST ZUSAMMENFASSUNG                                          ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}✓ Alle Tests erfolgreich!${NC}"
    echo ""
    echo -e "${GREEN}Coverage Reports:${NC}"
    echo -e "  Backend:  ${BACKEND_DIR}/htmlcov/index.html"
    echo -e "  Frontend: ${FRONTEND_DIR}/test-results/playwright-report/index.html"
    echo ""
    exit 0
else
    echo -e "${RED}✗ ${FAILED_TESTS} Test-Abschnitt(e) fehlgeschlagen${NC}"
    echo ""
    echo -e "${YELLOW}Bitte überprüfe die Fehlerausgaben oben.${NC}"
    echo ""
    exit 1
fi
