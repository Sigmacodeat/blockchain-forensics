import { createClient } from 'redis'
import Ajv from 'ajv'
import http from 'http'
import promClient from 'prom-client'

function sleep(ms: number) {
  return new Promise((r) => setTimeout(r, ms))
}

async function main() {
  const redisUrl = process.env.REDIS_URL
  const stream = process.env.WEBHOOK_STREAM || 'webhook:events'
  const dlq = process.env.WEBHOOK_DLQ || 'webhook:dlq'
  const group = process.env.WEBHOOK_GROUP || 'webhook-workers'
  const consumer = process.env.WEBHOOK_CONSUMER || `c-${Math.random().toString(36).slice(2)}`
  const maxAttempts = Number(process.env.MAX_ATTEMPTS || 3)
  const backoffBase = Number(process.env.BACKOFF_BASE_SEC || 5)
  const dead = process.env.WEBHOOK_DLQ || 'webhook:dead'
  const maxRetries = Number(process.env.WEBHOOK_MAX_RETRIES || 5)
  const retryIdleMs = Number(process.env.WEBHOOK_RETRY_IDLE_MS || 60_000)
  const pollCount = Number(process.env.WEBHOOK_POLL_COUNT || 10)
  const blockMs = Number(process.env.WEBHOOK_BLOCK_MS || 5000)

  if (!redisUrl) {
    // eslint-disable-next-line no-console
    console.error('REDIS_URL not set; worker exiting')
    process.exit(0)
  }

  const client = createClient({ url: redisUrl })
  client.on('error', (e) => {
    // eslint-disable-next-line no-console
    console.error('Redis error', e)
  })
  await client.connect()

  const ajv = new Ajv({ removeAdditional: 'failing' })
  const validate = ajv.compile({
    type: 'object',
    properties: { event: { type: 'string', minLength: 1 } },
    required: ['event'],
    additionalProperties: true,
  })

  const retryKey = (id: string) => `wh:retry:${id}`

  promClient.collectDefaultMetrics()
  const processedTotal = new promClient.Counter({ name: 'webhook_worker_processed_total', help: 'Processed messages' })
  const retryTotal = new promClient.Counter({ name: 'webhook_worker_retry_total', help: 'Retries' })
  const dlqTotal = new promClient.Counter({ name: 'webhook_worker_dlq_total', help: 'DLQ placements' })
  const deferredTotal = new promClient.Counter({ name: 'webhook_worker_deferred_total', help: 'Deferred messages' })

  const metricsPort = Number(process.env.METRICS_PORT || 9100)
  const metricsServer = http.createServer(async (req, res) => {
    if (req.url === '/metrics') {
      res.setHeader('Content-Type', promClient.register.contentType)
      res.end(await promClient.register.metrics())
      return
    }
    res.statusCode = 404
    res.end('not found')
  })
  metricsServer.listen(metricsPort)

  try {
    await client.xGroupCreate(stream, group, '0', { MKSTREAM: true })
  } catch {}

  let running = true
  async function shutdown() {
    running = false
    try {
      await client.quit()
    } catch {}
    process.exit(0)
  }
  process.on('SIGINT', shutdown)
  process.on('SIGTERM', shutdown)

  async function processMessage(id: string, fields: Record<string, string>) {
    const now = Math.floor(Date.now() / 1000)
    const nextTs = fields.next_ts ? Number(fields.next_ts) : 0
    if (nextTs && now < nextTs) {
      await client.xAdd(stream, '*', { ...fields })
      await client.xAck(stream, group, id)
      deferredTotal.inc()
      // eslint-disable-next-line no-console
      console.log('deferred', { id, until: nextTs })
      return
    }
    try {
      const payload = fields.payload || ''
      const headers = fields.headers ? JSON.parse(fields.headers) : {}
      const data = payload ? JSON.parse(payload) : {}
      if (!validate(data)) {
        await client.xAdd(dlq, '*', { reason: 'invalid_event', payload, headers: fields.headers || '' })
        await client.xAck(stream, group, id)
        dlqTotal.inc()
        // eslint-disable-next-line no-console
        console.log('dlq', { id, reason: 'invalid_event', errors: JSON.stringify(validate.errors || []) })
        return
      }
      if (data.event === 'force.fail') {
        throw new Error('forced_failure')
      }
      processedTotal.inc()
      // eslint-disable-next-line no-console
      console.log('processed', { id, event: data.event })
      await client.xAck(stream, group, id)
    } catch (e) {
      const attempts = Number(fields.attempts || '0')
      if (attempts < maxAttempts) {
        const delay = Math.floor(backoffBase * Math.pow(2, attempts))
        const re = { ...fields, attempts: String(attempts + 1), next_ts: String(now + delay) }
        await client.xAdd(stream, '*', re)
        await client.xAck(stream, group, id)
        retryTotal.inc()
        // eslint-disable-next-line no-console
        console.log('retry', { id, attempt: attempts + 1, delay })
      } else {
        await client.xAdd(dlq, '*', { reason: 'max_attempts', payload: fields.payload || '', headers: fields.headers || '' })
        await client.xAck(stream, group, id)
        dlqTotal.inc()
        // eslint-disable-next-line no-console
        console.log('dlq', { id, reason: 'max_attempts' })
      }
    }
  }

  async function handleError(id: string, fields: Record<string, string>, err: unknown) {
    const n = await client.incr(retryKey(id))
    await client.expire(retryKey(id), 24 * 3600)
    // eslint-disable-next-line no-console
    console.error('error processing', id, 'attempt', n, err)
    if (n > maxRetries) {
      // move to DLQ and ack
      await client.xAdd(dead, '*', {
        id,
        ts: Math.floor(Date.now() / 1000).toString(),
        payload: fields.payload || '',
        headers: fields.headers || '{}',
        error: (err as Error)?.message ?? 'error',
      })
      await client.xAck(stream, group, id)
      await client.del(retryKey(id))
      return
    }
    // leave pending to retry later via auto-claim
  }

  async function claimPendingLoop() {
    while (running) {
      try {
        const res = await client.xAutoClaim(stream, group, consumer, retryIdleMs, '0-0', {
          COUNT: pollCount,
        })
        const messages = res?.messages || []
        for (const m of messages) {
          if (!m || !m.id) continue
          const mid = m.id
          const mfields = (m.message ?? {}) as Record<string, string>
          try {
            await processMessage(mid, mfields)
            await client.xAck(stream, group, mid)
            await client.del(retryKey(mid))
          } catch (e) {
            await handleError(mid, mfields, e)
          }
        }
      } catch {}
      await sleep(1000)
    }
  }

  // fire and forget background reclaim loop
  void claimPendingLoop()

  // main consumption loop
  while (running) {
    try {
      const resp = await client.xReadGroup(group, consumer, [{ key: stream, id: '>' }], {
        COUNT: pollCount,
        BLOCK: blockMs,
      })
      if (!resp) continue
      for (const r of resp) {
        for (const m of r.messages) {
          if (!m || !m.id) continue
          const mid = m.id
          const mfields = (m.message ?? {}) as Record<string, string>
          try {
            await processMessage(mid, mfields)
            await client.xAck(stream, group, mid)
            await client.del(retryKey(mid))
          } catch (e) {
            await handleError(mid, mfields, e)
          }
        }
      }
    } catch {
      await sleep(500)
    }
  }

  try {
    await client.quit()
  } catch {}
}

main().catch((e) => {
  // eslint-disable-next-line no-console
  console.error(e)
  process.exit(1)
})
