# Developer API Quickstart

Dieser Quickstart zeigt, wie du unsere API sicher einbindest (JWT oder X-API-Key), welche Endpunkte monetarisierbar sind und wie du Realtime-Features (WebSocket/SSE) nutzt.

## Authentifizierung

- JWT: `Authorization: Bearer <token>` (enthält u.a. `plan`)
- API-Key (Server-seitig): `X-API-Key: <key>` (DB-validiert, Tiers: free/pro/enterprise)

Hinweis: Einige Endpunkte sind plan-geschützt (z.B. KYT business+, Alerts v2 plus, Threat Intel v2 pro/business/enterprise). Bei Verstoß: 403 oder WS-Code 4401.

## Rate Limits & Quotas

- Per-Plan Limits (z.B. community: 10 req/min, pro: 100 req/min, etc.)
- 429 bei Überschreitung, Header: `Retry-After`, `X-RateLimit-*`
- Quota/Usage: `GET /api/v1/usage/current` und `GET /api/v1/billing/usage`

---

## Risk Scoring (REST + SSE)

- Einzeladresse (REST):
```bash
curl -H "Authorization: Bearer $TOKEN" \
     "https://<host>/api/v1/risk/address?chain=ethereum&address=0x0000000000000000000000000000000000000000"
```
Antwort (gekürzt): `{ result: { chain, address, score, categories, reasons } }`

- Streaming (SSE):
```bash
curl -H "Authorization: Bearer $TOKEN" \
     -N "https://<host>/api/v1/risk/stream?chain=ethereum&address=0x..."
```
Events: `risk.ready`, `risk.typing`, `risk.result`, `risk.error`

---

## KYT – Real-Time Transaction Monitoring (WS + REST)

- WebSocket (business+):
```js
const ws = new WebSocket("wss://<host>/api/v1/ws/kyt", {
  headers: { Authorization: `Bearer ${token}` }
});
ws.onopen = () => ws.send(JSON.stringify({ action: "subscribe", user_id: "demo" }));
ws.onmessage = (e) => console.log("KYT:", JSON.parse(e.data));
```

- Analyse per REST (business+):
```bash
curl -H "Authorization: Bearer $TOKEN" \
     -H 'Content-Type: application/json' \
     -d '{"chain":"ethereum","from_address":"0x...","to_address":"0x...","value_eth":0.1}' \
     https://<host>/api/v1/kyt/analyze
```

---

## Threat Intelligence

- Enrichment (pro+):
```bash
curl -H "Authorization: Bearer $TOKEN" \
     -H 'Content-Type: application/json' \
     -d '{"chain":"ethereum","address":"0x..."}' \
     https://<host>/api/v1/threat-intel/enrich
```

- Dark Web Search (plus+):
```bash
curl -H "Authorization: Bearer $TOKEN" \
     "https://<host>/api/v1/threat-intel/darkweb/search?address=0x...&min_confidence=0.7"
```

---

## Wallet Scanner (Zero-Trust)

- Adressen-Scan (pro+):
```bash
curl -H "Authorization: Bearer $TOKEN" \
     -H 'Content-Type: application/json' \
     -d '{"addresses":[{"chain":"ethereum","address":"0x..."}],"check_history":true,"check_illicit":true}' \
     https://<host>/api/v1/wallet-scanner/scan/addresses
```

- Reports/Evidence:
```
GET /api/v1/wallet-scanner/report/{scan_id}/csv  (community+)
GET /api/v1/wallet-scanner/report/{scan_id}/pdf  (pro+)
GET /api/v1/wallet-scanner/report/{scan_id}/evidence (pro+)
```

- WebSocket Progress (pro+): `wss://<host>/api/v1/ws/scanner/{user_id}`

---

## Trace & Graph (Credits-basiert)

- Trace Start (community+):
```bash
curl -H "Authorization: Bearer $TOKEN" \
     -H 'Content-Type: application/json' \
     -d '{"source_address":"0x...","max_depth":4,"max_nodes":500}' \
     https://<host>/api/v1/trace/start
```
Antwort: `{ trace_id, status, total_nodes, ... }`

- Graph Subgraph (Visualisierung):
```bash
curl -H "Authorization: Bearer $TOKEN" \
     "https://<host>/api/v1/graph/subgraph?address=0x...&depth=3"
```

---

## Alerts v2 (plus+)

- Regel erstellen:
```bash
curl -H "Authorization: Bearer $TOKEN" \
     -H 'Content-Type: application/json' \
     -d '{"rule_id":"r1","name":"HighValue","conditions":[{"field":"value_usd","operator":"gt","value":10000}],"severity":"HIGH"}' \
     https://<host>/api/v1/alerts-v2/rules
```

- Events verarbeiten:
```bash
curl -H "Authorization: Bearer $TOKEN" \
     -H 'Content-Type: application/json' \
     -d '{"event":{"address":"0x...","value_usd":15000,"labels":["mixer"]}}' \
     https://<host>/api/v1/alerts-v2/process-event
```

---

## Fehlercodes & Headers

- 401/403 bei Auth/Plan-Verletzung.
- 429 bei Rate-Limit (Headers: `Retry-After`, `X-RateLimit-*`).
- WS Unauthorized: Code `4401`.

---

## Best Practices

- Serverseitig API-Key nutzen, clientseitig JWT.
- WebSockets stets mit JWT verbinden (oder API-Key in Header) – Query-String nur im Ausnahmefall.
- Idempotency-Key für schreibende Endpunkte setzen (siehe Backend-Konfiguration).
- Backoff bei 429 implementieren.

Viel Erfolg bei der Integration! Für Enterprise/Volumenpreise: Kontaktaufnahme via `/api/v1/support` oder Sales-E-Mail.
