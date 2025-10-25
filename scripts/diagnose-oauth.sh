#!/bin/bash

# Google OAuth Diagnose-Script
# Prüft die OAuth-Konfiguration und zeigt potenzielle Probleme

set -e

echo "🔍 Google OAuth Diagnose"
echo "========================"
echo ""

# Farben für Ausgabe
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Prüfe Backend Server
echo "1️⃣  Backend Server Erreichbarkeit..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Backend läuft auf http://localhost:8000"
else
    echo -e "${RED}✗${NC} Backend ist nicht erreichbar!"
    echo "   Starte Backend mit: cd backend && uvicorn app.main:app --reload --port 8000"
    exit 1
fi
echo ""

# 2. Prüfe OAuth Konfiguration
echo "2️⃣  OAuth Konfiguration..."
CONFIG=$(curl -s http://localhost:8000/api/v1/auth/oauth/google/config)

CONFIGURED=$(echo "$CONFIG" | python3 -c "import sys, json; print(json.load(sys.stdin)['configured'])")
CLIENT_ID=$(echo "$CONFIG" | python3 -c "import sys, json; print(json.load(sys.stdin)['client_id'])")
CALLBACK_URL=$(echo "$CONFIG" | python3 -c "import sys, json; print(json.load(sys.stdin)['callback_url'])")
ADMIN_EMAILS=$(echo "$CONFIG" | python3 -c "import sys, json; print(json.load(sys.stdin)['admin_emails'])")

if [ "$CONFIGURED" = "True" ]; then
    echo -e "${GREEN}✓${NC} Google OAuth ist konfiguriert"
    echo "   Client ID: $CLIENT_ID"
    echo "   Callback URL: $CALLBACK_URL"
    if [ "$ADMIN_EMAILS" = "[]" ]; then
        echo -e "${YELLOW}⚠${NC}  Keine Admin-Emails konfiguriert"
    else
        echo "   Admin Emails: $ADMIN_EMAILS"
    fi
else
    echo -e "${RED}✗${NC} Google OAuth ist NICHT konfiguriert!"
    echo "   Setze GOOGLE_CLIENT_ID und GOOGLE_CLIENT_SECRET in backend/.env"
    echo "   Siehe GOOGLE_OAUTH_SETUP.md für Details"
    exit 1
fi
echo ""

# 3. Prüfe .env Datei
echo "3️⃣  .env Datei..."
if [ -f "backend/.env" ]; then
    echo -e "${GREEN}✓${NC} backend/.env existiert"
    
    # Prüfe ob wichtige Variablen gesetzt sind (ohne Werte zu zeigen)
    if grep -q "GOOGLE_CLIENT_ID=" backend/.env; then
        echo -e "${GREEN}✓${NC} GOOGLE_CLIENT_ID ist gesetzt"
    else
        echo -e "${RED}✗${NC} GOOGLE_CLIENT_ID fehlt in .env"
    fi
    
    if grep -q "GOOGLE_CLIENT_SECRET=" backend/.env; then
        echo -e "${GREEN}✓${NC} GOOGLE_CLIENT_SECRET ist gesetzt"
    else
        echo -e "${RED}✗${NC} GOOGLE_CLIENT_SECRET fehlt in .env"
    fi
    
    if grep -q "POSTGRES_URL=" backend/.env; then
        echo -e "${GREEN}✓${NC} POSTGRES_URL ist gesetzt"
    else
        echo -e "${YELLOW}⚠${NC}  POSTGRES_URL fehlt in .env"
    fi
else
    echo -e "${RED}✗${NC} backend/.env nicht gefunden!"
    echo "   Erstelle eine .env Datei basierend auf backend/.env.example"
    echo "   cp backend/.env.example backend/.env"
    exit 1
fi
echo ""

# 4. Prüfe Datenbank-Connection
echo "4️⃣  Datenbank-Verbindung..."
# Versuche eine einfache Query über den Backend-Endpoint
if curl -s http://localhost:8000/api/v1/health 2>&1 | grep -q "ok\|healthy"; then
    echo -e "${GREEN}✓${NC} Datenbank ist erreichbar"
else
    echo -e "${YELLOW}⚠${NC}  Konnte Datenbank-Status nicht prüfen"
    echo "   Prüfe PostgreSQL-Connection manuell"
fi
echo ""

# 5. Google Console Redirect URIs
echo "5️⃣  Google Cloud Console Checkliste..."
echo ""
echo "   📝 Stelle sicher, dass in der Google Cloud Console folgende"
echo "      Redirect URIs eingetragen sind:"
echo ""
echo "   ${CALLBACK_URL}"
echo "   http://localhost:3000/en/login"
echo "   http://localhost:5173/en/login"
echo ""
echo "   🔗 Gehe zu: https://console.cloud.google.com/apis/credentials"
echo "   1. Wähle dein OAuth 2.0 Client"
echo "   2. Füge die URIs unter 'Autorisierte Weiterleitungs-URIs' hinzu"
echo "   3. Speichern"
echo ""

# 6. Test OAuth Flow
echo "6️⃣  OAuth Flow Test..."
echo ""
echo "   Um den OAuth Flow zu testen:"
echo "   1. Öffne: http://localhost:3000/en/login"
echo "   2. Klicke auf 'Mit Google anmelden'"
echo "   3. Du wirst zu Google weitergeleitet"
echo "   4. Nach Anmeldung zurück zur App"
echo ""

# 7. Logs prüfen
echo "7️⃣  Backend-Logs überwachen..."
echo ""
echo "   Führe in einem separaten Terminal aus:"
echo "   ${YELLOW}tail -f backend/logs/backend.log${NC}"
echo ""
echo "   Oder wenn Backend direkt läuft, siehst du die Logs im Terminal"
echo ""

# 8. Zusammenfassung
echo "📊 Zusammenfassung"
echo "=================="
echo ""
if [ "$CONFIGURED" = "True" ]; then
    echo -e "${GREEN}✓${NC} Backend läuft und OAuth ist konfiguriert"
    echo ""
    echo "   Nächste Schritte:"
    echo "   1. Prüfe Google Console Redirect URIs (siehe oben)"
    echo "   2. Teste OAuth Flow im Browser"
    echo "   3. Bei Problemen: Siehe GOOGLE_OAUTH_SETUP.md"
else
    echo -e "${RED}✗${NC} Es gibt Konfigurationsprobleme"
    echo ""
    echo "   Siehe Fehler oben und GOOGLE_OAUTH_SETUP.md"
fi
echo ""
