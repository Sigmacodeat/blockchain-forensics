import { createClient } from 'redis'

async function main() {
  const redisUrl = process.env.REDIS_URL
  const stream = process.env.WEBHOOK_STREAM || 'webhook:events'
  const dlq = process.env.WEBHOOK_DLQ || 'webhook:dlq'
  const id = process.env.DLQ_ID || ''
  if (!redisUrl) {
    // eslint-disable-next-line no-console
    console.error('REDIS_URL not set')
    process.exit(1)
  }
  const client = createClient({ url: redisUrl })
  client.on('error', (e) => console.error('Redis error', e))
  await client.connect()
  try {
    let msgId = id
    let msg: { id: string; message: Record<string, string> } | null = null
    if (!msgId) {
      const latest = await client.xRevRange(dlq, '+', '-', { COUNT: 1 })
      if (!latest.length) {
        // eslint-disable-next-line no-console
        console.log('dlq empty')
        return
      }
      msg = latest[0]
      msgId = msg.id
    } else {
      const range = await client.xRange(dlq, msgId, msgId, { COUNT: 1 })
      if (!range.length) {
        // eslint-disable-next-line no-console
        console.error('dlq id not found', msgId)
        return
      }
      msg = range[0]
    }
    const fields = msg!.message
    const re: Record<string, string> = {
      ...fields,
      attempts: '0',
      next_ts: '0',
    }
    await client.xAdd(stream, '*', re)
    // eslint-disable-next-line no-console
    console.log('requeued', { from: dlq, id: msg!.id, to: stream })
  } finally {
    await client.quit()
  }
}

main().catch((e) => {
  // eslint-disable-next-line no-console
  console.error(e)
  process.exit(1)
})
