import { createClient } from 'redis'

async function main() {
  const redisUrl = process.env.REDIS_URL
  const dlq = process.env.WEBHOOK_DLQ || 'webhook:dlq'
  const count = Number(process.env.DLQ_COUNT || 10)
  if (!redisUrl) {
    // eslint-disable-next-line no-console
    console.error('REDIS_URL not set')
    process.exit(1)
  }
  const client = createClient({ url: redisUrl })
  client.on('error', (e) => console.error('Redis error', e))
  await client.connect()
  try {
    const len = await client.xLen(dlq)
    // eslint-disable-next-line no-console
    console.log('dlq length', len)
    const items = await client.xRevRange(dlq, '+', '-', { COUNT: count })
    for (const it of items) {
      // eslint-disable-next-line no-console
      console.log('dlq item', it.id, it.message)
    }
  } finally {
    await client.quit()
  }
}

main().catch((e) => {
  // eslint-disable-next-line no-console
  console.error(e)
  process.exit(1)
})
