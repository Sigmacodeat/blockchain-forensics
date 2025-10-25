# Google OAuth 500 Error - Schnelle Lösung ⚡

## Problem
`GET http://localhost:8000/api/v1/auth/oauth/google/callback?... 500 (Internal Server Error)`

## Ursache
Die **Redirect URI** ist nicht in der Google Cloud Console registriert.

## ✅ Schnelle Lösung (5 Minuten)

### Schritt 1: Google Console öffnen
🔗 https://console.cloud.google.com/apis/credentials

### Schritt 2: OAuth Client bearbeiten
1. Klicke auf den Client mit ID: `275040666797-rp1iumtlnfe93t87onandmk995mupdnj`
2. ODER erstelle einen neuen OAuth 2.0 Client (Webanwendung)

### Schritt 3: Diese URIs hinzufügen

**Kopiere und füge diese in "Autorisierte Weiterleitungs-URIs" ein:**

```
http://localhost:8000/api/v1/auth/oauth/google/callback
http://localhost:3000/en/login
http://localhost:5173/en/login
```

⚠️ **WICHTIG**: 
- Keine Leerzeichen
- Kein Slash am Ende
- Exakt wie oben kopieren

### Schritt 4: Speichern
Klicke auf **Speichern** (unten rechts)

### Schritt 5: Testen
1. Warte 1-2 Minuten (Google braucht Zeit zum Update)
2. Öffne: http://localhost:3000/en/login
3. Klicke auf "Mit Google anmelden"
4. ✅ Sollte jetzt funktionieren!

---

## 🔧 Backend-Verbesserungen (bereits implementiert)

Ich habe das Backend verbessert mit:

### 1. Besseres Error-Handling
- Klare Fehlermeldungen statt generischer 500-Fehler
- Detailliertes Logging für Debugging
- Database Rollback bei Fehlern

### 2. Neue Test-Route
```bash
curl http://localhost:8000/api/v1/auth/oauth/google/config
```

Zeigt:
- Ob OAuth konfiguriert ist
- Callback URL
- Client ID (maskiert)
- Admin Emails

### 3. Diagnose-Script
```bash
./scripts/diagnose-oauth.sh
```

Prüft automatisch:
- Backend-Status
- OAuth-Konfiguration
- .env Datei
- Datenbank-Connection

---

## 📋 Logs prüfen

Backend-Logs zeigen jetzt genau, was passiert:

```bash
# Terminal wo Backend läuft
# Du siehst jetzt Logs wie:
INFO: OAuth callback URL: http://localhost:8000/api/v1/auth/oauth/google/callback
INFO: Exchanging code for tokens with Google
INFO: Fetching user info from Google
INFO: Processing OAuth login for email: user@example.com
```

Bei Fehlern:
```
ERROR: Token exchange failed: 400 - {...}
ERROR: Database error during OAuth user creation/update: ...
```

---

## ❓ Häufige Fehler nach dem Fix

### "redirect_uri_mismatch" 
✅ **Gelöst** durch Schritt 3 oben

### "Token exchange failed: invalid_grant"
⚠️ **Ursache**: Authorization Code ist abgelaufen (nur 10 Min gültig)
🔧 **Lösung**: Noch mal versuchen, nicht den Browser zurück-Button nutzen

### "Userinfo request failed: 401"
⚠️ **Ursache**: Access Token ungültig
🔧 **Lösung**: Prüfe GOOGLE_CLIENT_SECRET in backend/.env

### Datenbank-Fehler
⚠️ **Ursache**: PostgreSQL nicht erreichbar
🔧 **Lösung**: 
```bash
# Starte PostgreSQL
brew services start postgresql@14

# Oder mit Docker
docker-compose up -d postgres

# Migrations ausführen
cd backend
alembic upgrade head
```

---

## 🎉 Nach dem Fix

Du solltest sehen:
1. Google-Login-Seite öffnet sich
2. Du meldest dich an
3. Du wirst zurück zur App geleitet
4. Du bist eingeloggt! ✅

Im Backend-Log:
```
INFO: Processing OAuth login for email: deine-email@gmail.com
INFO: Creating new user via OAuth: deine-email@gmail.com with role viewer
```

---

## 📚 Weitere Hilfe

- **Vollständige Anleitung**: Siehe `GOOGLE_OAUTH_SETUP.md`
- **Diagnose**: `./scripts/diagnose-oauth.sh`
- **Backend-Logs**: Terminal wo Backend läuft

## 🔐 Admin-Zugang (Optional)

Um automatisch Admin-Rechte zu bekommen:

```bash
# In backend/.env hinzufügen:
ADMIN_EMAILS="deine-email@gmail.com"

# Backend neu starten
```

Beim nächsten Login bekommst du Admin-Rolle! 👑
