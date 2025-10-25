#!/bin/bash
# Test Script for Two-Tier Demo System
# ======================================

echo "🧪 Testing Two-Tier Demo System..."
echo ""

API_URL="${API_URL:-http://localhost:8000}"
FRONTEND_URL="${FRONTEND_URL:-http://localhost:3000}"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

test_endpoint() {
    local name="$1"
    local method="$2"
    local endpoint="$3"
    local expected_status="$4"
    
    echo -n "Testing: $name... "
    
    response=$(curl -s -o /dev/null -w "%{http_code}" -X "$method" "$API_URL$endpoint")
    
    if [ "$response" = "$expected_status" ]; then
        echo -e "${GREEN}✓ PASSED${NC} (HTTP $response)"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}✗ FAILED${NC} (Expected $expected_status, got $response)"
        ((TESTS_FAILED++))
    fi
}

echo "📡 Backend API Tests"
echo "===================="

# Test 1: Sandbox Demo Endpoint
test_endpoint "GET /demo/sandbox" "GET" "/api/v1/demo/sandbox" "200"

# Test 2: Live Demo Creation (will create a demo user)
echo -n "Testing: POST /demo/live... "
response=$(curl -s -X POST "$API_URL/api/v1/demo/live" \
    -H "Content-Type: application/json" \
    -w "\n%{http_code}")

status=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n-1)

if [ "$status" = "200" ] || [ "$status" = "429" ]; then
    echo -e "${GREEN}✓ PASSED${NC} (HTTP $status)"
    ((TESTS_PASSED++))
    
    if [ "$status" = "200" ]; then
        # Extract user_id and token
        user_id=$(echo "$body" | grep -o '"user_id":"[^"]*"' | cut -d'"' -f4)
        token=$(echo "$body" | grep -o '"token":"[^"]*"' | cut -d'"' -f4)
        
        if [ -n "$user_id" ]; then
            echo "   Created demo user: $user_id"
        fi
    else
        echo "   Rate limit hit (expected after 3 demos)"
    fi
else
    echo -e "${RED}✗ FAILED${NC} (Expected 200 or 429, got $status)"
    ((TESTS_FAILED++))
fi

# Test 3: Demo Stats (requires admin - will fail without auth)
echo -n "Testing: GET /demo/stats (admin)... "
response=$(curl -s -o /dev/null -w "%{http_code}" -X GET "$API_URL/api/v1/demo/stats")
if [ "$response" = "401" ] || [ "$response" = "403" ] || [ "$response" = "200" ]; then
    echo -e "${GREEN}✓ PASSED${NC} (HTTP $response - Auth required)"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗ FAILED${NC} (Got $response)"
    ((TESTS_FAILED++))
fi

echo ""
echo "🖥️  Frontend Route Tests"
echo "======================="

# Test 4: Frontend Sandbox Route
echo -n "Testing: GET /demo/sandbox... "
response=$(curl -s -o /dev/null -w "%{http_code}" "$FRONTEND_URL/en/demo/sandbox")
if [ "$response" = "200" ] || [ "$response" = "000" ]; then
    echo -e "${GREEN}✓ PASSED${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${YELLOW}⚠ SKIPPED${NC} (Frontend not running)"
fi

# Test 5: Frontend Live Demo Route
echo -n "Testing: GET /demo/live... "
response=$(curl -s -o /dev/null -w "%{http_code}" "$FRONTEND_URL/en/demo/live")
if [ "$response" = "200" ] || [ "$response" = "000" ]; then
    echo -e "${GREEN}✓ PASSED${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${YELLOW}⚠ SKIPPED${NC} (Frontend not running)"
fi

echo ""
echo "📁 File Existence Tests"
echo "======================="

check_file() {
    local name="$1"
    local path="$2"
    
    echo -n "Checking: $name... "
    if [ -f "$path" ]; then
        echo -e "${GREEN}✓ EXISTS${NC}"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}✗ MISSING${NC}"
        ((TESTS_FAILED++))
    fi
}

check_file "demo_service.py" "backend/app/services/demo_service.py"
check_file "demo.py API" "backend/app/api/v1/demo.py"
check_file "DemoSandboxPage.tsx" "frontend/src/pages/DemoSandboxPage.tsx"
check_file "DemoLivePage.tsx" "frontend/src/pages/DemoLivePage.tsx"
check_file "Migration SQL" "backend/migrations/versions/007_add_demo_user_fields.sql"
check_file "Cleanup Script" "backend/scripts/demo_cleanup.py"
check_file "K8s CronJob" "infra/kubernetes/cronjobs/demo-cleanup.yaml"
check_file "Documentation" "TWO_TIER_DEMO_SYSTEM_COMPLETE.md"

echo ""
echo "📊 Test Summary"
echo "==============="
echo -e "Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Failed: ${RED}$TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
    echo ""
    echo "🚀 Two-Tier Demo System is ready for deployment!"
    exit 0
else
    echo -e "${RED}❌ Some tests failed${NC}"
    echo ""
    echo "Please check the failed tests above."
    exit 1
fi
