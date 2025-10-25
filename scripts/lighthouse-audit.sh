#!/bin/bash

# ===== LIGHTHOUSE PERFORMANCE AUDIT =====
# Runs Lighthouse CI for Performance, Accessibility, Best Practices, SEO

set -e

echo "🚢 Lighthouse Performance Audit"
echo "================================"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check if lighthouse is installed
if ! command -v lighthouse &> /dev/null; then
    echo "Installing Lighthouse CLI..."
    npm install -g lighthouse
fi

# URLs to test
URLS=(
    "http://localhost:5173/en"
    "http://localhost:5173/en/features"
    "http://localhost:5173/en/pricing"
)

# Thresholds
PERFORMANCE_MIN=90
SEO_MIN=90
ACCESSIBILITY_MIN=90
BEST_PRACTICES_MIN=85

echo ""
echo "Testing ${#URLS[@]} URLs..."
echo ""

TOTAL_SCORE=0
FAILED=0

for URL in "${URLS[@]}"; do
    echo "Testing: $URL"
    
    # Run Lighthouse
    lighthouse "$URL" \
        --output=html \
        --output=json \
        --output-path=./lighthouse-reports/$(echo $URL | md5) \
        --chrome-flags="--headless --no-sandbox" \
        --quiet 2>/dev/null || true
    
    # Parse JSON results
    REPORT=$(cat ./lighthouse-reports/$(echo $URL | md5).report.json 2>/dev/null || echo "{}")
    
    PERF=$(echo $REPORT | jq -r '.categories.performance.score * 100' 2>/dev/null || echo "0")
    SEO=$(echo $REPORT | jq -r '.categories.seo.score * 100' 2>/dev/null || echo "0")
    A11Y=$(echo $REPORT | jq -r '.categories.accessibility.score * 100' 2>/dev/null || echo "0")
    BP=$(echo $REPORT | jq -r '.categories["best-practices"].score * 100' 2>/dev/null || echo "0")
    
    # Round to integer
    PERF=${PERF%.*}
    SEO=${SEO%.*}
    A11Y=${A11Y%.*}
    BP=${BP%.*}
    
    echo "  Performance: $PERF/100"
    echo "  SEO: $SEO/100"
    echo "  Accessibility: $A11Y/100"
    echo "  Best Practices: $BP/100"
    
    # Check thresholds
    if [ "$PERF" -lt "$PERFORMANCE_MIN" ]; then
        echo -e "  ${RED}✗ Performance below $PERFORMANCE_MIN${NC}"
        FAILED=$((FAILED + 1))
    fi
    
    if [ "$SEO" -lt "$SEO_MIN" ]; then
        echo -e "  ${RED}✗ SEO below $SEO_MIN${NC}"
        FAILED=$((FAILED + 1))
    fi
    
    if [ "$A11Y" -lt "$ACCESSIBILITY_MIN" ]; then
        echo -e "  ${YELLOW}⚠ Accessibility below $ACCESSIBILITY_MIN${NC}"
    fi
    
    if [ "$BP" -lt "$BEST_PRACTICES_MIN" ]; then
        echo -e "  ${YELLOW}⚠ Best Practices below $BEST_PRACTICES_MIN${NC}"
    fi
    
    # Add to total
    AVG=$(( (PERF + SEO + A11Y + BP) / 4 ))
    TOTAL_SCORE=$((TOTAL_SCORE + AVG))
    
    echo ""
done

# Calculate average
AVG_SCORE=$((TOTAL_SCORE / ${#URLS[@]}))

echo "================================"
echo "Summary"
echo "================================"
echo "Average Score: $AVG_SCORE/100"
echo ""

if [ "$FAILED" -eq "0" ] && [ "$AVG_SCORE" -ge "90" ]; then
    echo -e "${GREEN}✅ Lighthouse Audit PASSED${NC}"
    echo "Status: Excellent Performance"
    exit 0
elif [ "$AVG_SCORE" -ge "80" ]; then
    echo -e "${YELLOW}⚠️  Lighthouse Audit PASSED with warnings${NC}"
    echo "Status: Good Performance"
    exit 0
else
    echo -e "${RED}❌ Lighthouse Audit FAILED${NC}"
    echo "Status: Performance improvements needed"
    exit 1
fi
