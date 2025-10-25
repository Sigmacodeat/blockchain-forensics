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

const locales = Array.from(new Set([...baseLocales, ...REGIONALS]))
const CORE_ROUTES = [
  '/',
  '/optimization',
  '/features',
  '/about',
  '/contact',
  '/pricing',
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
