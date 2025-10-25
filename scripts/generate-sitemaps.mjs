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
  { path: '/optimization', priority: 0.8, changefreq: 'weekly' },
  { path: '/contact', priority: 0.6, changefreq: 'monthly' },
  { path: '/use-cases', priority: 0.7, changefreq: 'weekly' },
  { path: '/use-cases/law-enforcement', priority: 0.7, changefreq: 'weekly' },
  { path: '/use-cases/compliance', priority: 0.7, changefreq: 'weekly' },
  { path: '/use-cases/police', priority: 0.7, changefreq: 'weekly' },
  { path: '/use-cases/private-investigators', priority: 0.7, changefreq: 'weekly' },
  { path: '/use-cases/financial-institutions', priority: 0.7, changefreq: 'weekly' },
  { path: '/demo/sandbox', priority: 0.5, changefreq: 'monthly' },
  { path: '/demo/live', priority: 0.5, changefreq: 'monthly' },
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
// Blog-Unterstützung: Lese Blog-Indizes und füge Blog-URLs hinzu
import fsSync from 'fs'
const BLOG_DIR = path.join(__dirname, '..', 'frontend', 'public', 'blog')

async function collectBlogSlugMap(langs) {
  // slug -> Set(langs)
  const map = new Map()
  for (const l of langs) {
    const p = path.join(BLOG_DIR, `index-${l}.json`)
    if (!fsSync.existsSync(p)) continue
    try {
      const arr = JSON.parse(await fs.readFile(p, 'utf-8'))
      for (const it of arr) {
        const slug = it.slug
        if (!slug) continue
        if (!map.has(slug)) map.set(slug, new Set())
        map.get(slug).add(l)
      }
    } catch {}
  }
  return map
}

async function readBlogIndex(lang) {
  const p = path.join(BLOG_DIR, `index-${lang}.json`)
  if (!fsSync.existsSync(p)) return []
  try { return JSON.parse(await fs.readFile(p, 'utf-8')) } catch { return [] }
}

async function generateSitemapXML(lang, pages, allLangs) {
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

  // Blog-Einträge hinzufügen
  const blogItems = await readBlogIndex(lang)
  let blogEntries = ''
  if (Array.isArray(blogItems) && blogItems.length > 0) {
    // baue slug->langs Map einmal für Alternates
    const slugMap = await collectBlogSlugMap(allLangs)
    blogEntries = blogItems.map(item => {
      const slug = item.slug
      const loc = `${SITE_URL}/${lang}/blog/${slug}`
      // alternates nur für Sprachen, die den slug enthalten
      const langsWith = Array.from(slugMap.get(slug) || [])
      const alts = langsWith.map(l => {
        const href = `${SITE_URL}/${l}/blog/${slug}`
        return `    <xhtml:link rel="alternate" hreflang="${l}" href="${href}" />`
      }).join('\n')
      const defaultLang = allLangs.includes('en') ? 'en' : (allLangs[0] || 'en')
      const xDefault = `    <xhtml:link rel="alternate" hreflang="x-default" href="${SITE_URL}/${defaultLang}/blog/${slug}" />`
      return `  <url>
    <loc>${loc}</loc>
    <lastmod>${lastmod}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
${alts}\n${xDefault}
  </url>`
    }).join('\n')
  }

  return `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:xhtml="http://www.w3.org/1999/xhtml">
${urlEntries}
${blogEntries}
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

  // Generiere Sitemap pro Sprache
  for (const lang of LANGUAGES) {
    const xml = await generateSitemapXML(lang, PAGES, LANGUAGES)
    const filename = `sitemap-${lang}.xml`
    const filepath = path.join(targetDir, filename)
    
    await fs.writeFile(filepath, xml, 'utf-8')
    console.log(`✅ ${filename}`)
  }

  for (const r of REGIONALS) {
    const xml = generateSitemapXML(r, PAGES, [...LANGUAGES, ...REGIONALS])
    const filename = `sitemap-${r}.xml`
    const filepath = path.join(targetDir, filename)
    await fs.writeFile(filepath, xml, 'utf-8')
    console.log(`✅ ${filename}`)
  }

  // Generiere Sitemap-Index
  const indexXML = generateSitemapIndex([...LANGUAGES, ...REGIONALS])
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
