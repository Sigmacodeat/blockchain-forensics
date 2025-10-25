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
  '/businessplan',
  '/optimization',
  '/contact',
  '/use-cases',
  '/use-cases/law-enforcement',
  '/use-cases/compliance',
  '/use-cases/police',
  '/use-cases/private-investigators',
  '/use-cases/financial-institutions',
  '/demo/sandbox',
  '/demo/live',
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
  'en-GB','en-US','en-AU','en-CA','en-NZ','en-IE','en-ZA','en-SG','en-HK','en-IN','en-PH','en-NG','en-KE','en-GH','en-PK',
  'es-ES','es-MX','es-AR','es-CL','es-CO','es-PE','es-VE','es-UY','es-BO','es-EC','es-CR','es-PA','es-PY','es-DO','es-GT','es-HN','es-NI','es-SV','es-PR','es-419',
  'pt-PT','pt-BR','pt-AO','pt-MZ','pt-CV','pt-GW','pt-ST',
  'fr-FR','fr-CA','fr-BE','fr-CH','fr-LU','fr-DZ','fr-MA','fr-TN','fr-SN','fr-CM','fr-CI',
  'de-DE','de-AT','de-CH','de-LU','de-LI','it-CH','it-IT','nl-NL','nl-BE',
  'sv-SE','sv-FI','fi-FI','da-DK','nb-NO','nn-NO','is-IS',
  'pl-PL','cs-CZ','sk-SK','sl-SI','hu-HU','ro-RO','ro-MD','bg-BG','et-EE','lv-LV','lt-LT',
  'sr-RS','sr-BA','bs-BA','mk-MK','sq-AL','sq-MK','sq-XK',
  'el-GR','el-CY',
  'ru-RU','ru-BY','ru-KZ','ru-KG','uk-UA','be-BY',
  'ar-SA','ar-AE','ar-EG','ar-MA','ar-DZ','ar-TN','ar-LB','ar-IQ','ar-JO','ar-OM','ar-QA','ar-KW','ar-BH','ar-PS','ar-LY','ar-SY','ar-YE','ar-SD','he-IL','fa-IR','fa-AF',
  'hi-IN','bn-BD','bn-IN','id-ID','ms-MY','ms-SG','ms-BN','th-TH','ur-PK','ur-IN','vi-VN','ja-JP','ko-KR',
  'zh-CN','zh-TW','zh-HK','zh-MO'
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
    // Note: Blog routes are not exported currently
  }
  console.log(`Exported static routes for ${allLocales.length} locales × ${CORE_ROUTES.length} routes`)
}

main()
