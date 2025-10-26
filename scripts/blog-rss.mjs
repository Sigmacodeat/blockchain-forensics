#!/usr/bin/env node
/**
 * RSS/Atom Feed Generator für Blog
 * Generiert rss-<lang>.xml und atom-<lang>.xml aus blog/index-<lang>.json
 * 
 * Run: node scripts/blog-rss.mjs
 */
import fs from 'fs/promises'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const ROOT = path.join(__dirname, '..')
const BLOG_DIR = path.join(ROOT, 'frontend', 'public', 'blog')
const SITE_URL = process.env.VITE_SITE_URL || 'https://forensics.ai'

async function ensureDir(p) { await fs.mkdir(p, { recursive: true }) }

async function detectLanguages() {
  try {
    const entries = await fs.readdir(BLOG_DIR, { withFileTypes: true })
    return entries.filter(e => e.isFile() && e.name.startsWith('index-') && e.name.endsWith('.json')).map(e => e.name.replace(/^index-/, '').replace(/\.json$/, ''))
  } catch { return [] }
}

async function readIndex(lang) {
  const p = path.join(BLOG_DIR, `index-${lang}.json`)
  try { return JSON.parse(await fs.readFile(p, 'utf-8')) } catch { return [] }
}

function escapeXml(s) { return s.replace(/[<>&'"]/g, c => ({ '<': '&lt;', '>': '&gt;', '&': '&amp;', "'": '&#39;', '"': '&quot;' }[c])) }

function generateRSS(lang, items) {
  const title = `SIGMACODE Forensics Blog - ${lang.toUpperCase()}`
  const description = lang === 'de' ? 'Blog über Blockchain-Forensik, Tracing-Techniken und Case Studies.' : 'Blog about blockchain forensics, tracing techniques, and case studies.'
  const link = `${SITE_URL}/${lang}/blog`
  const now = new Date().toUTCString()

  const itemsXml = items.slice(0, 20).map(item => {
    const postLink = `${SITE_URL}/${lang}/blog/${item.slug}`
    const pubDate = item.datePublished ? new Date(item.datePublished).toUTCString() : now
    const desc = escapeXml(item.description || item.title)
    const content = escapeXml(item.content ? item.content.substring(0, 500) + '...' : desc)
    return `<item>
  <title>${escapeXml(item.title)}</title>
  <description>${desc}</description>
  <content:encoded><![CDATA[${content}]]></content:encoded>
  <link>${postLink}</link>
  <guid isPermaLink="true">${postLink}</guid>
  <pubDate>${pubDate}</pubDate>
  ${item.author ? `<author>${escapeXml(item.author)}</author>` : ''}
  ${item.category ? `<category>${escapeXml(item.category)}</category>` : ''}
</item>`
  }).join('\n')

  return `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/">
  <channel>
    <title>${escapeXml(title)}</title>
    <description>${escapeXml(description)}</description>
    <link>${link}</link>
    <language>${lang}</language>
    <lastBuildDate>${now}</lastBuildDate>
    <generator>SIGMACODE Blog RSS Generator</generator>
    ${itemsXml}
  </channel>
</rss>`
}

function generateAtom(lang, items) {
  const title = `SIGMACODE Forensics Blog - ${lang.toUpperCase()}`
  const id = `${SITE_URL}/${lang}/blog`
  const now = new Date().toISOString()
  const self = `${SITE_URL}/atom-${lang}.xml`

  const entriesXml = items.slice(0, 20).map(item => {
    const entryId = `${SITE_URL}/${lang}/blog/${item.slug}`
    const updated = item.dateModified || item.datePublished || now
    const published = item.datePublished || updated
    const summary = escapeXml(item.description || item.title.substring(0, 150) + '...')
    const content = escapeXml(item.content ? item.content.substring(0, 500) + '...' : summary)
    return `<entry>
  <id>${entryId}</id>
  <title>${escapeXml(item.title)}</title>
  <summary type="html">${summary}</summary>
  <content type="html"><![CDATA[${content}]]></content>
  <link rel="alternate" type="text/html" href="${entryId}"/>
  <published>${published}</published>
  <updated>${updated}</updated>
  ${item.author ? `<author><name>${escapeXml(item.author)}</name></author>` : ''}
  ${item.category ? `<category term="${escapeXml(item.category)}"/>` : ''}
</entry>`
  }).join('\n')

  return `<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <id>${id}</id>
  <title>${escapeXml(title)}</title>
  <updated>${now}</updated>
  <link rel="self" type="application/atom+xml" href="${self}"/>
  <link rel="alternate" type="text/html" href="${id}"/>
  <author><name>SIGMACODE Editorial</name></author>
  ${entriesXml}
</feed>`
}

async function main() {
  await ensureDir(BLOG_DIR)
  const languages = await detectLanguages()
  for (const lang of languages) {
    const items = await readIndex(lang)
    if (items.length === 0) continue

    const rss = generateRSS(lang, items)
    const atom = generateAtom(lang, items)

    await fs.writeFile(path.join(BLOG_DIR, `rss-${lang}.xml`), rss, 'utf-8')
    await fs.writeFile(path.join(BLOG_DIR, `atom-${lang}.xml`), atom, 'utf-8')
    console.log(`✔ RSS/Atom for ${lang}`)
  }
}

main().catch(err => { console.error('❌', err); process.exit(1) })
