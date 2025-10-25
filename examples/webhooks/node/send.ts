import { createHmac } from 'crypto'

async function main() {
  const url = process.env.WEBHOOK_URL || 'http://localhost:3001/webhook'
  const secret = process.env.WEBHOOK_SECRET || 'replace-me'
  const payload = process.env.PAYLOAD || JSON.stringify({ event: 'webhook.test', timestamp: new Date().toISOString() })
  const deliveryId = process.env.DELIVERY_ID || `${Date.now()}-${Math.random().toString(36).slice(2)}`

  const ts = Math.floor(Date.now() / 1000).toString()
  const base = `${ts}.${payload}`
  const sig = createHmac('sha256', secret).update(base).digest('hex')

  const res = await fetch(url, {
    method: 'POST',
    headers: {
      'content-type': 'application/json',
      'x-webhook-delivery': deliveryId,
      'x-webhook-timestamp': ts,
      'x-webhook-signature-v2': `sha256=${sig}`,
    },
    body: payload,
  })
  const text = await res.text()
  // eslint-disable-next-line no-console
  console.log(res.status, text)
}

main().catch((e) => {
  // eslint-disable-next-line no-console
  console.error(e)
  process.exit(1)
})
