# Webhooks – Sicherheit, Signaturen und Idempotenz

Dieser Leitfaden erklärt, wie eingehende Webhooks aus der Blockchain-Forensics-Plattform sicher verifiziert und idempotent verarbeitet werden.

## Ereignisse

- `alert.triggered`
- `risk.high_risk_detected`
- `trace.completed`
- `webhook.test`

Beispiel-Payload (JSON):
```json
{
  "event": "alert.triggered",
  "timestamp": "2025-10-16T13:00:00Z",
  "delivery_id": "d3f3d5b0-3a6b-4bbf-8c08-3d11b9a6f5a1",
  "data": { "id": "...", "severity": "high" }
}
```

## Header

- `X-Webhook-Event`: Ereignistyp
- `X-Webhook-Delivery`: Eindeutige Delivery-ID (auch als `Idempotency-Key` gesetzt)
- `Idempotency-Key`: Idempotenzschlüssel (entspricht Delivery-ID)
- `X-Webhook-Signature`: `sha256=<hex>` (Legacy: HMAC über Body)
- `X-Webhook-Timestamp`: UNIX-Sekunden (String)
- `X-Webhook-Signature-V2`: `sha256=<hex>` (HMAC über `${timestamp}.${payload}`)

## Replay-Schutz und Ablauf

- Empfohlene maximale **Uhrzeitabweichung**: ±300 Sekunden.
- **Ablage** der `delivery_id` (z. B. Redis) für 24h zur Deduplizierung.

## Verifikation – Node.js (TypeScript)

```ts
import crypto from 'node:crypto'

function safeEqual(a: string, b: string) {
  const aBuf = Buffer.from(a)
  const bBuf = Buffer.from(b)
  if (aBuf.length !== bBuf.length) return false
  return crypto.timingSafeEqual(aBuf, bBuf)
}

export function verifyWebhook(reqBody: string, headers: Record<string,string>, secret: string) {
  const ts = headers['x-webhook-timestamp']
  const sigV2 = headers['x-webhook-signature-v2']?.replace(/^sha256=/, '')
  if (!ts || !sigV2) return false

  // Replay window
  const now = Math.floor(Date.now()/1000)
  if (Math.abs(now - Number(ts)) > 300) return false

  const base = `${ts}.${reqBody}`
  const expected = crypto.createHmac('sha256', secret).update(base).digest('hex')
  return safeEqual(expected, sigV2)
}
```

### Quickstart – Express Listener

Siehe `examples/webhooks/node/express.ts`:

```ts
import express from 'express'
import { verifyWebhookV2, verifyWebhookLegacy } from './verify'

const app = express()
app.use(express.text({ type: '*/*' })) // Roh-Body unverändert behalten

const WEBHOOK_SECRET = process.env.WEBHOOK_SECRET || 'replace-me'

app.post('/webhook', (req, res) => {
  const raw = req.body as string
  const headers = Object.fromEntries(
    Object.entries(req.headers).map(([k, v]) => [k.toLowerCase(), Array.isArray(v) ? v[0] : String(v)])
  )
  const ok = verifyWebhookV2(raw, headers, WEBHOOK_SECRET) || verifyWebhookLegacy(raw, headers, WEBHOOK_SECRET)
  if (!ok) return res.status(400).send('invalid signature')
  return res.status(200).send('ok')
})
```

Hinweis: Kein JSON-Parser vor der Verifikation verwenden (sonst ändert sich der Body!).

## Verifikation – Python

```python
import hmac, hashlib, time

def verify_webhook(body: bytes, headers: dict, secret: str) -> bool:
    ts = headers.get('x-webhook-timestamp')
    sigv2 = (headers.get('x-webhook-signature-v2') or '').replace('sha256=', '')
    if not ts or not sigv2:
        return False
    try:
        ts_int = int(ts)
    except Exception:
        return False
    if abs(int(time.time()) - ts_int) > 300:
        return False
    base = f"{ts}.{body.decode('utf-8')}".encode('utf-8')
    expected = hmac.new(secret.encode('utf-8'), base, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, sigv2)
```

### Quickstart – Flask Listener

Siehe `examples/webhooks/python/flask_app.py`:

```python
from flask import Flask, request, Response
from .verify import verify_webhook_v2, verify_webhook_legacy
import os

app = Flask(__name__)
WEBHOOK_SECRET = os.getenv('WEBHOOK_SECRET', 'replace-me')

def normalize_headers(h):
    return {k.lower(): v for k, v in h.items()}

@app.post('/webhook')
def webhook():
    raw = request.get_data()  # bytes
    headers = normalize_headers(request.headers)
    ok = verify_webhook_v2(raw, headers, WEBHOOK_SECRET) or verify_webhook_legacy(raw, headers, WEBHOOK_SECRET)
    if not ok:
        return Response('invalid signature', status=400)
    return Response('ok', status=200)
```

## Idempotente Verarbeitung

1. `delivery_id` aus `X-Webhook-Delivery`/`Idempotency-Key` lesen.
2. In einem **idempotency store** (Redis/DB) mit TTL (24h) transaktional markieren.
3. Wenn bereits vorhanden: 200 OK zurückgeben, ohne Nebenwirkungen zu wiederholen.

## empfohlene Antworten

- `2xx` für akzeptierte/verarbeitete Events (auch bei Idempotenz-Treffer)
- `4xx` bei dauerhaften Fehlern (Validation)
- `5xx` bei temporären Fehlern (Sender führt Retries mit Backoff aus)

## Sicherheitsempfehlungen

- Secret pro Webhook-Endpunkt (wechselbar/rotierbar)
- Eingehende Größe limitieren (z. B. 256KB)
- Strict TLS erzwingen
- Logging ohne Secrets/Signaturen (PII-Minimierung)
- Zeitfenster strikt prüfen (±300s) und `delivery_id` idempotent speichern

