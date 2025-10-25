#!/usr/bin/env node
import { readdirSync, readFileSync, writeFileSync, existsSync, mkdirSync, cpSync } from 'node:fs'
import { resolve, dirname } from 'node:path'

const ROOT = process.cwd()
const DIST = resolve(ROOT, 'dist')
const PUBLIC_DIR = resolve(ROOT, 'public')

// Load index.html built by Vite
const indexHtmlPath = resolve(DIST, 'index.html')
if (!existsSync(indexHtmlPath)) {
  console.error('dist/index.html not found. Run `npm run build` first.')
  process.exit(1)
}
const INDEX_HTML = readFileSync(indexHtmlPath, 'utf8')

// Core routes (SPA paths) to pre-create for static hosts
const CORE_ROUTES = [
  '/',
  '/features',
  '/about',
  '/pricing',
  '/search',
  '/legal/privacy',
  '/legal/terms',
  '/legal/impressum',
  // Monitoring & Dashboards
  '/dashboards',
  '/monitoring',
  '/monitoring/dashboard'
]

// Discover base locales from src/locales
const LOCALES_DIR = resolve(ROOT, 'src', 'locales')
const files = readdirSync(LOCALES_DIR).filter((f) => f.endsWith('.json'))
const baseLocales = files.map((f) => f.replace(/\.json$/, '')).filter((code) => !/^WORDING/.test(code)).sort()

// Regional variants to export as well (must match generate-sitemaps.mjs)
const REGIONALS = [
  'en-GB','en-US','en-AU','en-CA','en-NZ','en-ZA','en-SG','en-IE','en-IN','en-PH','en-HK',
  'es-ES','es-MX','es-AR','es-CL','es-CO','es-PE','es-VE','es-UY','es-419',
  'pt-PT','pt-BR','pt-AO','pt-MZ',
  'fr-FR','fr-CA','fr-BE','fr-CH','fr-LU','fr-DZ','fr-MA','fr-TN',
  'de-AT','de-CH','it-CH','nl-BE',
  'zh-CN','zh-TW','zh-HK','he-IL'
]

const allLocales = Array.from(new Set([...baseLocales, ...REGIONALS]))

function writeRoute(locale, route) {
  const outDir = resolve(DIST, locale, route === '/' ? '.' : route.slice(1))
  mkdirSync(outDir, { recursive: true })
  const outFile = resolve(outDir, 'index.html')
  writeFileSync(outFile, INDEX_HTML, 'utf8')
}

function main() {
  // Ensure public assets copied (Vite already copies public into dist). If necessary, copy again.
  if (existsSync(PUBLIC_DIR)) {
    cpSync(PUBLIC_DIR, DIST, { recursive: true, force: true })
  }

  for (const locale of allLocales) {
    for (const route of CORE_ROUTES) {
      writeRoute(locale, route)
    }
  }
  console.log(`Exported static routes for ${allLocales.length} locales × ${CORE_ROUTES.length} routes`)
}

main()
