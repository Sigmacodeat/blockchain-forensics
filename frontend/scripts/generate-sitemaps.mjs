#!/usr/bin/env node
import { readdirSync, writeFileSync, existsSync, mkdirSync, readFileSync } from 'node:fs'
import { resolve, dirname } from 'node:path'

// Config
const SITE_ORIGIN = process.env.SITE_ORIGIN || 'https://sigmacode.io'
const PUBLIC_DIR = resolve(process.cwd(), 'public')

// Core routes (without language prefix)
const CORE_ROUTES = [
  '/',
  '/features',
  '/about',
  '/pricing',
  '/search',
  '/legal/privacy',
  '/legal/terms',
  '/legal/impressum',
  // Monitoring & Dashboards (sprachpräfix wird später ergänzt)
  '/dashboards',
  '/monitoring',
  '/monitoring/dashboard'
]

// Discover base locales from src/locales/*.json
const LOCALES_DIR = resolve(process.cwd(), 'src', 'locales')
const files = readdirSync(LOCALES_DIR).filter((f) => f.endsWith('.json'))
const baseLocales = files
  .map((f) => f.replace(/\.json$/, ''))
  .filter((code) => !/^WORDING/.test(code))
  .sort()

// Add regional variants for state-of-the-art hreflang coverage
const REGIONALS = [
  'en-GB','en-US','en-AU','en-CA','en-NZ','en-ZA','en-SG','en-IE','en-IN','en-PH','en-HK',
  'es-ES','es-MX','es-AR','es-CL','es-CO','es-PE','es-VE','es-UY','es-419',
  'pt-PT','pt-BR','pt-AO','pt-MZ',
  'fr-FR','fr-CA','fr-BE','fr-CH','fr-LU','fr-DZ','fr-MA','fr-TN',
  'de-AT','de-CH','it-CH','nl-BE',
  'zh-CN','zh-TW','zh-HK','he-IL','fa-IR'
]

// Build full alternate matrix: base + regional variants mapped to base availability
const alternates = new Map()
for (const base of baseLocales) {
  alternates.set(base, [base])
}
for (const r of REGIONALS) {
  const base = r.split('-')[0]
  if (alternates.has(base)) {
    alternates.get(base).push(r)
  }
}

function xmlEscape(s) {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;')
}

function generateLocaleSitemap(locale, allLocalesForAlternates) {
  const urlsetOpen = '<?xml version="1.0" encoding="UTF-8"?>\n' +
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
    + 'xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
  const urlsetClose = '</urlset>\n'

  let body = ''
  for (const route of CORE_ROUTES) {
    // current URL for this locale
    const loc = `${SITE_ORIGIN}/${locale}${route === '/' ? '' : route}`

    // build xhtml:link alternates for allLocalesForAlternates
    let xhtml = ''
    for (const alt of allLocalesForAlternates) {
      const href = `${SITE_ORIGIN}/${alt}${route === '/' ? '' : route}`
      xhtml += `    <xhtml:link rel="alternate" hreflang="${alt}" href="${xmlEscape(href)}"/>\n`
    }
    // x-default
    const xDefault = `${SITE_ORIGIN}/en${route === '/' ? '' : route}`
    xhtml += `    <xhtml:link rel="alternate" hreflang="x-default" href="${xmlEscape(xDefault)}"/>\n`

    body += '  <url>\n' +
      `    <loc>${xmlEscape(loc)}</loc>\n` +
      xhtml +
      '  </url>\n'
  }

  return urlsetOpen + body + urlsetClose
}

function writeFileSafe(target, content) {
  const dir = dirname(target)
  if (!existsSync(dir)) mkdirSync(dir, { recursive: true })
  writeFileSync(target, content)
}

function main() {
  const indexParts = ['<?xml version="1.0" encoding="UTF-8"?>', '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']

  // For each base locale we generate a sitemap including its regional alternates and all other base locales
  for (const [base, regs] of alternates.entries()) {
    const allForAlternates = Array.from(new Set([...baseLocales, ...REGIONALS]))
    const xml = generateLocaleSitemap(base, allForAlternates)
    const file = resolve(PUBLIC_DIR, `sitemap-${base}.xml`)
    writeFileSafe(file, xml)
    indexParts.push('  <sitemap>')
    indexParts.push(`    <loc>${SITE_ORIGIN}/sitemap-${base}.xml</loc>`) 
    indexParts.push(`    <lastmod>${new Date().toISOString().slice(0,10)}</lastmod>`) 
    indexParts.push('  </sitemap>')
  }

  // Also generate sitemaps for regional variants that map to existing bases
  for (const r of REGIONALS) {
    const base = r.split('-')[0]
    if (!alternates.has(base)) continue
    const allForAlternates = Array.from(new Set([...baseLocales, ...REGIONALS]))
    const xml = generateLocaleSitemap(r, allForAlternates)
    const file = resolve(PUBLIC_DIR, `sitemap-${r}.xml`)
    writeFileSafe(file, xml)
    indexParts.push('  <sitemap>')
    indexParts.push(`    <loc>${SITE_ORIGIN}/sitemap-${r}.xml</loc>`) 
    indexParts.push(`    <lastmod>${new Date().toISOString().slice(0,10)}</lastmod>`) 
    indexParts.push('  </sitemap>')
  }

  indexParts.push('</sitemapindex>')
  const indexXml = indexParts.join('\n') + '\n'
  writeFileSafe(resolve(PUBLIC_DIR, 'sitemap.xml'), indexXml)

  // robots.txt: Ensure sitemap reference exists
  const robotsPath = resolve(PUBLIC_DIR, 'robots.txt')
  let robots = existsSync(robotsPath) ? readFileSync(robotsPath, 'utf8') : 'User-agent: *\nAllow: /\n'
  if (!robots.includes('Sitemap:')) {
    robots += `\nSitemap: ${SITE_ORIGIN}/sitemap.xml\n`
    writeFileSafe(robotsPath, robots)
  }

  console.log('Sitemaps generated successfully.')
}

main()
