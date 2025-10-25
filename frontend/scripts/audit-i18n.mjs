#!/usr/bin/env node

/**
 * i18n Audit Script
 * Überprüft die Vollständigkeit und Konsistenz aller Übersetzungen
 * 
 * Usage: node scripts/audit-i18n.mjs
 */

import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

const LOCALES_DIR = path.join(__dirname, '../src/locales')
const COLORS = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m',
  bold: '\x1b[1m'
}

// Hilfsfunktionen
function log(msg, color = 'reset') {
  console.log(`${COLORS[color]}${msg}${COLORS.reset}`)
}

function countKeys(obj, prefix = '') {
  let count = 0
  for (const key in obj) {
    if (typeof obj[key] === 'object' && obj[key] !== null) {
      count += countKeys(obj[key], prefix + key + '.')
    } else {
      count++
    }
  }
  return count
}

function getAllKeys(obj, prefix = '') {
  const keys = []
  for (const key in obj) {
    const fullKey = prefix + key
    if (typeof obj[key] === 'object' && obj[key] !== null) {
      keys.push(...getAllKeys(obj[key], fullKey + '.'))
    } else {
      keys.push(fullKey)
    }
  }
  return keys
}

function findEmptyValues(obj, prefix = '') {
  const empty = []
  for (const key in obj) {
    const fullKey = prefix + key
    if (typeof obj[key] === 'object' && obj[key] !== null) {
      empty.push(...findEmptyValues(obj[key], fullKey + '.'))
    } else if (obj[key] === '' || obj[key] === null || obj[key] === undefined) {
      empty.push(fullKey)
    }
  }
  return empty
}

// Hauptfunktion
async function auditI18n() {
  log('\n╔════════════════════════════════════════════════════════╗', 'cyan')
  log('║     🌍  i18n AUDIT - Internationalisierung Check     ║', 'cyan')
  log('╚════════════════════════════════════════════════════════╝\n', 'cyan')

  // 1. Dateien laden
  const files = fs.readdirSync(LOCALES_DIR).filter(f => f.endsWith('.json'))
  log(`📁 Gefundene Sprachdateien: ${files.length}\n`, 'blue')

  // 2. Englisch als Referenz laden
  const enPath = path.join(LOCALES_DIR, 'en.json')
  if (!fs.existsSync(enPath)) {
    log('❌ ERROR: en.json nicht gefunden!', 'red')
    process.exit(1)
  }
  
  const enData = JSON.parse(fs.readFileSync(enPath, 'utf8'))
  const enKeys = new Set(getAllKeys(enData))
  const enKeyCount = enKeys.size
  
  log(`📊 Referenz (EN): ${enKeyCount} Keys\n`, 'green')

  // 3. Alle Sprachen prüfen
  const results = []
  let hasErrors = false
  let hasWarnings = false

  for (const file of files) {
    const lang = file.replace('.json', '')
    const filePath = path.join(LOCALES_DIR, file)
    
    try {
      const data = JSON.parse(fs.readFileSync(filePath, 'utf8'))
      const keys = getAllKeys(data)
      const keySet = new Set(keys)
      const keyCount = keys.length
      const emptyValues = findEmptyValues(data)
      const fileSize = fs.statSync(filePath).size
      
      // Keys vergleichen
      const missingKeys = [...enKeys].filter(k => !keySet.has(k))
      const extraKeys = [...keySet].filter(k => !enKeys.has(k))
      
      results.push({
        lang,
        keyCount,
        emptyValues: emptyValues.length,
        missingKeys: missingKeys.length,
        extraKeys: extraKeys.length,
        fileSize,
        diff: keyCount - enKeyCount,
        status: emptyValues.length > 0 ? 'error' : 
                (missingKeys.length > 20 ? 'warning' : 'ok'),
        emptyList: emptyValues,
        missingList: missingKeys.slice(0, 5),
        extraList: extraKeys.slice(0, 5)
      })
      
      if (emptyValues.length > 0) hasErrors = true
      if (missingKeys.length > 20) hasWarnings = true
      
    } catch (error) {
      log(`❌ ERROR parsing ${file}: ${error.message}`, 'red')
      hasErrors = true
    }
  }

  // 4. Ergebnisse sortieren und anzeigen
  results.sort((a, b) => {
    // Fehler zuerst
    if (a.status === 'error' && b.status !== 'error') return -1
    if (b.status === 'error' && a.status !== 'error') return 1
    // Dann Warnungen
    if (a.status === 'warning' && b.status !== 'warning') return -1
    if (b.status === 'warning' && a.status !== 'warning') return 1
    // Dann nach Keys
    return b.keyCount - a.keyCount
  })

  // Tabellen-Header
  log('┌────────┬────────┬────────┬────────┬────────┬──────────┬────────┐', 'cyan')
  log('│ Sprache│  Keys  │ Leer   │ Fehlt  │  Extra │   Diff   │  Size  │', 'cyan')
  log('├────────┼────────┼────────┼────────┼────────┼──────────┼────────┤', 'cyan')

  for (const r of results) {
    const statusIcon = r.status === 'error' ? '❌' : 
                       r.status === 'warning' ? '⚠️ ' : 
                       '✅'
    const diff = r.diff === 0 ? '  ✓' : r.diff > 0 ? `+${r.diff}` : r.diff
    const empty = r.emptyValues === 0 ? '  ✓' : r.emptyValues
    const missing = r.missingKeys === 0 ? '  ✓' : r.missingKeys
    const extra = r.extraKeys === 0 ? '  ✓' : r.extraKeys
    
    const line = `│ ${statusIcon} ${r.lang.padEnd(4)} │ ${String(r.keyCount).padStart(6)} │ ${String(empty).padStart(6)} │ ${String(missing).padStart(6)} │ ${String(extra).padStart(6)} │ ${String(diff).padStart(8)} │ ${(r.fileSize/1024).toFixed(0).padStart(5)}K │`
    
    const color = r.status === 'error' ? 'red' : 
                  r.status === 'warning' ? 'yellow' : 
                  'reset'
    log(line, color)
  }
  
  log('└────────┴────────┴────────┴────────┴────────┴──────────┴────────┘\n', 'cyan')

  // 5. Detaillierte Fehler anzeigen
  if (hasErrors) {
    log('\n❌ FEHLER gefunden:\n', 'red')
    for (const r of results.filter(r => r.status === 'error')) {
      log(`  ${r.lang}: ${r.emptyValues} leere Übersetzungen`, 'red')
      if (r.emptyList.length > 0) {
        log(`    Beispiele:`, 'red')
        r.emptyList.slice(0, 3).forEach(k => log(`      - ${k}`, 'red'))
        if (r.emptyList.length > 3) {
          log(`      ... und ${r.emptyList.length - 3} weitere`, 'red')
        }
      }
    }
  }

  if (hasWarnings) {
    log('\n⚠️  WARNUNGEN:\n', 'yellow')
    for (const r of results.filter(r => r.status === 'warning')) {
      log(`  ${r.lang}: ${r.missingKeys} fehlende Keys`, 'yellow')
      if (r.missingList.length > 0) {
        log(`    Beispiele:`, 'yellow')
        r.missingList.forEach(k => log(`      - ${k}`, 'yellow'))
        if (r.missingKeys > 5) {
          log(`      ... und ${r.missingKeys - 5} weitere`, 'yellow')
        }
      }
    }
  }

  // 6. Zusammenfassung
  log('\n╔════════════════════════════════════════════════════════╗', 'cyan')
  log('║                    📊 ZUSAMMENFASSUNG                  ║', 'cyan')
  log('╚════════════════════════════════════════════════════════╝\n', 'cyan')

  const totalKeys = results.reduce((sum, r) => sum + r.keyCount, 0)
  const avgKeys = Math.round(totalKeys / results.length)
  const totalEmpty = results.reduce((sum, r) => sum + r.emptyValues, 0)
  const okCount = results.filter(r => r.status === 'ok').length
  const warnCount = results.filter(r => r.status === 'warning').length
  const errCount = results.filter(r => r.status === 'error').length

  log(`  Sprachen total:       ${results.length}`, 'blue')
  log(`  Keys durchschnittlich: ${avgKeys}`, 'blue')
  log(`  Keys total:           ~${totalKeys.toLocaleString()}`, 'blue')
  log(`  Leere Werte total:    ${totalEmpty}`, totalEmpty === 0 ? 'green' : 'red')
  log(``, 'reset')
  log(`  Status:`, 'blue')
  log(`    ✅ OK:       ${okCount}`, okCount > 0 ? 'green' : 'reset')
  if (warnCount > 0) log(`    ⚠️  Warnung: ${warnCount}`, 'yellow')
  if (errCount > 0) log(`    ❌ Fehler:   ${errCount}`, 'red')

  // 7. Finale Bewertung
  log('\n╔════════════════════════════════════════════════════════╗', 'cyan')
  if (hasErrors) {
    log('║                  ❌ AUDIT FAILED                       ║', 'red')
    log('║  Bitte behebe die Fehler bevor du deployst!           ║', 'red')
  } else if (hasWarnings) {
    log('║                  ⚠️  AUDIT WARNING                     ║', 'yellow')
    log('║  Einige Übersetzungen fehlen, aber kein Blocker       ║', 'yellow')
  } else {
    log('║                  ✅ AUDIT PASSED                       ║', 'green')
    log('║  Alle Übersetzungen sind vollständig!                 ║', 'green')
  }
  log('╚════════════════════════════════════════════════════════╝\n', 'cyan')

  // Exit code
  process.exit(hasErrors ? 1 : 0)
}

// Script ausführen
auditI18n().catch(err => {
  log(`\n❌ Unerwarteter Fehler: ${err.message}`, 'red')
  console.error(err)
  process.exit(1)
})
