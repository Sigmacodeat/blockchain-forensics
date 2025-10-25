#!/usr/bin/env node
import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)
const LOCALES_DIR = path.join(__dirname, '../src/locales')

const REQUIRED = [
  'banner_aria',
  'title',
  'title_short',
  'description',
  'privacy_link',
  'terms_link',
  'imprint_link',
  'only_necessary',
  'accept_all',
  'preferences',
  'save_preferences',
  'manage',
  'analytics_title',
  'analytics_desc',
  'marketing_title',
  'marketing_desc',
]

function loadJSON(p) {
  return JSON.parse(fs.readFileSync(p, 'utf8'))
}
function saveJSON(p, obj) {
  fs.writeFileSync(p, JSON.stringify(obj, null, 2) + '\n')
}

const en = loadJSON(path.join(LOCALES_DIR, 'en.json'))
if (!en.cookie) {
  console.error('en.json has no cookie section; aborting')
  process.exit(1)
}

const enCookie = en.cookie

const files = fs.readdirSync(LOCALES_DIR).filter(f => f.endsWith('.json'))
let updated = 0
for (const f of files) {
  const fp = path.join(LOCALES_DIR, f)
  const data = loadJSON(fp)
  data.cookie = data.cookie || {}
  let changed = false
  for (const key of REQUIRED) {
    if (!(key in data.cookie)) {
      data.cookie[key] = enCookie[key]
      changed = true
    }
  }
  if (changed) {
    saveJSON(fp, data)
    updated++
    console.log(`Updated ${f}`)
  }
}

console.log(`Done. Updated ${updated} locale files.`)
