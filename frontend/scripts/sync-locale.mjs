#!/usr/bin/env node
import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)
const LOCALES_DIR = path.join(__dirname, '../src/locales')

function readJson(p) {
  return JSON.parse(fs.readFileSync(p, 'utf8'))
}

function writeJson(p, obj) {
  fs.writeFileSync(p, JSON.stringify(obj, null, 2) + '\n', 'utf8')
}

function deepMergeKeys(base, target) {
  if (Array.isArray(base)) return target ?? base
  if (typeof base !== 'object' || base === null) return target ?? base
  const out = { ...(typeof target === 'object' && target ? target : {}) }
  for (const k of Object.keys(base)) {
    const b = base[k]
    const t = target ? target[k] : undefined
    out[k] = deepMergeKeys(b, t)
  }
  return out
}

function main() {
  const src = process.argv[2] || 'en'
  const dst = process.argv[3] || 'he'
  const srcPath = path.join(LOCALES_DIR, `${src}.json`)
  const dstPath = path.join(LOCALES_DIR, `${dst}.json`)
  if (!fs.existsSync(srcPath)) {
    console.error('Missing source locale:', srcPath)
    process.exit(1)
  }
  if (!fs.existsSync(dstPath)) {
    console.error('Missing target locale:', dstPath)
    process.exit(1)
  }
  const base = readJson(srcPath)
  const target = readJson(dstPath)
  const merged = deepMergeKeys(base, target)
  writeJson(dstPath, merged)
  console.log(`Synced keys from ${src}.json -> ${dst}.json`)
}

main()
