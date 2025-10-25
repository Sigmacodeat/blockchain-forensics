import { Configuration, DefaultApi } from '../../../sdk/typescript'

async function main() {
  const env: any = (globalThis as any).process?.env || {}
  const api = new DefaultApi(
    new Configuration({
      basePath: env.API_URL || 'http://localhost:8000/api/v1',
      headers: {
        Authorization: `Bearer ${env.API_TOKEN || ''}`,
        'X-API-Key': env.API_KEY || '',
      },
    })
  )

  const res = await api.healthzGet()
  // eslint-disable-next-line no-console
  console.log(res)
}

main().catch((e) => {
  // eslint-disable-next-line no-console
  console.error(e)
  ;(globalThis as any).process?.exit?.(1)
})
