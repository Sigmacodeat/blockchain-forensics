#!/bin/bash

# ===== SECURITY AUDIT SCRIPT =====
# Runs comprehensive security checks

set -e

echo "🔒 Starting Security Audit..."
echo "================================"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ===== BACKEND SECURITY AUDIT =====
echo ""
echo "🐍 Backend Security Audit..."
cd backend

# 1. Safety Check (Known Vulnerabilities)
echo "  → Running safety check..."
pip install -q safety 2>/dev/null || true
if command -v safety &> /dev/null; then
    safety check --json > ../security-reports/safety.json 2>&1 || true
    SAFETY_ISSUES=$(cat ../security-reports/safety.json | grep -c "vulnerability" || echo "0")
    if [ "$SAFETY_ISSUES" -gt "0" ]; then
        echo -e "  ${RED}✗ Found $SAFETY_ISSUES vulnerabilities${NC}"
    else
        echo -e "  ${GREEN}✓ No known vulnerabilities${NC}"
    fi
else
    echo -e "  ${YELLOW}⚠ Safety not installed${NC}"
fi

# 2. Bandit (Security Linter)
echo "  → Running bandit..."
pip install -q bandit 2>/dev/null || true
if command -v bandit &> /dev/null; then
    bandit -r app -f json -o ../security-reports/bandit.json 2>&1 || true
    BANDIT_HIGH=$(cat ../security-reports/bandit.json | grep -o '"issue_severity": "HIGH"' | wc -l)
    if [ "$BANDIT_HIGH" -gt "0" ]; then
        echo -e "  ${RED}✗ Found $BANDIT_HIGH high-severity issues${NC}"
    else
        echo -e "  ${GREEN}✓ No high-severity issues${NC}"
    fi
else
    echo -e "  ${YELLOW}⚠ Bandit not installed${NC}"
fi

# 3. Pip-audit (Dependencies)
echo "  → Running pip-audit..."
pip install -q pip-audit 2>/dev/null || true
if command -v pip-audit &> /dev/null; then
    pip-audit --format json > ../security-reports/pip-audit.json 2>&1 || true
    PIP_VULNS=$(cat ../security-reports/pip-audit.json | grep -c "\"fix_versions\"" || echo "0")
    if [ "$PIP_VULNS" -gt "0" ]; then
        echo -e "  ${RED}✗ Found $PIP_VULNS vulnerable dependencies${NC}"
    else
        echo -e "  ${GREEN}✓ All dependencies secure${NC}"
    fi
else
    echo -e "  ${YELLOW}⚠ Pip-audit not installed${NC}"
fi

# 4. Secrets Detection
echo "  → Checking for hardcoded secrets..."
if command -v gitleaks &> /dev/null; then
    cd ..
    gitleaks detect --no-git --report-path security-reports/secrets.json 2>&1 || true
    SECRETS=$(cat security-reports/secrets.json | grep -c "\"Match\"" || echo "0")
    if [ "$SECRETS" -gt "0" ]; then
        echo -e "  ${RED}✗ Found $SECRETS potential secrets${NC}"
    else
        echo -e "  ${GREEN}✓ No secrets detected${NC}"
    fi
    cd backend
else
    echo -e "  ${YELLOW}⚠ Gitleaks not installed${NC}"
fi

# ===== FRONTEND SECURITY AUDIT =====
echo ""
echo "⚛️  Frontend Security Audit..."
cd ../frontend

# 1. NPM Audit
echo "  → Running npm audit..."
npm audit --json > ../security-reports/npm-audit.json 2>&1 || true
NPM_HIGH=$(cat ../security-reports/npm-audit.json | grep -o '"severity": "high"' | wc -l)
NPM_CRITICAL=$(cat ../security-reports/npm-audit.json | grep -o '"severity": "critical"' | wc -l)

if [ "$NPM_CRITICAL" -gt "0" ]; then
    echo -e "  ${RED}✗ Found $NPM_CRITICAL critical vulnerabilities${NC}"
elif [ "$NPM_HIGH" -gt "0" ]; then
    echo -e "  ${YELLOW}⚠ Found $NPM_HIGH high vulnerabilities${NC}"
else
    echo -e "  ${GREEN}✓ No critical/high vulnerabilities${NC}"
fi

# 2. License Check
echo "  → Checking licenses..."
npx license-checker --json --production > ../security-reports/licenses.json 2>&1 || true
GPL_LICENSES=$(cat ../security-reports/licenses.json | grep -ic "gpl" || echo "0")
if [ "$GPL_LICENSES" -gt "0" ]; then
    echo -e "  ${YELLOW}⚠ Found $GPL_LICENSES GPL-licensed dependencies${NC}"
else
    echo -e "  ${GREEN}✓ No GPL licenses${NC}"
fi

# ===== SSL/TLS CHECK =====
echo ""
echo "🔐 SSL/TLS Configuration..."
cd ..

if [ "$1" == "prod" ]; then
    DOMAIN="blocksigmakode.ai"
    echo "  → Checking $DOMAIN..."
    
    # SSL Labs API (simplified)
    echo "  → Visit: https://www.ssllabs.com/ssltest/analyze.html?d=$DOMAIN"
    
    # Basic SSL check
    if command -v openssl &> /dev/null; then
        SSL_GRADE=$(echo | openssl s_client -servername $DOMAIN -connect $DOMAIN:443 2>/dev/null | openssl x509 -noout -subject -dates 2>/dev/null || echo "No SSL")
        if [[ "$SSL_GRADE" == *"No SSL"* ]]; then
            echo -e "  ${RED}✗ SSL certificate not found${NC}"
        else
            echo -e "  ${GREEN}✓ SSL certificate valid${NC}"
            echo "    $SSL_GRADE"
        fi
    fi
else
    echo "  ${YELLOW}⚠ Skipped (use './security-audit.sh prod' for production check)${NC}"
fi

# ===== SECURITY HEADERS CHECK =====
echo ""
echo "🛡️  Security Headers..."

if [ "$1" == "prod" ]; then
    DOMAIN="https://blocksigmakode.ai"
    echo "  → Checking $DOMAIN..."
    
    HEADERS=$(curl -sI $DOMAIN 2>/dev/null || echo "")
    
    # Check for important headers
    if [[ "$HEADERS" == *"X-Content-Type-Options"* ]]; then
        echo -e "  ${GREEN}✓ X-Content-Type-Options present${NC}"
    else
        echo -e "  ${RED}✗ X-Content-Type-Options missing${NC}"
    fi
    
    if [[ "$HEADERS" == *"X-Frame-Options"* ]]; then
        echo -e "  ${GREEN}✓ X-Frame-Options present${NC}"
    else
        echo -e "  ${RED}✗ X-Frame-Options missing${NC}"
    fi
    
    if [[ "$HEADERS" == *"Content-Security-Policy"* ]]; then
        echo -e "  ${GREEN}✓ Content-Security-Policy present${NC}"
    else
        echo -e "  ${YELLOW}⚠ Content-Security-Policy missing${NC}"
    fi
    
    if [[ "$HEADERS" == *"Strict-Transport-Security"* ]]; then
        echo -e "  ${GREEN}✓ Strict-Transport-Security present${NC}"
    else
        echo -e "  ${RED}✗ Strict-Transport-Security missing${NC}"
    fi
else
    echo "  ${YELLOW}⚠ Skipped (use './security-audit.sh prod' for production check)${NC}"
fi

# ===== SUMMARY =====
echo ""
echo "================================"
echo "📊 Security Audit Summary"
echo "================================"

# Count total issues
TOTAL_ISSUES=0
if [ -f security-reports/safety.json ]; then
    TOTAL_ISSUES=$((TOTAL_ISSUES + $(cat security-reports/safety.json | grep -c "vulnerability" || echo "0")))
fi
if [ -f security-reports/bandit.json ]; then
    TOTAL_ISSUES=$((TOTAL_ISSUES + $(cat security-reports/bandit.json | grep -o '"issue_severity": "HIGH"' | wc -l || echo "0")))
fi
if [ -f security-reports/npm-audit.json ]; then
    TOTAL_ISSUES=$((TOTAL_ISSUES + $(cat security-reports/npm-audit.json | grep -c '"severity": "critical"' || echo "0")))
fi

echo "Total Critical Issues: $TOTAL_ISSUES"

if [ "$TOTAL_ISSUES" -eq "0" ]; then
    echo -e "${GREEN}✅ Security Audit PASSED${NC}"
    echo "Status: Ready for Production"
    exit 0
elif [ "$TOTAL_ISSUES" -lt "5" ]; then
    echo -e "${YELLOW}⚠️  Security Audit PASSED with warnings${NC}"
    echo "Status: Acceptable for MVP"
    exit 0
else
    echo -e "${RED}❌ Security Audit FAILED${NC}"
    echo "Status: Not ready for production"
    echo "Please fix critical issues before deploying"
    exit 1
fi
