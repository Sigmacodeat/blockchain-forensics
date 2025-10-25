#!/usr/bin/env node
/**
 * Sitemap-Generator für mehrsprachige Website
 * Generiert sitemap-{lang}.xml für jede Sprache + sitemap-index.xml
 * 
 * Run: node scripts/generate-sitemaps.mjs
 */

import fs from 'fs/promises'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

// Konfiguration
const SITE_URL = process.env.VITE_SITE_URL || 'https://sigmacode.io'
const DIST_DIR = path.join(__dirname, '..', 'dist')
const FRONTEND_PUBLIC_DIR = path.join(__dirname, '..', 'frontend', 'public')
const ROOT_PUBLIC_DIR = path.join(__dirname, '..', 'public')

// Locale-Quellverzeichnis erkennen (Frontend-Locales)
const LOCALES_DIR = path.join(__dirname, '..', 'frontend', 'src', 'locales')

// Sprachen dynamisch aus den Locale-Dateien ableiten (Fallback auf Kernmenge)
async function detectLanguages() {
  try {
    const entries = await fs.readdir(LOCALES_DIR, { withFileTypes: true })
    const langs = entries
      .filter(e => e.isFile() && e.name.endsWith('.json'))
      .map(e => e.name.replace(/\.json$/, ''))
      .sort()
    if (langs.length > 0) return langs
  } catch {}
  // Fallback-Kernmenge
  return ['en','de','fr','es','it','pt','nl','sv','fi','pl','cs','da','ko','ja','zh-CN','tr','ru','uk']
}

// Seiten-Definitionen mit Priorität und Change-Frequency
const PAGES = [
  { path: '/', priority: 1.0, changefreq: 'daily' },
  { path: '/about', priority: 0.8, changefreq: 'weekly' },
  { path: '/features', priority: 0.9, changefreq: 'weekly' },
  { path: '/pricing', priority: 1.0, changefreq: 'daily' },
  { path: '/trace', priority: 0.7, changefreq: 'weekly' },
  { path: '/analytics', priority: 0.7, changefreq: 'weekly' },
  { path: '/investigator', priority: 0.7, changefreq: 'weekly' },
  { path: '/login', priority: 0.5, changefreq: 'monthly' },
  { path: '/register', priority: 0.5, changefreq: 'monthly' },
  { path: '/legal/privacy', priority: 0.4, changefreq: 'monthly' },
  { path: '/legal/terms', priority: 0.4, changefreq: 'monthly' },
  { path: '/legal/impressum', priority: 0.3, changefreq: 'yearly' }, // nur DE
]

/**
 * Generiert XML für eine einzelne Sitemap
 */
function generateSitemapXML(lang, pages, allLangs) {
  const lastmod = new Date().toISOString().split('T')[0]
  
  const urlEntries = pages.map(page => {
    // Impressum nur für DE
    if (page.path === '/legal/impressum' && lang !== 'de') return ''
    
    const loc = `${SITE_URL}/${lang}${page.path === '/' ? '' : page.path}`
    
    return `  <url>
    <loc>${loc}</loc>
    <lastmod>${lastmod}</lastmod>
    <changefreq>${page.changefreq}</changefreq>
    <priority>${page.priority}</priority>
    ${generateAlternateLinks(page.path, lang, allLangs)}
  </url>`
  }).filter(Boolean).join('\n')

  return `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:xhtml="http://www.w3.org/1999/xhtml">
${urlEntries}
</urlset>`
}

/**
 * Generiert hreflang-Alternate-Links für eine URL
 */
function generateAlternateLinks(path, currentLang, allLangs) {
  const links = allLangs.map(lang => {
    // Impressum nur für DE
    if (path === '/legal/impressum' && lang !== 'de') return ''
    
    const href = `${SITE_URL}/${lang}${path === '/' ? '' : path}`
    return `    <xhtml:link rel="alternate" hreflang="${lang}" href="${href}" />`
  }).filter(Boolean).join('\n')

  // x-default (auf EN)
  const defaultLang = allLangs.includes('en') ? 'en' : (allLangs[0] || 'en')
  const xDefault = `    <xhtml:link rel="alternate" hreflang="x-default" href="${SITE_URL}/${defaultLang}${path === '/' ? '' : path}" />`
  
  return `${links}\n${xDefault}`
}

/**
 * Generiert Sitemap-Index
 */
function generateSitemapIndex(languages) {
  const lastmod = new Date().toISOString().split('T')[0]
  
  const sitemapEntries = languages.map(lang => `  <sitemap>
    <loc>${SITE_URL}/sitemap-${lang}.xml</loc>
    <lastmod>${lastmod}</lastmod>
  </sitemap>`).join('\n')

  return `<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${sitemapEntries}
</sitemapindex>`
}

/**
 * Hauptfunktion
 */
async function main() {
  console.log('🌍 Generiere mehrsprachige Sitemaps...\n')

  // Zielverzeichnis
  // 1) dist/ wenn vorhanden (Build)
  // 2) frontend/public/ (Vite Dev / Frontend Static)
  // 3) repo-root public/ (Fallback)
  let targetDir = DIST_DIR
  try {
    await fs.access(targetDir)
  } catch {
    try {
      await fs.access(FRONTEND_PUBLIC_DIR)
      targetDir = FRONTEND_PUBLIC_DIR
    } catch {
      targetDir = ROOT_PUBLIC_DIR
    }
  }
  
  try {
    await fs.access(targetDir)
  } catch {
    await fs.mkdir(targetDir, { recursive: true })
  }

  // Sprachen ermitteln
  const LANGUAGES = await detectLanguages()

  // Generiere Sitemap pro Sprache
  for (const lang of LANGUAGES) {
    const xml = generateSitemapXML(lang, PAGES, LANGUAGES)
    const filename = `sitemap-${lang}.xml`
    const filepath = path.join(targetDir, filename)
    
    await fs.writeFile(filepath, xml, 'utf-8')
    console.log(`✅ ${filename}`)
  }

  // Generiere Sitemap-Index
  const indexXML = generateSitemapIndex(LANGUAGES)
  const indexPath = path.join(targetDir, 'sitemap.xml')
  await fs.writeFile(indexPath, indexXML, 'utf-8')
  console.log(`✅ sitemap.xml (Index)\n`)

  console.log(`📁 Sitemaps gespeichert in: ${targetDir}`)
  console.log(`🔗 Beispiel: ${SITE_URL}/sitemap.xml`)
  console.log(`\n⚠️ Wichtig: In robots.txt eintragen:`)
  console.log(`   Sitemap: ${SITE_URL}/sitemap.xml\n`)
}

main().catch(err => {
  console.error('❌ Fehler:', err)
  process.exit(1)
})
