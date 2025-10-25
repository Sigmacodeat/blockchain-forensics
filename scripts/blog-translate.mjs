#!/usr/bin/env node
/**
 * Blog-Übersetzungs-Pipeline
 * - Quelle: content/blog/en/*.json
 * - Ziel: frontend/public/blog/<lang>/<slug>.json
 * - Sprachen: aus frontend/src/locales/*.json abgeleitet oder aus ENV BLOG_LANGS (csv)
 * - Provider: CONTENT_TRANSLATE_PROVIDER=deepl|google (Default google)
 * - Keys: DEEPL_API_KEY oder GOOGLE_API_KEY
 */
import fs from 'fs/promises'
import fssync from 'fs'
import path from 'path'
import https from 'https'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const ROOT = path.join(__dirname, '..')
const CONTENT_DIR = path.join(ROOT, 'content', 'blog', 'en')
const OUT_DIR = path.join(ROOT, 'frontend', 'public', 'blog')
const LOCALES_DIR = path.join(ROOT, 'frontend', 'src', 'locales')

const provider = (process.env.CONTENT_TRANSLATE_PROVIDER || process.env.I18N_PROVIDER || 'google').toLowerCase()
const langsEnv = process.env.BLOG_LANGS || ''

async function ensureDir(p) { await fs.mkdir(p, { recursive: true }) }

async function detectLanguages() {
  if (langsEnv) return langsEnv.split(',').map(s => s.trim()).filter(Boolean)
  try {
    const entries = await fs.readdir(LOCALES_DIR, { withFileTypes: true })
    const langs = entries.filter(e => e.isFile() && e.name.endsWith('.json')).map(e => e.name.replace(/\.json$/, ''))
    if (langs.length) return langs
  } catch {}
  // Fallback kleinster Satz
  return ['en','de','fr','es','it','pt','nl','sv','fi','pl','cs','da','ko','ja','zh-CN','tr','ru','uk']
}

function httpsRequest(options, body) {
  return new Promise((resolve, reject) => {
    const req = https.request(options, res => {
      let data = ''
      res.on('data', c => data += c)
      res.on('end', () => {
        if (res.statusCode && res.statusCode >= 200 && res.statusCode < 300) resolve({ status: res.statusCode, data })
        else reject(new Error(`HTTP ${res.statusCode}: ${data}`))
      })
    })
    req.on('error', reject)
    if (body) req.write(body)
    req.end()
  })
}

async function translateDeepl(texts, targetLang) {
  const key = process.env.DEEPL_API_KEY
  if (!key) throw new Error('DEEPL_API_KEY missing')
  const params = new URLSearchParams()
  for (const t of texts) params.append('text', t)
  params.append('target_lang', targetLang.toUpperCase())
  params.append('source_lang', 'EN')
  const res = await httpsRequest({ method: 'POST', hostname: 'api-free.deepl.com', path: '/v2/translate', headers: { 'Authorization': `DeepL-Auth-Key ${key}`, 'Content-Type': 'application/x-www-form-urlencoded' } }, params.toString())
  const json = JSON.parse(res.data)
  return json.translations.map(t => t.text)
}

async function translateGoogle(texts, targetLang) {
  const key = process.env.GOOGLE_API_KEY
  if (!key) throw new Error('GOOGLE_API_KEY missing')
  const body = JSON.stringify({ q: texts, target: targetLang, source: 'en', format: 'text' })
  const res = await httpsRequest({ method: 'POST', hostname: 'translation.googleapis.com', path: `/language/translate/v2?key=${key}`, headers: { 'Content-Type': 'application/json' } }, body)
  const json = JSON.parse(res.data)
  return json.data.translations.map(t => t.translatedText)
}

const langMap = {
  'zh-CN': { deepl: 'ZH', google: 'zh-CN' },
  'en': { deepl: 'EN', google: 'en' },
  'de': { deepl: 'DE', google: 'de' },
  'es': { deepl: 'ES', google: 'es' },
  'fr': { deepl: 'FR', google: 'fr' },
  'it': { deepl: 'IT', google: 'it' },
  'nl': { deepl: 'NL', google: 'nl' },
  'pt': { deepl: 'PT-PT', google: 'pt' },
  'pt-BR': { deepl: 'PT-BR', google: 'pt-BR' },
  'ru': { deepl: 'RU', google: 'ru' },
  'pl': { deepl: 'PL', google: 'pl' },
  'ja': { deepl: 'JA', google: 'ja' },
  'ko': { deepl: 'KO', google: 'ko' },
}

function maskPlaceholders(text) {
  const map = []
  let idx = 0
  // Code-Fences, Inline-Code, Platzhalter
  const regex = /(```[\s\S]*?```|`[^`]*`|\{\{\s*[^}]+\s*\}\}|\{\s*[^}]+\s*\}|%\d*\$?[sdif]|:[a-zA-Z_][\w-]*|\{\d+\})/g
  const masked = String(text).replace(regex, (m) => {
    const token = `__PH_${idx++}__`
    map.push({ token, value: m })
    return token
  })
  return { masked, map }
}
function unmaskPlaceholders(text, map = []) { let out = text; for (const { token, value } of map) { out = out.replaceAll(token, value) } return out }

async function translateFields(obj, target) {
  if (target === 'en') return { ...obj }
  const codes = langMap[target] || { deepl: target, google: target }
  const texts = [obj.title || '', obj.description || '', obj.content || '']
  const masks = texts.map(t => maskPlaceholders(String(t)))
  const inputs = masks.map(m => m.masked)
  let outputs
  try {
    outputs = provider === 'deepl' ? await translateDeepl(inputs, codes.deepl) : await translateGoogle(inputs, codes.google)
  } catch (e) {
    // Fallback: keep EN
    outputs = inputs
    console.warn(`[${target}] translate failed:`, e.message)
  }
  const [titleT, descT, contentT] = outputs.map((o, i) => unmaskPlaceholders(String(o), masks[i].map))
  return { ...obj, title: titleT || obj.title, description: descT || obj.description, content: contentT || obj.content }
}

async function main() {
  const languages = await detectLanguages()
  await ensureDir(OUT_DIR)
  const files = (await fs.readdir(CONTENT_DIR)).filter(f => f.endsWith('.json'))
  if (files.length === 0) {
    console.log('No source posts in content/blog/en')
    return
  }
  for (const f of files) {
    const srcPath = path.join(CONTENT_DIR, f)
    const raw = JSON.parse(await fs.readFile(srcPath, 'utf-8'))
    const base = {
      id: raw.id || path.basename(f, '.json'),
      slug: raw.slug || path.basename(f, '.json'),
      title: raw.title || raw.slug || raw.id,
      description: raw.description || '',
      content: raw.content || '',
      datePublished: raw.datePublished || null,
      dateModified: raw.dateModified || raw.datePublished || null,
      author: raw.author || 'Editorial',
      category: raw.category || null,
      tags: Array.isArray(raw.tags) ? raw.tags : [],
      featuredImage: raw.featuredImage || null,
      tenant: raw.tenant || null,
    }

    for (const lang of languages) {
      const langDir = path.join(OUT_DIR, lang)
      await ensureDir(langDir)
      const translated = await translateFields(base, lang)
      // Slug: bewusst sprachstabil (EN-Slug) für einfache hreflang-Verlinkung
      const out = { ...translated, id: base.id, slug: base.slug }
      const outPath = path.join(langDir, `${base.slug}.json`)
      await fs.writeFile(outPath, JSON.stringify(out, null, 2) + '\n', 'utf-8')
      console.log(`✔ ${lang}/${base.slug}.json`)
    }
  }
}

main().catch(err => { console.error('❌', err); process.exit(1) })
