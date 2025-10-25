#!/usr/bin/env node
import { promises as fs } from 'fs'
import path from 'path'
import url from 'url'

const __filename = url.fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

async function main() {
  const localesDir = path.resolve(__dirname, '../src/locales')
  const files = await fs.readdir(localesDir, { withFileTypes: true })
  const jsonFiles = files
    .filter((ent) => ent.isFile() && ent.name.endsWith('.json'))
    .map((ent) => path.join(localesDir, ent.name))

  // Load EN as base for fallbacks
  const enPath = path.join(localesDir, 'en.json')
  const enRaw = await fs.readFile(enPath, 'utf8')
  const en = JSON.parse(enRaw)
  const base = en?.navigation ?? {}

  const ensureMap = {
    use_cases: base.use_cases ?? 'Use Cases',
    businessplan: base.businessplan ?? 'Businessplan & Funding',
    group_product: base.group_product ?? 'Product',
    group_company: base.group_company ?? 'Company',
    group_preferences: base.group_preferences ?? 'Preferences',
    open_menu: base.open_menu ?? 'Open navigation',
    close_menu: base.close_menu ?? 'Close navigation',
  }

  let updatedFiles = 0
  let totalAdded = 0

  for (const file of jsonFiles) {
    try {
      const raw = await fs.readFile(file, 'utf8')
      const data = JSON.parse(raw)
      if (!data.navigation || typeof data.navigation !== 'object') {
        data.navigation = {}
      }
      let added = 0
      for (const [k, v] of Object.entries(ensureMap)) {
        if (!(k in data.navigation)) {
          data.navigation[k] = v
          added++
        }
      }
      if (added > 0) {
        const pretty = JSON.stringify(data, null, 2) + '\n'
        await fs.writeFile(file, pretty, 'utf8')
        updatedFiles++
        totalAdded += added
        console.log(`Updated ${path.basename(file)} (+${added} keys)`) // eslint-disable-line no-console
      }
    } catch (e) {
      console.error(`Failed ${file}:`, e) // eslint-disable-line no-console
    }
  }

  console.log(`Done. Updated ${updatedFiles} files, inserted ${totalAdded} keys.`) // eslint-disable-line no-console
}

main().catch((e) => {
  console.error(e) // eslint-disable-line no-console
  process.exit(1)
})
