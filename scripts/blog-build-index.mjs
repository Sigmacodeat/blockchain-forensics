#!/usr/bin/env node
/**
 * Blog-Index-Builder
 * - Scannt frontend/public/blog/<lang>/*.json
 * - Schreibt frontend/public/blog/index-<lang>.json als Liste von Metadaten
 * - Fügt alternates (hreflang) pro slug hinzu
 */
import fs from 'fs/promises'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const ROOT = path.join(__dirname, '..')
const BLOG_DIR = path.join(ROOT, 'frontend', 'public', 'blog')

async function detectLanguages() {
  try {
    const entries = await fs.readdir(BLOG_DIR, { withFileTypes: true })
    const langs = entries.filter(e => e.isDirectory()).map(e => e.name).sort()
    return langs
  } catch {
    return []
  }
}

async function readJsonSafe(p, fallback=null) {
  try { return JSON.parse(await fs.readFile(p, 'utf-8')) } catch { return fallback }
}

function pickMeta(p) {
  return {
    id: p.id || null,
    slug: p.slug,
    title: p.title,
    description: p.description || '',
    datePublished: p.datePublished || null,
    dateModified: p.dateModified || p.datePublished || null,
    author: p.author || null,
    category: p.category || null,
    tags: Array.isArray(p.tags) ? p.tags : [],
    featuredImage: p.featuredImage || null,
  }
}

async function main() {
  const languages = await detectLanguages()
  if (languages.length === 0) {
    console.log('No blog languages found at frontend/public/blog')
    return
  }

  // Build map slug -> langs
  const slugMap = new Map()
  for (const lang of languages) {
    const langDir = path.join(BLOG_DIR, lang)
    let files
    try { files = (await fs.readdir(langDir)).filter(f => f.endsWith('.json')) } catch { files = [] }
    for (const f of files) {
      const slug = f.replace(/\.json$/, '')
      const list = slugMap.get(slug) || []
      list.push(lang)
      slugMap.set(slug, list)
    }
  }

  // For each language, build index
  for (const lang of languages) {
    const langDir = path.join(BLOG_DIR, lang)
    let files
    try { files = (await fs.readdir(langDir)).filter(f => f.endsWith('.json')) } catch { files = [] }
    const items = []
    for (const f of files) {
      const p = await readJsonSafe(path.join(langDir, f))
      if (!p) continue
      const slug = p.slug
      const alternates = Object.fromEntries((slugMap.get(slug) || []).map(l => [l, `/blog/${l}/${slug}.json`]))
      items.push({ ...pickMeta(p), alternates })
    }
    // Sort by datePublished desc
    items.sort((a, b) => {
      const da = a.datePublished ? Date.parse(a.datePublished) : 0
      const db = b.datePublished ? Date.parse(b.datePublished) : 0
      return db - da
    })
    const outPath = path.join(BLOG_DIR, `index-${lang}.json`)
    await fs.writeFile(outPath, JSON.stringify(items, null, 2) + '\n', 'utf-8')
    console.log(`✔ index-${lang}.json`)
  }
}

main().catch(err => { console.error('❌', err); process.exit(1) })
