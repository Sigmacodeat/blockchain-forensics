#!/usr/bin/env node
/**
 * Findet fehlende Übersetzungen in allen Sprachdateien
 * Sucht nach Keys, deren Wert dem Key-Namen entspricht (z.B. "agent.cancel": "agent.cancel")
 */

import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

const LOCALES_DIR = path.join(__dirname, '../src/locales')

// Aktive Sprach-Allowlist (entspricht PublicLayout Allowlist)
const DEFAULT_ALLOWLIST = [
  'en', 'de', 'fr', 'es', 'it', 'pt', 'nl', 'sv', 'fi', 'pl', 'da',
  'ko', 'ja', 'zh-CN', 'tr', 'ru', 'uk'
]

// Optionales Override via Umgebungsvariable I18N_LANGS="en,de,fr"
const LANGUAGES = (process.env.I18N_LANGS
  ? process.env.I18N_LANGS.split(',').map(s => s.trim()).filter(Boolean)
  : DEFAULT_ALLOWLIST)

// Referenz: Englisch
const enFile = path.join(LOCALES_DIR, 'en.json')
const enData = JSON.parse(fs.readFileSync(enFile, 'utf8'))

// Funktion: Flatten nested object zu dot-notation
function flattenObject(obj, prefix = '') {
  let result = {}
  
  for (const [key, value] of Object.entries(obj)) {
    const newKey = prefix ? `${prefix}.${key}` : key
    
    if (value && typeof value === 'object' && !Array.isArray(value)) {
      Object.assign(result, flattenObject(value, newKey))
    } else {
      result[newKey] = value
    }
  }
  
  return result
}

// Alle Keys aus EN
const enFlat = flattenObject(enData)
const allKeys = Object.keys(enFlat)

console.log(`\n🔍 Überprüfe ${LANGUAGES.length} Sprachen mit ${allKeys.length} Keys...\n`)

const report = []
let totalMissing = 0
let totalUntranslated = 0

// Bestimmte Keys/Pfade sind optional und sollen nicht als Fehler zählen
// Unterstützt exakte Matches und Prefix-Matches (dot-notation)
const OPTIONAL_KEYS = new Set([
  'cookie.all_optional_title',
  'cookie.all_optional_desc',
])
const OPTIONAL_PREFIXES = []

for (const lang of LANGUAGES) {
  const file = path.join(LOCALES_DIR, `${lang}.json`)
  
  if (!fs.existsSync(file)) {
    console.log(`❌ ${lang}.json fehlt!`)
    continue
  }
  
  const data = JSON.parse(fs.readFileSync(file, 'utf8'))
  const flat = flattenObject(data)
  
  const missing = []
  const untranslated = []
  
  for (const key of allKeys) {
    // Optional keys handling
    const isOptional = OPTIONAL_KEYS.has(key) || OPTIONAL_PREFIXES.some(p => key.startsWith(p))
    if (isOptional) continue
    // Key fehlt komplett
    if (!(key in flat)) {
      missing.push(key)
    }
    // Key existiert, aber Wert = Key-Name (nicht übersetzt)
    else if (flat[key] === key) {
      untranslated.push(key)
    }
  }
  
  const failOnUntranslated = process.env.FAIL_ON_UNTRANSLATED === '1'
  const total = missing.length + (failOnUntranslated ? untranslated.length : 0)
  totalMissing += missing.length
  totalUntranslated += untranslated.length
  
  if (missing.length > 0 || (failOnUntranslated && untranslated.length > 0)) {
    report.push({
      lang,
      missing: missing.length,
      untranslated: untranslated.length,
      total,
      missingKeys: missing,
      untranslatedKeys: untranslated
    })
  }
}

// Sortiere nach Anzahl Probleme
report.sort((a, b) => b.total - a.total)

// Ausgabe
console.log('═══════════════════════════════════════════════════════════════')
console.log('                  ÜBERSETZUNGS-REPORT')
console.log('═══════════════════════════════════════════════════════════════\n')

if (report.length === 0) {
  console.log('✅ Perfekt! Alle Sprachen sind vollständig übersetzt.\n')
} else {
  console.log(`🔴 ${report.length} Sprachen mit Problemen gefunden:\n`)
  
  console.log('┌──────┬──────────┬──────────────┬─────────┐')
  console.log('│ Lang │ Fehlend  │ Unübersetzt  │ Gesamt  │')
  console.log('├──────┼──────────┼──────────────┼─────────┤')
  
  for (const r of report) {
    const langPad = r.lang.padEnd(4)
    const missingPad = String(r.missing).padStart(8)
    const untranslatedPad = String(r.untranslated).padStart(12)
    const totalPad = String(r.total).padStart(7)
    console.log(`│ ${langPad} │ ${missingPad} │ ${untranslatedPad} │ ${totalPad} │`)
  }
  
  console.log('└──────┴──────────┴──────────────┴─────────┘\n')
  
  console.log(`📊 GESAMT: ${totalMissing} fehlende Keys${process.env.FAIL_ON_UNTRANSLATED==='1' ? ' (und ' + totalUntranslated + ' unübersetzte)' : ''} über ${report.length} Sprachen\n`)
  
  // Top 5 problematischste Sprachen
  console.log('🔴 TOP 5 PROBLEMATISCHE SPRACHEN:\n')
  for (let i = 0; i < Math.min(5, report.length); i++) {
    const r = report[i]
    console.log(`${i + 1}. ${r.lang}: ${r.total} Probleme`)
    
    if (r.untranslated.length > 0) {
      console.log(`   Unübersetzt (erste 5):`)
      for (const key of r.untranslatedKeys.slice(0, 5)) {
        console.log(`   - ${key}`)
      }
    }
    console.log('')
  }
  
  // Häufigste fehlende Keys (über alle Sprachen)
  const keyFrequency = {}
  for (const r of report) {
    const keys = process.env.FAIL_ON_UNTRANSLATED==='1' ? [...r.missingKeys, ...r.untranslatedKeys] : r.missingKeys
    for (const key of keys) {
      keyFrequency[key] = (keyFrequency[key] || 0) + 1
    }
  }
  
  const topMissing = Object.entries(keyFrequency)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10)
  
  console.log('🔥 TOP 10 FEHLENDE KEYS (über alle Sprachen):\n')
  for (const [key, count] of topMissing) {
    console.log(`${count}x - ${key}`)
  }
  console.log('')
}

// Schreibe detaillierten Report
const reportFile = path.join(__dirname, '../i18n-missing-keys.json')
fs.writeFileSync(reportFile, JSON.stringify(report, null, 2))
console.log(`📝 Detaillierter Report: ${reportFile}\n`)

console.log('═══════════════════════════════════════════════════════════════\n')

// Exit mit Fehlercode wenn Probleme
process.exit(report.some(r => r.missing > 0) || (process.env.FAIL_ON_UNTRANSLATED==='1' && report.some(r => r.untranslated > 0)) ? 1 : 0)
