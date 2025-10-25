# Deployment Guide (Privates GitHub + Server)

Dieser Guide bringt euch mit möglichst wenig Klicks live: Images werden privat auf GHCR gebaut/gespeichert, der Server zieht die Images mit Docker Compose.

## 1) Private GitHub Repo + Push
1. Privates Repo anlegen (z.B. `github.com/<ORG>/<REPO>`)
2. Lokal:
   ```bash
   git init
   git remote add origin git@github.com:<ORG>/<REPO>.git
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git push -u origin main
   ```
3. CI/Build: Läuft automatisch (Workflows vorhanden)
   - `.github/workflows/ci.yml`: Tests
   - `.github/workflows/build-images.yml`: Build & Push Docker Images zu GHCR

Images landen als:
- `ghcr.io/<org>/<repo>-backend:latest` (und `:sha-<commit>`)
- `ghcr.io/<org>/<repo>-frontend:latest` (und `:sha-<commit>`)

Hinweis: GHCR benötigt keine extra Secrets für Push, `GITHUB_TOKEN` reicht innerhalb Actions.

## 2) Server vorbereiten
Auf dem Zielserver:
- Docker + Docker Compose Plugin installieren
- Login zu GHCR (PAT notwendig mit `read:packages`)
  ```bash
  echo <YOUR_GHCR_PAT> | docker login ghcr.io -u <GITHUB_USERNAME> --password-stdin
  ```

## 3) Compose-Deploy
1. Variablen-Datei erstellen: `deploy/.env` (Beispiel siehe `.env.sample`)
2. Starten:
   ```bash
   docker compose -f deploy/compose.yml --env-file deploy/.env pull
   docker compose -f deploy/compose.yml --env-file deploy/.env up -d
   ```

Wichtige Variablen in `deploy/.env`:
- `GH_OWNER` = GitHub Owner (klein geschrieben empfiehlt sich)
- `GH_REPO` = Repository-Name (klein)
- `TAG` = `latest` oder ein konkreter Commit-Tag `sha-<commit>`
- `NEO4J_PASSWORD`, `POSTGRES_PASSWORD` (Prod-Strong-Passwords)
- `OPENAI_API_KEY` (optional für AI Agents)
- `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` (optional für OAuth)

## 4) Endpunkte prüfen
- Backend Health: `http://<SERVER_IP>:8000/health`
- Frontend: `http://<SERVER_IP>:3000`
- Prometheus: `http://<SERVER_IP>:9090`
- Grafana: `http://<SERVER_IP>:3003` (Login: admin / `${GRAFANA_PASSWORD}`)
- Jaeger (Tracing UI): `http://<SERVER_IP>:16686`

## 5) Manuelles Update (Rolling)
```bash
# neue Images ziehen
docker compose -f deploy/compose.yml --env-file deploy/.env pull
# nur geänderte Services neu starten
docker compose -f deploy/compose.yml --env-file deploy/.env up -d
```

## 6) Optional: GitHub Actions Deployment per SSH
Ein Template liegt in `.github/workflows/deploy-via-ssh.yml.disabled`.
- Setze Repo-Secrets:
  - `DEPLOY_HOST` (server.example.com)
  - `DEPLOY_USER` (z.B. ubuntu)
  - `DEPLOY_SSH_KEY` (private key, base64 oder als Klartext Secret)
  - `DEPLOY_DIR` (z.B. `/opt/blockchain-forensics`)
  - `GHCR_PAT` (PAT mit `read:packages`)
- Aktiviere den Workflow (Datei nach `deploy-via-ssh.yml` umbenennen).

Der Workflow führt remote aus:
```bash
mkdir -p $DEPLOY_DIR
cd $DEPLOY_DIR
# .env vom Secret/Runner bereitstellen oder vorhalten
docker login ghcr.io -u $GITHUB_ACTOR -p $GHCR_PAT
curl -fsSL https://raw.githubusercontent.com/<ORG>/<REPO>/main/deploy/compose.yml -o compose.yml
# .env muss im selben Ordner liegen
docker compose --env-file .env pull
docker compose --env-file .env up -d
```

## 7) Pre-commit (lokal)
```bash
pip install pre-commit
pre-commit install
pre-commit run -a
```

## Hinweise
- Ports in `deploy/compose.yml` ggf. anpassen (80/443 via Reverse Proxy empfohlen).
- Für Production TLS/Domain via Traefik/Caddy/NGINX vorsehen.
- Backups: Volumes für Neo4j/Postgres sichern (Snapshot/Backup-Plan).
- Secrets gehören nicht ins Repo – nur in `.env` auf dem Server oder als GitHub Secrets.
