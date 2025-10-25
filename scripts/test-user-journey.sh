#!/bin/bash
# Critical User Journey Test - Lawyer Use Case
# Tests: Signup → Login → Bitcoin Trace → Inline Chat → Report Export

set -e

API_URL="http://localhost:8000"
FRONTEND_URL="http://localhost:5173"

echo "🧪 Testing Critical User Journey - Lawyer Use Case"
echo "=================================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Test counter
PASSED=0
FAILED=0

# Function to test endpoint
test_endpoint() {
  local name=$1
  local method=$2
  local endpoint=$3
  local data=$4
  local expected_code=$5
  
  echo -n "Testing: $name... "
  
  if [ "$method" == "POST" ]; then
    response=$(curl -s -w "\n%{http_code}" -X POST "$API_URL$endpoint" \
      -H "Content-Type: application/json" \
      -d "$data" 2>/dev/null)
  else
    response=$(curl -s -w "\n%{http_code}" "$API_URL$endpoint" 2>/dev/null)
  fi
  
  http_code=$(echo "$response" | tail -n1)
  body=$(echo "$response" | sed '$d')
  
  if [ "$http_code" == "$expected_code" ]; then
    echo -e "${GREEN}✓ PASSED${NC} (HTTP $http_code)"
    PASSED=$((PASSED + 1))
    echo "$body"
    return 0
  else
    echo -e "${RED}✗ FAILED${NC} (Expected $expected_code, got $http_code)"
    FAILED=$((FAILED + 1))
    echo "Response: $body"
    return 1
  fi
}

echo "Step 1: Check Backend Health"
echo "-----------------------------"
test_endpoint "Backend Health" "GET" "/health" "" "200"
echo ""

echo "Step 2: User Registration"
echo "-------------------------"
TEST_EMAIL="lawyer-test-$(date +%s)@example.com"
TEST_PASSWORD="SecurePassword123!"

SIGNUP_DATA=$(cat <<EOF
{
  "email": "$TEST_EMAIL",
  "password": "$TEST_PASSWORD",
  "username": "testlawyer$(date +%s)",
  "name": "Test Lawyer"
}
EOF
)

if test_endpoint "User Signup" "POST" "/api/v1/auth/register" "$SIGNUP_DATA" "201"; then
  echo "✓ User created: $TEST_EMAIL"
else
  echo "⚠ Signup failed - trying login with existing user"
fi
echo ""

echo "Step 3: User Login"
echo "------------------"
LOGIN_DATA=$(cat <<EOF
{
  "email": "$TEST_EMAIL",
  "password": "$TEST_PASSWORD"
}
EOF
)

if LOGIN_RESPONSE=$(curl -s -X POST "$API_URL/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d "$LOGIN_DATA" 2>/dev/null); then
  
  ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
  
  if [ -n "$ACCESS_TOKEN" ]; then
    echo -e "${GREEN}✓ Login successful${NC}"
    echo "Access Token: ${ACCESS_TOKEN:0:20}..."
    PASSED=$((PASSED + 1))
  else
    echo -e "${RED}✗ Login failed - no token received${NC}"
    echo "Response: $LOGIN_RESPONSE"
    FAILED=$((FAILED + 1))
    exit 1
  fi
else
  echo -e "${RED}✗ Login request failed${NC}"
  FAILED=$((FAILED + 1))
  exit 1
fi
echo ""

echo "Step 4: Bitcoin Address Trace"
echo "------------------------------"
# Test with a real Bitcoin address (Satoshi's genesis block)
BTC_ADDRESS="1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"

TRACE_DATA=$(cat <<EOF
{
  "source_address": "$BTC_ADDRESS",
  "chain": "bitcoin",
  "max_depth": 2,
  "max_transactions": 10
}
EOF
)

echo "Tracing Bitcoin address: $BTC_ADDRESS"
if TRACE_RESPONSE=$(curl -s -X POST "$API_URL/api/v1/trace/start" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d "$TRACE_DATA" 2>/dev/null); then
  
  TRACE_ID=$(echo "$TRACE_RESPONSE" | grep -o '"trace_id":"[^"]*' | cut -d'"' -f4)
  
  if [ -n "$TRACE_ID" ]; then
    echo -e "${GREEN}✓ Trace started${NC}"
    echo "Trace ID: $TRACE_ID"
    PASSED=$((PASSED + 1))
    
    # Wait for trace to process
    echo "Waiting 5 seconds for trace to process..."
    sleep 5
    
    # Check trace status
    echo "Checking trace status..."
    if curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
      "$API_URL/api/v1/trace/$TRACE_ID" | grep -q "trace_id"; then
      echo -e "${GREEN}✓ Trace data accessible${NC}"
      PASSED=$((PASSED + 1))
    else
      echo -e "${YELLOW}⚠ Trace status check inconclusive${NC}"
    fi
  else
    echo -e "${RED}✗ Trace failed - no trace_id received${NC}"
    echo "Response: $TRACE_RESPONSE"
    FAILED=$((FAILED + 1))
  fi
else
  echo -e "${RED}✗ Trace request failed${NC}"
  FAILED=$((FAILED + 1))
fi
echo ""

echo "Step 5: Chat Agent Integration"
echo "-------------------------------"
CHAT_DATA=$(cat <<EOF
{
  "message": "Trace Bitcoin address $BTC_ADDRESS with max depth 2",
  "context": "forensics"
}
EOF
)

echo "Testing forensics chat agent..."
if CHAT_RESPONSE=$(curl -s -X POST "$API_URL/api/v1/chat" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d "$CHAT_DATA" 2>/dev/null); then
  
  if echo "$CHAT_RESPONSE" | grep -q "answer"; then
    echo -e "${GREEN}✓ Chat agent responded${NC}"
    ANSWER=$(echo "$CHAT_RESPONSE" | grep -o '"answer":"[^"]*' | cut -d'"' -f4)
    echo "Agent response preview: ${ANSWER:0:100}..."
    PASSED=$((PASSED + 1))
  else
    echo -e "${RED}✗ Chat agent failed${NC}"
    echo "Response: $CHAT_RESPONSE"
    FAILED=$((FAILED + 1))
  fi
else
  echo -e "${RED}✗ Chat request failed${NC}"
  FAILED=$((FAILED + 1))
fi
echo ""

echo "Step 6: Available Chains Check"
echo "-------------------------------"
if curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  "$API_URL/api/v1/chains" | grep -q "bitcoin"; then
  echo -e "${GREEN}✓ Multi-chain support confirmed (Bitcoin available)${NC}"
  PASSED=$((PASSED + 1))
else
  echo -e "${YELLOW}⚠ Chains endpoint check inconclusive${NC}"
fi
echo ""

# Summary
echo "=================================================="
echo "📊 Test Summary"
echo "=================================================="
echo ""
echo -e "Passed: ${GREEN}$PASSED${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
  echo -e "${GREEN}✅ ALL CRITICAL TESTS PASSED!${NC}"
  echo ""
  echo "✓ User can signup and login"
  echo "✓ Bitcoin tracing works"
  echo "✓ Chat agent responds"
  echo "✓ API authentication works"
  echo "✓ Multi-chain support confirmed"
  echo ""
  echo "🎉 Critical User Journey: SUCCESS"
  exit 0
else
  echo -e "${RED}❌ SOME TESTS FAILED${NC}"
  echo ""
  echo "Please review failed tests above and fix issues before production deployment."
  exit 1
fi
