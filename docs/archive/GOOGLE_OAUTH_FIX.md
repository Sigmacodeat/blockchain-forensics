# Google OAuth Fix - Dokumentation

## Problem

**Fehlermeldung:**
```json
{"detail":"Google OAuth nicht konfiguriert. Bitte GOOGLE_CLIENT_ID und GOOGLE_CLIENT_SECRET setzen."}
```

## Ursache

Das Backend lädt die `.env` Datei aus dem `backend/` Verzeichnis, **nicht** aus dem Root-Verzeichnis. 

- ✅ Root `.env` hatte die Google OAuth Variablen
- ❌ `backend/.env` existierte nicht oder hatte sie nicht

## Lösung

### 1. Google OAuth Variablen in `backend/.env` kopieren

Die folgenden Variablen müssen in `backend/.env` vorhanden sein:

```bash
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here
OAUTH_CALLBACK_PATH=/api/v1/auth/oauth/google/callback
```

### 2. Variablen von Root nach Backend kopieren

```bash
# Aus dem Root-Verzeichnis
grep -E "GOOGLE_CLIENT|OAUTH_CALLBACK" .env >> backend/.env
```

### 3. Verifizierung

```bash
cd backend
python -c "from app.config import settings; print('✅ OK' if settings.GOOGLE_CLIENT_ID else '❌ FEHLT')"
```

## Warum passiert das?

Das Backend lädt `.env` Dateien so:

1. **Pydantic Settings** in `backend/app/config.py` (Zeile 296):
   ```python
   model_config = SettingsConfigDict(
       env_file=(".env" if _use_env_file else None),  # Lädt .env aus CWD
       case_sensitive=True
   )
   ```

2. **Current Working Directory (CWD)** ist `backend/` wenn das Backend läuft

3. Daher sucht Pydantic nach `backend/.env`, nicht nach `.env` im Root

## Langfristige Lösung

### Option A: Symlink (empfohlen für Development)

```bash
ln -s ../.env backend/.env
```

**Vorteile:**
- Eine einzige .env für alle Services
- Automatische Synchronisation

**Nachteile:**
- Symlinks können in manchen Deployment-Szenarien Probleme machen

### Option B: Separate .env Dateien (empfohlen für Production)

- Root `.env` für Frontend/Docker Compose
- `backend/.env` für Backend-spezifische Variablen

**Vorteile:**
- Klare Trennung
- Deployment-freundlich

**Nachteile:**
- Duplikation von Variablen

## Google OAuth Setup

### Google Cloud Console

1. Gehe zu https://console.cloud.google.com/
2. Erstelle ein neues Projekt oder wähle ein bestehendes
3. Aktiviere Google+ API
4. Erstelle OAuth 2.0 Client ID:
   - Anwendungstyp: Webanwendung
   - Autorisierte JavaScript-Ursprünge: `http://localhost:8000`, `http://localhost:5173`
   - Autorisierte Weiterleitungs-URIs: `http://localhost:8000/api/v1/auth/oauth/google/callback`
5. Kopiere Client-ID und Client-Secret

### Backend .env

```bash
GOOGLE_CLIENT_ID=275040666797-xxxxxxxxxxxxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-xxxxxxxxxxxxxx
OAUTH_CALLBACK_PATH=/api/v1/auth/oauth/google/callback
```

### Frontend .env

```bash
VITE_GOOGLE_CLIENT_ID=275040666797-xxxxxxxxxxxxx.apps.googleusercontent.com
```

## Test

```bash
# Backend
cd backend
python -c "from app.config import settings; print(settings.GOOGLE_CLIENT_ID)"

# Frontend (wenn React)
cd frontend
cat .env | grep VITE_GOOGLE_CLIENT_ID
```

## Troubleshooting

### Fehler: "Google OAuth nicht konfiguriert"

1. Prüfe `backend/.env`:
   ```bash
   cat backend/.env | grep GOOGLE
   ```

2. Prüfe ob Backend die Variablen lädt:
   ```bash
   cd backend
   python -c "from app.config import settings; print(settings.GOOGLE_CLIENT_ID)"
   ```

3. Prüfe ob `.env` Datei im gitignore ist:
   ```bash
   grep ".env" .gitignore
   ```

### Fehler: "redirect_uri_mismatch"

1. Prüfe autorisierte URIs in Google Console
2. Stelle sicher, dass `OAUTH_CALLBACK_PATH` korrekt ist
3. Prüfe ob Backend-URL korrekt ist (localhost vs. 127.0.0.1)

## Status

✅ **BEHOBEN**: Google OAuth Variablen sind jetzt in `backend/.env` und werden korrekt geladen.

## Dateien geändert

1. ✅ `backend/.env` - Google OAuth Variablen hinzugefügt
2. ✅ `.env.example` - Google OAuth Variablen dokumentiert
3. ✅ `backend/.env.example` - Google OAuth Variablen dokumentiert
4. ✅ `GOOGLE_OAUTH_FIX.md` - Diese Dokumentation

## Nächste Schritte

- [ ] Prüfe ob Frontend auch VITE_GOOGLE_CLIENT_ID hat
- [ ] Teste Google Login Flow im Frontend
- [ ] Prüfe ob Callback-URL in Google Console registriert ist
- [ ] Überlege Symlink vs. separate .env Dateien für Production
