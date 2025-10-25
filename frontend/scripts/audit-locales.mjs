#!/usr/bin/env node
import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)
const LOCALES_DIR = path.join(__dirname, '../src/locales')

function readJson(p) { return JSON.parse(fs.readFileSync(p, 'utf8')) }

function flatten(obj, prefix = '') {
  const out = {}
  for (const [k, v] of Object.entries(obj)) {
    const key = prefix ? `${prefix}.${k}` : k
    if (v && typeof v === 'object' && !Array.isArray(v)) Object.assign(out, flatten(v, key))
    else out[key] = v
  }
  return out
}

function detectLanguageSpecificIssues(val, code) {
  const issues = []
  if (typeof val !== 'string') return issues
  // Template vars
  if (/{{.*?}}/.test(val)) issues.push('Contains template variables')
  // External URLs
  if (/https?:\/\/[\w\-\.]+/i.test(val) && !val.includes('sigmacode.io')) issues.push('Contains external URL')
  // Long numbers
  if (/\d{4,}/.test(val)) issues.push('Contains long number')
  return issues
}

const ENGLISH_WORDS = [
  'Loading', 'Save', 'Saved', 'Start', 'Next', 'Previous', 'Close', 'Open', 'Settings', 'Privacy', 'Terms', 'Export',
  'Overview', 'Dashboard', 'Features', 'Cookies', 'Policy', 'Search', 'Help', 'User', 'Error', 'Warning', 'Success',
  'Compliance', 'Security', 'Alert', 'Alerts', 'Graph', 'Network', 'Performance', 'Monitoring', 'Analytics'
]

function isNamespacedPlaceholder(val) {
  if (typeof val !== 'string') return false
  return /^[a-z0-9_.-]+(\.[a-z0-9_.-]+)+$/i.test(val)
}

function looksEnglish(val) {
  if (typeof val !== 'string') return false
  if (/^https?:\/\//i.test(val)) return false
  if (/{{\w+}}/.test(val)) return false
  return ENGLISH_WORDS.some(w => val.includes(w))
}

function main() {
  const files = fs.readdirSync(LOCALES_DIR).filter(f => f.endsWith('.json'))
  const en = readJson(path.join(LOCALES_DIR, 'en.json'))
  const enFlat = flatten(en)
  const totalKeys = Object.keys(enFlat).length

  const report = []
  for (const f of files) {
    const code = f.replace(/\.json$/, '')
    const data = readJson(path.join(LOCALES_DIR, f))
    const flat = flatten(data)

    let sameAsEn = 0
    let namespaced = 0
    let englishish = 0
    let missingTranslations = 0
    let incompleteTranslations = 0
    const potentialIssues = []

    for (const k of Object.keys(enFlat)) {
      const enV = enFlat[k]
      const v = flat[k]
      if (v === undefined || v === null || v === '') { missingTranslations++; continue }
      if (code !== 'en' && typeof v === 'string' && enV && v === enV) {
        sameAsEn++
        if (enV.length > 3) potentialIssues.push(`${k}: Identical to English`)
      }
      if (typeof v === 'string' && enV && enV.length > 10 && v.length < enV.length * 0.3) {
        incompleteTranslations++
        potentialIssues.push(`${k}: Very short vs EN (${v.length}/${enV.length})`)
      }
      if (isNamespacedPlaceholder(v)) namespaced++
      if (looksEnglish(v) && !isNamespacedPlaceholder(v)) englishish++
      const langIssues = detectLanguageSpecificIssues(v, code)
      if (langIssues.length) potentialIssues.push(`${k}: ${langIssues.join(', ')}`)
    }

    const translatedKeys = totalKeys - missingTranslations
    const completeness = ((translatedKeys / totalKeys) * 100).toFixed(1) + '%'

    report.push({
      code,
      totalKeys,
      translatedKeys,
      completeness,
      sameAsEn,
      incompleteTranslations,
      namespaced,
      englishish,
      missingTranslations,
      potentialIssues: potentialIssues.slice(0, 5)
    })
  }

  // Sort non-en first, then en
  report.sort((a, b) => (a.code === 'en') - (b.code === 'en') || a.code.localeCompare(b.code))

  console.log(`\n📊 Translation Quality Report`)
  console.log(`Found ${files.length} language files\n`)
  console.table(report)

  const nonEn = report.filter(r => r.code !== 'en')
  const avgCompleteness = nonEn.reduce((s, r) => s + parseFloat(r.completeness), 0) / (nonEn.length || 1)
  console.log(`\n📈 Summary:`)
  console.log(`• Total languages analyzed: ${nonEn.length}`)
  console.log(`• Average translation completeness: ${avgCompleteness.toFixed(1)}%`)
  console.log(`• Languages with 100% completeness: ${nonEn.filter(r => r.completeness === '100.0%').length}`)
  console.log(`• Languages needing attention (<90%): ${nonEn.filter(r => parseFloat(r.completeness) < 90).length}`)
  const issuesCount = nonEn.filter(r => r.potentialIssues && r.potentialIssues.length > 0).length
  if (issuesCount) console.log(`\n⚠️  Potential issues found in ${issuesCount} languages`)
}

main()
