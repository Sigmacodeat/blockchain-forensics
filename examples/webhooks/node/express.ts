import express from 'express'
import type { Server } from 'http'
import { createClient } from 'redis'
import rateLimit from 'express-rate-limit'
import client from 'prom-client'
import { verifyWebhookV2, verifyWebhookLegacy } from './verify'

const app = express()
if (process.env.TRUST_PROXY === '1') app.set('trust proxy', 1)

const windowMs = Number(process.env.RATE_WINDOW_MS || 60_000)
const max = Number(process.env.RATE_MAX || 120)
const limiter = rateLimit({ windowMs, max, standardHeaders: true, legacyHeaders: false })

const allow = (process.env.IP_ALLOWLIST || '')
  .split(',')
  .map((s) => s.trim())
  .filter(Boolean)

function ipAllowed(req: express.Request) {
  if (!allow.length) return true
  const ip = req.ip || ''
  const norm = ip.replace('::ffff:', '')
  return allow.includes(ip) || allow.includes(norm)
}

client.collectDefaultMetrics()
const requestsTotal = new client.Counter({ name: 'webhook_requests_total', help: 'Total webhook requests' })
const invalidSigTotal = new client.Counter({ name: 'webhook_invalid_signature_total', help: 'Invalid signature' })
const replayTotal = new client.Counter({ name: 'webhook_replay_total', help: 'Replay hits' })
const enqueueTotal = new client.Counter({ name: 'webhook_enqueue_total', help: 'Enqueued events' })
const reqDuration = new client.Histogram({ name: 'webhook_request_duration_seconds', help: 'Duration of webhook handler', buckets: [0.01,0.05,0.1,0.25,0.5,1,2,5] })

app.get('/metrics', async (_req, res) => {
  res.set('Content-Type', client.register.contentType)
  res.end(await client.register.metrics())
})

// Wichtig: unveränderten Roh-Body verwenden, damit die Signaturprüfung exakt ist
app.post('/webhook', limiter, express.raw({ type: 'application/json', limit: '256kb' }), async (req, res) => {
  const endTimer = reqDuration.startTimer()
  requestsTotal.inc()
  if (!ipAllowed(req)) return res.status(403).send('forbidden')
  const raw = Buffer.isBuffer(req.body) ? req.body.toString('utf8') : ''
  const headers = Object.fromEntries(
    Object.entries(req.headers).map(([k, v]) => [k.toLowerCase(), Array.isArray(v) ? v[0] : String(v)])
  ) as Record<string, string>

  const contentType = headers['content-type'] || ''
  if (!contentType.includes('application/json')) return res.status(400).send('invalid content-type')

  const secretEnv = (process.env.WEBHOOK_SECRETS || '').split(',').map((s) => s.trim()).filter(Boolean)
  const fallback = process.env.WEBHOOK_SECRET || 'replace-me'
  const secrets = secretEnv.length ? secretEnv : [fallback]

  // Signaturprüfung (V2 bevorzugt, Legacy als Fallback)
  const ok = secrets.some((s) => verifyWebhookV2(raw, headers, s) || verifyWebhookLegacy(raw, headers, s))
  if (!ok) {
    invalidSigTotal.inc()
    endTimer()
    return res.status(400).send('invalid signature')
  }

  // Einfache Idempotenz/Replay-Protection (24h) – In-Memory Beispiel
  const deliveryId = headers['x-webhook-delivery'] || headers['idempotency-key']
  if (!deliveryId) return res.status(400).send('missing delivery id')
  if (deliveryId) {
    if (redisClient) {
      try {
        const key = `wh:${deliveryId}`
        const set = await redisClient.set(key, '1', { NX: true, EX: 24 * 3600 })
        if (set === null) return res.status(200).send('ok')
      } catch {}
    } else {
      const now = Date.now()
      for (const [k, exp] of idempotencyStore.entries()) {
        if (exp < now) idempotencyStore.delete(k)
      }
      if (idempotencyStore.has(deliveryId)) {
        replayTotal.inc()
        endTimer()
        return res.status(200).send('ok')
      }
      idempotencyStore.set(deliveryId, now + 24 * 3600 * 1000)
    }
  }

  const stream = process.env.WEBHOOK_STREAM || 'webhook:events'
  const tsNow = Math.floor(Date.now() / 1000).toString()
  if (redisClient) {
    try {
      await redisClient.xAdd(stream, '*', {
        id: deliveryId,
        ts: tsNow,
        headers: JSON.stringify(headers),
        payload: raw,
      })
      enqueueTotal.inc()
    } catch {}
  }
  const r = res.status(200).send('ok')
  endTimer()
  return r
})

// In-Memory Idempotenz-Store (Key -> expiresAt)
const idempotencyStore: Map<string, number> = new Map()
function cleanupIdem(now: number) {
  for (const [k, exp] of idempotencyStore.entries()) {
    if (exp < now) idempotencyStore.delete(k)
  }
}
const redisUrl = process.env.REDIS_URL
const redisClient = redisUrl ? createClient({ url: redisUrl }) : null
if (redisClient) {
  redisClient.on('error', () => {})
  redisClient.connect().catch(() => {})
}

const port = process.env.PORT || 3001
const server = app.listen(port, () => {
  // eslint-disable-next-line no-console
  console.log(`Webhook listener on http://localhost:${port}`)
})

let shuttingDown = false
async function shutdown() {
  // eslint-disable-next-line no-console
  console.log('Shutting down...')
  try {
    if (redisClient) {
      await redisClient.quit().catch(() => {})
    }
  } catch {}
  try {
    await new Promise<void>((resolve) => server.close(() => resolve()))
  } catch {}
  process.exit(0)
}

process.on('SIGINT', shutdown)
process.on('SIGTERM', shutdown)
