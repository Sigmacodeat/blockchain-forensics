#!/usr/bin/env node
/*
 * Backfill für neue Locales (ms, zh-TW):
 * - Merged fehlende Keys aus en.json bzw. zh-CN.json
 * - Beibehaltung vorhandener Übersetzungen
 */
import fs from 'fs'
import path from 'path'
import url from 'url'

const __filename = url.fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)
const LOCALES_DIR = path.resolve(__dirname, '../src/locales')

const files = {
  ms: {
    base: 'en.json', // ms basiert zunächst auf Englisch
    target: 'ms.json',
  },
  'zh-TW': {
    base: 'zh-CN.json', // zh-TW basiert zunächst auf zh-CN
    target: 'zh-TW.json',
  },
}

function deepMerge(target, source) {
  // Füllt nur fehlende Keys aus source in target
  for (const key of Object.keys(source)) {
    const s = source[key]
    const t = target[key]
    if (t === undefined) {
      target[key] = s
    } else if (typeof s === 'object' && s && typeof t === 'object' && t) {
      deepMerge(t, s)
    }
  }
  return target
}

function readJSON(file) {
  return JSON.parse(fs.readFileSync(file, 'utf8'))
}

function writeJSON(file, obj) {
  fs.writeFileSync(file, JSON.stringify(obj, null, 2) + '\n', 'utf8')
}

function run(localeKey) {
  const { base, target } = files[localeKey]
  const basePath = path.join(LOCALES_DIR, base)
  const targetPath = path.join(LOCALES_DIR, target)
  if (!fs.existsSync(basePath)) throw new Error(`Basisdatei fehlt: ${basePath}`)
  if (!fs.existsSync(targetPath)) throw new Error(`Zieldatei fehlt: ${targetPath}`)

  const baseObj = readJSON(basePath)
  const targetObj = readJSON(targetPath)
  const merged = deepMerge(targetObj, baseObj)
  writeJSON(targetPath, merged)
  console.log(`Backfill abgeschlossen: ${target}`)
}

try {
  run('ms')
  run('zh-TW')
  console.log('Alle Backfills erfolgreich.')
} catch (e) {
  console.error('Fehler beim Backfill:', e.message)
  process.exit(1)
}
