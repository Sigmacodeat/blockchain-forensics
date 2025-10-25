#!/usr/bin/env node
import { readdirSync, readFileSync } from 'node:fs'
import { resolve } from 'node:path'

const ROOT = process.cwd()
const DIST = resolve(ROOT, 'dist')
const LOCALES_DIR = resolve(ROOT, 'src', 'locales')

// Known base locales from src/locales/*.json
const baseLocales = readdirSync(LOCALES_DIR)
  .filter((f) => f.endsWith('.json'))
  .map((f) => f.replace(/\.json$/, ''))
  .filter((code) => !/^WORDING/.test(code))
  .sort()

// Regional variants (kept in sync with other scripts)
const REGIONALS = [
  'en-GB','en-US','en-AU','en-CA','en-NZ','en-ZA','en-SG','en-IE','en-IN','en-PH','en-HK',
  'es-ES','es-MX','es-AR','es-CL','es-CO','es-PE','es-VE','es-UY','es-419',
  'pt-PT','pt-BR','pt-AO','pt-MZ',
  'fr-FR','fr-CA','fr-BE','fr-CH','fr-LU','fr-DZ','fr-MA','fr-TN',
  'de-AT','de-CH','it-CH','nl-BE',
  'zh-CN','zh-TW','zh-HK','he-IL'
]

const locales = Array.from(new Set([...baseLocales, ...REGIONALS]))
const CORE_ROUTES = [
  '/',
  '/features',
  '/about',
  '/pricing',
  '/search',
  '/legal/privacy',
  '/legal/terms',
  '/legal/impressum',
  '/dashboards',
  '/monitoring',
  '/monitoring/dashboard'
]

function readHtml(locale, route) {
  const dir = route === '/' ? resolve(DIST, locale) : resolve(DIST, locale, route.slice(1))
  const file = resolve(dir, 'index.html')
  try {
    return readFileSync(file, 'utf8')
  } catch {
    return ''
  }
}

function main() {
  // Validate only presence of index.html (head tags are injected at runtime by SPA)
  const problems = []
  for (const loc of locales) {
    for (const route of CORE_ROUTES) {
      const html = readHtml(loc, route)
      if (!html) problems.push(`[${loc}] ${route}: missing index.html`)
    }
  }

  if (problems.length) {
    console.error('\nStatic Export Validation Errors:')
    for (const p of problems) console.error('- ' + p)
    process.exit(2)
  }

  console.log('Static export validation passed for locales:', locales.join(', '))
}

main()
