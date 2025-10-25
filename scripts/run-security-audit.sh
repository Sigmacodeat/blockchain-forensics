#!/bin/bash

# ===================================================================
# Security Audit Runner Script
# ===================================================================
# Führt vollständiges Security Audit durch und generiert Reports
# 
# Usage: ./scripts/run-security-audit.sh
# ===================================================================

set -e

echo "🔒 Starting Security Audit..."
echo "================================"
echo ""

# Farben für Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Erstelle Reports-Verzeichnis
mkdir -p security-reports

# Prüfe ob Tools installiert sind
check_tool() {
    if ! command -v $1 &> /dev/null; then
        echo -e "${YELLOW}⚠️  $1 nicht gefunden. Installiere...${NC}"
        return 1
    fi
    return 0
}

# Navigiere zu Backend
cd backend

# 1. Bandit Scan
echo "📝 [1/5] Running Bandit (Python Security Scanner)..."
if check_tool bandit; then
    bandit -r app/ -f json -o ../security-reports/bandit.json 2>&1 || true
    echo -e "${GREEN}✅ Bandit Scan abgeschlossen${NC}"
else
    pip install bandit
    bandit -r app/ -f json -o ../security-reports/bandit.json 2>&1 || true
fi
echo ""

# 2. Safety Check
echo "📦 [2/5] Running Safety (Dependency Vulnerability Scan)..."
if check_tool safety; then
    safety check --json > ../security-reports/safety.json 2>&1 || true
    echo -e "${GREEN}✅ Safety Scan abgeschlossen${NC}"
else
    pip install safety
    safety check --json > ../security-reports/safety.json 2>&1 || true
fi
echo ""

# 3. Semgrep Scan
echo "🔍 [3/5] Running Semgrep (SAST)..."
cd ..
if check_tool semgrep; then
    semgrep --config=.semgrep.yml --json --output=security-reports/semgrep.json backend/app/ 2>&1 || true
    echo -e "${GREEN}✅ Semgrep Scan abgeschlossen${NC}"
else
    pip install semgrep
    semgrep --config=.semgrep.yml --json --output=security-reports/semgrep.json backend/app/ 2>&1 || true
fi
echo ""

# 4. Secrets Detection
echo "🔐 [4/5] Running detect-secrets (Secrets Scanner)..."
if check_tool detect-secrets; then
    detect-secrets scan --all-files --force-use-all-plugins > security-reports/secrets.json 2>&1 || true
    echo -e "${GREEN}✅ Secrets Scan abgeschlossen${NC}"
else
    pip install detect-secrets
    detect-secrets scan --all-files --force-use-all-plugins > security-reports/secrets.json 2>&1 || true
fi
echo ""

# 5. Run Security Tests
echo "🧪 [5/5] Running Security Tests..."
cd backend
if pytest tests/security/ -v --tb=short 2>&1; then
    echo -e "${GREEN}✅ Security Tests bestanden${NC}"
else
    echo -e "${RED}❌ Security Tests fehlgeschlagen${NC}"
fi
echo ""

# 6. Generiere Gesamtreport
echo "📊 Generating Comprehensive Report..."
cd ..
python -c "
import asyncio
from backend.app.security.audit import SecurityAuditor

async def run():
    auditor = SecurityAuditor('.')
    report = await auditor.run_full_audit()
    print(report.summary)

asyncio.run(run())
" || echo -e "${YELLOW}⚠️ Report-Generierung fehlgeschlagen (Python-Modul)${NC}"

echo ""
echo "================================"
echo -e "${GREEN}✅ Security Audit abgeschlossen!${NC}"
echo ""
echo "📁 Reports gespeichert in: ./security-reports/"
echo ""
echo "📋 Nächste Schritte:"
echo "  1. Prüfe security-reports/security-audit_*.md"
echo "  2. Behebe CRITICAL und HIGH Issues prioritär"
echo "  3. Plane MEDIUM Issues für nächsten Sprint ein"
echo ""
