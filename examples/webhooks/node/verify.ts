import { createHmac, timingSafeEqual } from 'crypto'

function safeEqual(a: string, b: string) {
  const aBuf = Buffer.from(a)
  const bBuf = Buffer.from(b)
  if (aBuf.length !== bBuf.length) return false
  return timingSafeEqual(aBuf, bBuf)
}

export function verifyWebhookV2(rawBody: string, headers: Record<string, string>, secret: string): boolean {
  const ts = headers['x-webhook-timestamp']
  const sigHeader = headers['x-webhook-signature-v2'] || ''
  const sig = sigHeader.replace(/^sha256=/, '')
  if (!ts || !sig) return false
  const now = Math.floor(Date.now() / 1000)
  if (Math.abs(now - Number(ts)) > 300) return false
  const base = `${ts}.${rawBody}`
  const expected = createHmac('sha256', secret).update(base).digest('hex')
  return safeEqual(expected, sig)
}

export function verifyWebhookLegacy(rawBody: string, headers: Record<string, string>, secret: string): boolean {
  const sigHeader = headers['x-webhook-signature'] || ''
  const sig = sigHeader.replace(/^sha256=/, '')
  if (!sig) return false
  const expected = createHmac('sha256', secret).update(rawBody).digest('hex')
  return safeEqual(expected, sig)
}
