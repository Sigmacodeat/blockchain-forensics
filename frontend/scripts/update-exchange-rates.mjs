#!/usr/bin/env node
/*
 * Aktualisiert EXCHANGE_RATES in src/utils/currencyConverter.ts
 * Quelle: https://api.exchangerate.host/latest?base=USD (kostenfrei, ohne API-Key)
 */
import fs from 'fs'
import path from 'path'
import url from 'url'
import https from 'https'

const __filename = url.fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

const PROJECT_ROOT = path.resolve(__dirname, '..')
const TARGET_FILE = path.resolve(PROJECT_ROOT, 'src/utils/currencyConverter.ts')
const API_URL = 'https://api.exchangerate.host/latest?base=USD'

function fetchJSON(apiUrl) {
  return new Promise((resolve, reject) => {
    https.get(apiUrl, (res) => {
      let data = ''
      res.on('data', (chunk) => (data += chunk))
      res.on('end', () => {
        try {
          const json = JSON.parse(data)
          resolve(json)
        } catch (e) {
          reject(e)
        }
      })
    }).on('error', reject)
  })
}

function parseRatesFromFile(source) {
  // Grobe Extraktion des Rate-Blocks
  const start = source.indexOf('export const EXCHANGE_RATES')
  if (start === -1) throw new Error('EXCHANGE_RATES nicht gefunden')
  const braceStart = source.indexOf('{', start)
  let i = braceStart, depth = 0
  for (; i < source.length; i++) {
    if (source[i] === '{') depth++
    else if (source[i] === '}') { depth--; if (depth === 0) { i++; break } }
  }
  const block = source.slice(braceStart, i)
  return { block, start: braceStart, end: i }
}

function formatNumber(n) {
  // Behalte 2-5 Nachkommastellen je nach Größe
  if (n >= 1000) return n.toFixed(2)
  if (n >= 100) return n.toFixed(2)
  if (n >= 10) return n.toFixed(3)
  if (n >= 1) return n.toFixed(4)
  return n.toFixed(5)
}

function updateBlock(block, newRates) {
  // Ersetze nur Werte für existierende Keys im Block, belasse Kommentare und Reihenfolge
  return block.replace(/'([A-Z]{3})'\s*:\s*([0-9]+(?:\.[0-9]+)?)\s*,/g, (m, code) => {
    if (!(code in newRates)) return m
    const v = Number(newRates[code])
    if (!isFinite(v) || v <= 0) return m
    return `'${code}': ${formatNumber(v)},`
  })
}

async function main() {
  const dry = process.argv.includes('--dry')
  const content = fs.readFileSync(TARGET_FILE, 'utf8')
  const { block, start, end } = parseRatesFromFile(content)

  const json = await fetchJSON(API_URL)
  if (!json || !json.rates) throw new Error('Ungültige API-Antwort')
  const updatedBlock = updateBlock(block, json.rates)
  if (updatedBlock === block) {
    console.log('Keine Änderungen erforderlich.')
    return
  }
  const next = content.slice(0, start) + updatedBlock + content.slice(end)
  if (dry) {
    console.log('— Vorschau (dry-run), Datei wird nicht geschrieben —')
    console.log(next.slice(start, start + updatedBlock.length + 60))
    return
  }
  fs.writeFileSync(TARGET_FILE, next, 'utf8')
  console.log('Wechselkurse aktualisiert aus', API_URL)
}

main().catch((e) => {
  console.error('Fehler beim Aktualisieren der Wechselkurse:', e.message)
  process.exit(1)
})
