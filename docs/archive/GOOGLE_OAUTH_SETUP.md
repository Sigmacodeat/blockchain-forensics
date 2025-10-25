# Google OAuth Setup - Fehlerbehebung

## Problem
Der 500 Internal Server Error beim Google OAuth-Login tritt auf, weil die **Redirect URI** nicht in der Google Cloud Console konfiguriert ist.

## Aktuelle Konfiguration
- **Client ID**: `275040666797-rp1iumtlnfe93t87onandmk995mupdnj.apps.googleusercontent.com`
- **Callback URL**: `http://localhost:8000/api/v1/auth/oauth/google/callback`

## Lösung: Redirect URI in Google Console eintragen

### Schritt 1: Google Cloud Console öffnen
1. Gehe zu: https://console.cloud.google.com/apis/credentials
2. Wähle das Projekt aus (oder erstelle ein neues)

### Schritt 2: OAuth Client ID finden
1. Klicke auf die OAuth 2.0 Client ID mit der ID `275040666797-rp1iumtlnfe93t87onandmk995mupdnj`
2. Oder erstelle eine neue OAuth 2.0 Client ID:
   - Anwendungstyp: **Webanwendung**
   - Name: Blockchain Forensics Platform

### Schritt 3: Autorisierte Weiterleitungs-URIs hinzufügen
Füge diese URIs zur Liste hinzu:

**Für Entwicklung (localhost):**
```
http://localhost:8000/api/v1/auth/oauth/google/callback
http://localhost:3000/en/login
http://localhost:5173/en/login
```

**Für Produktion:**
```
https://your-domain.com/api/v1/auth/oauth/google/callback
https://your-domain.com/en/login
```

### Schritt 4: Speichern und neue Credentials kopieren
1. Klicke auf **Speichern**
2. Wenn du neue Credentials erstellt hast, kopiere:
   - Client-ID
   - Client-Secret

### Schritt 5: .env Datei aktualisieren
Erstelle/aktualisiere `backend/.env`:

```bash
# Google OAuth
GOOGLE_CLIENT_ID="DEINE_CLIENT_ID"
GOOGLE_CLIENT_SECRET="DEIN_CLIENT_SECRET"
OAUTH_CALLBACK_PATH="/api/v1/auth/oauth/google/callback"

# Optional: Admin-Emails (Komma-getrennt)
ADMIN_EMAILS="deine-email@example.com"
```

### Schritt 6: Backend neu starten
```bash
cd backend
# Wenn du Docker verwendest:
docker-compose restart backend

# Oder direkt:
uvicorn app.main:app --reload --port 8000
```

## Test der Konfiguration

### 1. Konfiguration prüfen
```bash
curl http://localhost:8000/api/v1/auth/oauth/google/config | python3 -m json.tool
```

Sollte zurückgeben:
```json
{
    "configured": true,
    "client_id": "275040666797-rp1iumt...",
    "callback_url": "http://localhost:8000/api/v1/auth/oauth/google/callback",
    "admin_emails": ["deine-email@example.com"]
}
```

### 2. OAuth Flow testen
1. Öffne Frontend: http://localhost:3000/en/login
2. Klicke auf "Mit Google anmelden"
3. Du solltest zur Google-Anmeldeseite weitergeleitet werden
4. Nach der Anmeldung zurück zur App

## Backend-Logs prüfen
Die verbesserten Logs zeigen jetzt genau, wo der Fehler auftritt:

```bash
# Logs in Echtzeit anzeigen
tail -f backend/logs/backend.log

# Oder wenn Backend direkt läuft:
# Die Logs erscheinen im Terminal
```

Du solltest Logs sehen wie:
```
INFO: OAuth callback URL: http://localhost:8000/api/v1/auth/oauth/google/callback
INFO: Exchanging code for tokens with Google
INFO: Fetching user info from Google
INFO: Processing OAuth login for email: user@example.com
INFO: Creating new user via OAuth: user@example.com with role viewer
```

## Häufige Fehler

### 1. "redirect_uri_mismatch"
**Problem**: Die Callback-URL stimmt nicht mit der in Google Console konfigurierten URI überein

**Lösung**: 
- Prüfe, dass die URL **exakt** übereinstimmt (inkl. http/https, Port, Pfad)
- Keine Leerzeichen am Anfang/Ende
- Kein abschließender Slash

### 2. "Token-Austausch fehlgeschlagen: invalid_grant"
**Problem**: Der Authorization Code ist abgelaufen oder ungültig

**Lösung**:
- Stelle sicher, dass die Redirect URI korrekt ist
- Der Code kann nur einmal verwendet werden
- Lösche Browser-Cache und versuche es erneut

### 3. "OAuth nicht konfiguriert" (503 Error)
**Problem**: GOOGLE_CLIENT_ID oder GOOGLE_CLIENT_SECRET fehlen in .env

**Lösung**:
- Prüfe backend/.env Datei
- Stelle sicher, dass keine Anführungszeichen im Wert sind (außer in .env.example)
- Starte Backend neu

### 4. Datenbankfehler beim User-Erstellen
**Problem**: PostgreSQL ist nicht erreichbar oder Schema fehlt

**Lösung**:
```bash
# Prüfe DB-Connection
psql $POSTGRES_URL

# Führe Migrations aus
cd backend
alembic upgrade head
```

## Sicherheitshinweise

⚠️ **WICHTIG für Produktion:**

1. **HTTPS verwenden**: OAuth sollte immer über HTTPS laufen
2. **Secrets schützen**: Niemals GOOGLE_CLIENT_SECRET im Code committen
3. **Environment Variables**: Verwende sichere Secret-Management-Systeme
4. **Redirect URIs einschränken**: Nur tatsächlich verwendete URIs eintragen

## Frontend-Integration

Die Frontend-Komponente `GoogleLoginButton` sollte so konfiguriert sein:

```typescript
// frontend/src/components/auth/GoogleLoginButton.tsx
const handleGoogleLogin = () => {
  const redirectUri = `${window.location.origin}${i18n.language ? `/${i18n.language}` : ''}/login`;
  window.location.href = `${API_URL}/api/v1/auth/oauth/google?redirect_uri=${encodeURIComponent(redirectUri)}`;
};
```

## Support

Bei weiteren Problemen:
1. Prüfe Backend-Logs für detaillierte Fehlermeldungen
2. Teste Konfiguration mit `/api/v1/auth/oauth/google/config`
3. Verifiziere Google Console Einstellungen

---

**Verbesserungen in dieser Version:**
- ✅ Besseres Error-Handling im Backend
- ✅ Detailliertes Logging für alle OAuth-Schritte
- ✅ Test-Endpoint für Konfigurationsprüfung
- ✅ Klare Fehlermeldungen (400/503 statt 500)
- ✅ Database Rollback bei Fehlern
