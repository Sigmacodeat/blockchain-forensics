/* eslint-disable no-console */
import assert from 'node:assert'

async function send(payload: any, opts?: { deliveryId?: string; url?: string; secret?: string }) {
  const url = opts?.url || process.env.WEBHOOK_URL || 'http://localhost:3062/webhook'
  const secret = opts?.secret || process.env.WEBHOOK_SECRET || 'replace-me'
  const body = typeof payload === 'string' ? payload : JSON.stringify(payload)
  const ts = Math.floor(Date.now() / 1000).toString()
  const enc = new TextEncoder()
  const key = await crypto.subtle.importKey('raw', enc.encode(secret), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign'])
  const sigBuf = await crypto.subtle.sign('HMAC', key, enc.encode(`${ts}.${body}`))
  const sigHex = Buffer.from(new Uint8Array(sigBuf)).toString('hex')
  const delivery = opts?.deliveryId || process.env.DELIVERY_ID || `${Date.now()}-${Math.random().toString(36).slice(2)}`

  const res = await fetch(url, {
    method: 'POST',
    headers: {
      'content-type': 'application/json',
      'x-webhook-delivery': delivery,
      'x-webhook-timestamp': ts,
      'x-webhook-signature-v2': `sha256=${sigHex}`,
    },
    body,
  })
  const text = await res.text()
  return { status: res.status, text, delivery }
}

async function getMetric(expr: string, endpoint: string) {
  const res = await fetch(endpoint)
  const txt = await res.text()
  const lines = txt.split('\n').filter((l) => l.startsWith(expr))
  const last = lines[lines.length - 1]
  if (!last) return 0
  const parts = last.trim().split(' ')
  return Number(parts[parts.length - 1]) || 0
}

async function main() {
  const listenerMetrics = process.env.LISTENER_METRICS || 'http://localhost:3062/metrics'
  const workerMetrics = process.env.WORKER_METRICS || 'http://localhost:9101/metrics'

  const baseInvalidBefore = await getMetric('webhook_invalid_signature_total', listenerMetrics)
  const baseProcessedBefore = await getMetric('webhook_worker_processed_total', workerMetrics)
  const baseDlqBefore = await getMetric('webhook_worker_dlq_total', workerMetrics)

  const ok1 = await send({ event: 'e2e.ok', t: Date.now() })
  assert.strictEqual(ok1.status, 200)

  const replay = await send({ event: 'e2e.ok', t: Date.now() }, { deliveryId: ok1.delivery })
  assert.strictEqual(replay.status, 200)

  const invalid = await send({ foo: 'bar' })
  assert.strictEqual(invalid.status, 200)

  const fail = await send({ event: 'force.fail' })
  assert.strictEqual(fail.status, 200)

  // wait a bit for worker to process
  await new Promise((r) => setTimeout(r, 1500))

  const baseInvalidAfter = await getMetric('webhook_invalid_signature_total', listenerMetrics)
  const baseProcessedAfter = await getMetric('webhook_worker_processed_total', workerMetrics)
  const baseDlqAfter = await getMetric('webhook_worker_dlq_total', workerMetrics)

  console.log('metrics-diff', {
    invalid_delta: baseInvalidAfter - baseInvalidBefore,
    processed_delta: baseProcessedAfter - baseProcessedBefore,
    dlq_delta: baseDlqAfter - baseDlqBefore,
  })
}

main().catch((e) => {
  console.error(e)
  process.exit(1)
})
