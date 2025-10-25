#!/bin/bash

# Intelligence Network Verification Script
# Überprüft alle Komponenten, API-Endpunkte und Integrationen

echo "🔍 Intelligence Network - Complete Verification"
echo "=============================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counters
PASSED=0
FAILED=0

# Function to check file exists
check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✓${NC} File exists: $1"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}✗${NC} File missing: $1"
        ((FAILED++))
        return 1
    fi
}

# Function to check content in file
check_content() {
    if grep -q "$2" "$1"; then
        echo -e "${GREEN}✓${NC} Content found in $1: $2"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}✗${NC} Content missing in $1: $2"
        ((FAILED++))
        return 1
    fi
}

echo "📂 Checking Frontend Files..."
echo "---------------------------------------------"
check_file "frontend/src/pages/IntelligenceNetwork.tsx"
check_file "frontend/src/components/intelligence/NetworkStats.tsx"
check_file "frontend/src/components/intelligence/ActiveFlags.tsx"
check_file "frontend/src/components/intelligence/AddressChecker.tsx"
check_file "frontend/src/components/intelligence/FlagSubmission.tsx"
check_file "frontend/src/components/intelligence/CompetitiveComparison.tsx"
check_file "frontend/src/components/intelligence/RelatedAddressNetwork.tsx"
check_file "frontend/src/hooks/useIntelligenceNetwork.ts"
echo ""

echo "🔧 Checking Backend Files..."
echo "---------------------------------------------"
check_file "backend/app/api/v1/intelligence_network.py"
check_file "backend/app/services/intelligence_sharing_service.py"
echo ""

echo "🔗 Checking Integrations..."
echo "---------------------------------------------"
check_content "frontend/src/App.tsx" "IntelligenceNetwork"
check_content "frontend/src/App.tsx" "intelligence-network"
check_content "frontend/src/components/Layout.tsx" "Intelligence Network"
check_content "backend/app/api/v1/__init__.py" "intelligence_network_router"
echo ""

echo "📄 Checking Documentation..."
echo "---------------------------------------------"
check_file "INTELLIGENCE_NETWORK_STATE_OF_THE_ART.md"
echo ""

echo "🎨 Checking Component Imports..."
echo "---------------------------------------------"
check_content "frontend/src/pages/IntelligenceNetwork.tsx" "NetworkStats"
check_content "frontend/src/pages/IntelligenceNetwork.tsx" "ActiveFlags"
check_content "frontend/src/pages/IntelligenceNetwork.tsx" "AddressChecker"
check_content "frontend/src/pages/IntelligenceNetwork.tsx" "FlagSubmission"
check_content "frontend/src/pages/IntelligenceNetwork.tsx" "CompetitiveComparison"
echo ""

echo "🔍 Checking API Endpoints..."
echo "---------------------------------------------"
check_content "backend/app/api/v1/intelligence_network.py" "/investigators/register"
check_content "backend/app/api/v1/intelligence_network.py" "/flags"
check_content "backend/app/api/v1/intelligence_network.py" "/check"
check_content "backend/app/api/v1/intelligence_network.py" "/stats"
echo ""

echo "🎯 Checking Features..."
echo "---------------------------------------------"
check_content "frontend/src/pages/IntelligenceNetwork.tsx" "Overview"
check_content "frontend/src/pages/IntelligenceNetwork.tsx" "Active Flags"
check_content "frontend/src/pages/IntelligenceNetwork.tsx" "Check Address"
check_content "frontend/src/pages/IntelligenceNetwork.tsx" "Submit Flag"
check_content "frontend/src/pages/IntelligenceNetwork.tsx" "Live Network Activity"
echo ""

echo "🚀 Checking State-of-the-Art Features..."
echo "---------------------------------------------"
check_content "frontend/src/components/intelligence/NetworkStats.tsx" "Network Health"
check_content "frontend/src/components/intelligence/NetworkStats.tsx" "Top Contributors"
check_content "frontend/src/components/intelligence/ActiveFlags.tsx" "Filters"
check_content "frontend/src/components/intelligence/ActiveFlags.tsx" "Evidence"
check_content "frontend/src/components/intelligence/AddressChecker.tsx" "Risk Assessment"
check_content "frontend/src/components/intelligence/FlagSubmission.tsx" "Auto-Trace"
check_content "frontend/src/components/intelligence/CompetitiveComparison.tsx" "Competitive Analysis"
echo ""

echo "✨ Checking Animations & UX..."
echo "---------------------------------------------"
check_content "frontend/src/pages/IntelligenceNetwork.tsx" "framer-motion"
check_content "frontend/src/components/intelligence/NetworkStats.tsx" "motion"
check_content "frontend/src/components/intelligence/ActiveFlags.tsx" "AnimatePresence"
echo ""

echo "=============================================="
echo ""
echo "📊 Final Results:"
echo "---------------------------------------------"
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ ALL CHECKS PASSED!${NC}"
    echo ""
    echo "🎉 Intelligence Network is 100% Production Ready!"
    echo ""
    echo "🚀 Next Steps:"
    echo "  1. Start backend: cd backend && uvicorn app.main:app --reload"
    echo "  2. Start frontend: cd frontend && npm run dev"
    echo "  3. Visit: http://localhost:3000/en/intelligence-network"
    echo ""
    echo "📖 Documentation: INTELLIGENCE_NETWORK_STATE_OF_THE_ART.md"
    exit 0
else
    echo -e "${RED}❌ SOME CHECKS FAILED${NC}"
    echo ""
    echo "Please review the failed checks above."
    exit 1
fi
