# Webhooks (Node.js, TypeScript)

Harter, produktionsnaher Webhook-Listener mit Signaturprüfung (V2/Legacy), Idempotenz & Replay-Protection, Rate-Limit, IP-Allowlist, asynchroner Verarbeitung via Redis Streams, Retry mit Exponential Backoff und DLQ.

## Verzeichnis
- `express.ts`: Webhook-HTTP-Endpoint (Express)
- `verify.ts`: Signaturprüfung (V2 bevorzugt, Legacy Fallback)
- `send.ts`: Test-Sender
- `worker.ts`: Stream-Consumer mit Retry & DLQ
- `inspect-dlq.ts`: DLQ inspizieren
- `requeue.ts`: DLQ-Message zurück in Stream

## Voraussetzungen
- Node.js 18+
- Redis 7+ (lokal oder via Docker)

## Installation
```bash
npm install
```

## ENV-Variablen
- Auth/Signaturen
  - `WEBHOOK_SECRETS`: Komma-separierte Secrets (Rotation), z. B. `s1,s2`. Falls leer, Fallback `WEBHOOK_SECRET`.
  - `WEBHOOK_SECRET`: Einzelnes Secret (Fallback)
- Listener
  - `PORT`: Port des HTTP-Servers (Default 3001)
  - `RATE_WINDOW_MS` (Default 60000), `RATE_MAX` (Default 120)
  - `IP_ALLOWLIST`: Komma-separierte Liste erlaubter IPs (optional)
  - `TRUST_PROXY=1`: Aktivieren, wenn hinter Proxy/Load Balancer
  - `REDIS_URL`: z. B. `redis://localhost:6379`
  - `WEBHOOK_STREAM`: Redis Stream für Events (Default `webhook:events`)
- Worker
  - `REDIS_URL`: z. B. `redis://localhost:6379`
  - `WEBHOOK_STREAM` (Default `webhook:events`)
  - `WEBHOOK_GROUP` (Default `webhook-workers`)
  - `WEBHOOK_CONSUMER` (auto Default)
  - `WEBHOOK_DLQ` (Default `webhook:dlq`)
  - `MAX_ATTEMPTS` (Default 3), `BACKOFF_BASE_SEC` (Default 5)
- Sender (`send.ts`)
  - `WEBHOOK_URL`: Ziel-URL (Default `http://localhost:3001/webhook`)
  - `WEBHOOK_SECRET`: Secret für Signaturbildung
  - `DELIVERY_ID`: Optional, ansonsten wird eine generiert
  - `PAYLOAD`: Optionales JSON (String)

## Start (mit Redis, Async-Verarbeitung)
1) Listener starten
```bash
PORT=3060 REDIS_URL=redis://localhost:6379 WEBHOOK_STREAM=webhook:events npm run dev
```

2) Worker starten
```bash
REDIS_URL=redis://localhost:6379 WEBHOOK_STREAM=webhook:events WEBHOOK_GROUP=webhook-workers npm run worker
```

3) Test senden
```bash
WEBHOOK_URL=http://localhost:3060/webhook WEBHOOK_SECRET=replace-me npx -y tsx send.ts
```

## Sicherheitsfeatures
- Content-Type Check (`application/json`)
- Signaturprüfung V2 (`x-webhook-timestamp`, `x-webhook-signature-v2`)
- Legacy-Signatur als Fallback (`x-webhook-signature`)
- Pflicht-Delivery-ID (`x-webhook-delivery` oder `idempotency-key`)
- Idempotenz: Redis `SET NX EX` (24h), Fallback In-Memory
- Rate Limit pro Route `/webhook`
- Optionale IP-Allowlist
- Graceful Shutdown (Server & Redis)

## Asynchrone Verarbeitung
- Listener enqueued Events nach Redis Stream (`WEBHOOK_STREAM`)
- Worker konsumiert via Consumer-Group
- Retry mit Exponential Backoff über `attempts` und `next_ts`
- DLQ (`WEBHOOK_DLQ`) für invalide Events oder nach Max-Versuchen

## DLQ Werkzeuge
- DLQ inspizieren
```bash
REDIS_URL=redis://localhost:6379 npm run dlq:inspect
```
- DLQ requeue
```bash
REDIS_URL=redis://localhost:6379 npm run dlq:requeue
# Optional eine bestimmte DLQ-ID:
REDIS_URL=redis://localhost:6379 DLQ_ID=<id> npm run dlq:requeue
```

## Troubleshooting
- 400 `invalid content-type`: Sender muss `content-type: application/json` setzen
- 400 `invalid signature`: Secret/Signatur-/Zeitstempel prüfen (±5min Window)
- 400 `missing delivery id`: Header `x-webhook-delivery` oder `idempotency-key` setzen
- `EADDRINUSE`: Anderen Port wählen (`PORT`)
- Redis nicht erreichbar: `REDIS_URL` prüfen oder Redis starten (z. B. Docker)

## Docker (optional)
Redis lokal starten:
```bash
docker run -d --name redis -p 6379:6379 redis:7
```
