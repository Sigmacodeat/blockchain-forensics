#!/usr/bin/env node
import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)
const LOCALES_DIR = path.join(__dirname, '../src/locales')

let ok = 0, failed = 0
for (const f of fs.readdirSync(LOCALES_DIR)) {
  if (!f.endsWith('.json')) continue
  const p = path.join(LOCALES_DIR, f)
  try {
    // Read as UTF-8 text, parse, and re-serialize to normalize whitespace/encoding
    const txt = fs.readFileSync(p, 'utf8')
    const obj = JSON.parse(txt)
    fs.writeFileSync(p, JSON.stringify(obj, null, 2) + '\n', { encoding: 'utf8' })
    ok++
    console.log('normalized', f)
  } catch (e) {
    failed++
    console.error('skip', f, e.message)
  }
}
console.log(`Done. normalized=${ok}, failed=${failed}`)
