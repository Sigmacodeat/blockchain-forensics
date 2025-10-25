#!/usr/bin/env node
import fs from 'fs'
import path from 'path'
import process from 'process'

const root = process.cwd()
const localesDir = path.resolve(root, 'frontend', 'src', 'locales')

function readJson(fp) {
  return JSON.parse(fs.readFileSync(fp, 'utf8'))
}

function walk(dir) {
  const res = []
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    if (e.name.startsWith('.')) continue
    const p = path.join(dir, e.name)
    if (e.isDirectory()) res.push(...walk(p))
    else if (/[.][jt]sx?$/.test(e.name)) res.push(p)
  }
  return res
}

// Regex patterns for i18n key usage
const usagePatterns = [
  /\bt\(\s*['"]([^'\"]+)['"]/g,
  /\bi18n\.t\(\s*['"]([^'\"]+)['"]/g,
  /\bi18next\.t\(\s*['"]([^'\"]+)['"]/g,
  /i18nKey\s*=\s*['"]([^'\"]+)['"]/g,
]

function extractUsedKeys(srcRoot) {
  const used = new Set()
  const files = walk(srcRoot)
  for (const f of files) {
    const txt = fs.readFileSync(f, 'utf8')
    for (const re of usagePatterns) {
      let m
      while ((m = re.exec(txt)) !== null) if (m[1]) used.add(m[1])
    }
  }
  return used
}

function flatten(obj, prefix = '', out = {}) {
  for (const [k, v] of Object.entries(obj)) {
    const key = prefix ? `${prefix}.${k}` : k
    if (v && typeof v === 'object' && !Array.isArray(v)) {
      flatten(v, key, out)
    } else {
      out[key] = v
    }
  }
  return out
}

function listLanguages() {
  return fs
    .readdirSync(localesDir)
    .filter((f) => f.endsWith('.json'))
    .map((f) => f.replace(/\.json$/, ''))
    .sort()
}

function extractPlaceholders(text) {
  if (typeof text !== 'string') return []
  const re = /\{\{\s*([\w.]+)\s*\}\}/g
  const out = new Set()
  let m
  while ((m = re.exec(text)) !== null) out.add(m[1])
  return [...out].sort()
}

function main() {
  const args = process.argv.slice(2)
  const baseLang = (args.find((a) => a === '--base') ? args[args.indexOf('--base') + 1] : 'en')
    .replace(/\.json$/, '')
  const fail = args.includes('--fail') || args.includes('--fail-on-issues')
  const usedOnly = args.includes('--used-only')

  const basePath = path.join(localesDir, `${baseLang}.json`)
  if (!fs.existsSync(basePath)) {
    console.error(`Base locale not found: ${basePath}`)
    process.exit(1)
  }

  const baseFlat = flatten(readJson(basePath))
  const langs = listLanguages()

  let usedKeys = null
  if (usedOnly) {
    const srcRoot = path.resolve(root, 'frontend', 'src')
    usedKeys = extractUsedKeys(srcRoot)
  }

  const report = {
    timestamp: new Date().toISOString(),
    base: baseLang,
    localesDir,
    languages: langs,
    issues: {},
    totals: { placeholders: 0, missingTokens: 0 }
  }

  for (const lang of langs) {
    const fp = path.join(localesDir, `${lang}.json`)
    const flat = flatten(readJson(fp))
    const placeholders = []
    const missingTokens = []

    for (const [k, v] of Object.entries(flat)) {
      if (usedOnly && usedKeys && !usedKeys.has(k)) continue
      if (typeof v === 'string' && v.trim() === k) {
        placeholders.push(k)
      }
    }

    // interpolation token parity vs base
    for (const [k, baseVal] of Object.entries(baseFlat)) {
      if (usedOnly && usedKeys && !usedKeys.has(k)) continue
      if (typeof baseVal !== 'string') continue
      const baseTokens = extractPlaceholders(baseVal)
      if (baseTokens.length === 0) continue
      const tgtVal = flat[k]
      if (typeof tgtVal !== 'string') {
        missingTokens.push({ key: k, missing: baseTokens })
        continue
      }
      const tgtTokens = extractPlaceholders(tgtVal)
      const missing = baseTokens.filter((t) => !tgtTokens.includes(t))
      if (missing.length) missingTokens.push({ key: k, missing })
    }

    report.issues[lang] = {
      placeholdersCount: placeholders.length,
      placeholders: placeholders.slice(0, 50),
      missingTokensCount: missingTokens.length,
      missingTokens: missingTokens.slice(0, 50)
    }
    report.totals.placeholders += placeholders.length
    report.totals.missingTokens += missingTokens.length
  }

  const outPath = path.join(root, 'I18N_QUALITY_REPORT.json')
  fs.writeFileSync(outPath, JSON.stringify(report, null, 2))

  // Console summary
  console.log('i18n-quality summary')
  console.log('Base:', baseLang)
  console.log('Locales:', langs.length)
  if (usedOnly) console.log('Mode: used-only')
  const rows = Object.entries(report.issues)
    .sort((a, b) => a[0].localeCompare(b[0]))
    .map(([lang, s]) => `${lang}\t${s.placeholdersCount}\t${s.missingTokensCount}`)
  console.log('lang\tplaceholders\tmissing_tokens')
  for (const r of rows) console.log(r)

  const hasIssues = report.totals.placeholders > 0 || report.totals.missingTokens > 0
  if (fail && hasIssues) {
    console.error('\n❌ i18n-quality: Issues detected. See I18N_QUALITY_REPORT.json')
    process.exit(2)
  } else {
    console.log('\n✅ i18n-quality: Done', hasIssues ? '(issues found)' : '(no issues)')
  }
}

main()
