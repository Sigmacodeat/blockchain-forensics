import React from 'react'
import { useParams, useSearchParams, Link } from 'react-router-dom'
import { useI18n } from '@/contexts/I18nContext'

const API_URL = import.meta.env.VITE_API_URL || ''

interface NewsItem {
  id: string
  source: string
  url: string
  url_norm?: string
  title: string
  summary?: string
  title_translated?: string
  summary_translated?: string
  tags?: string[]
  published_at?: string
  lang?: string
}

export default function NewsPage() {
  const { lang } = useParams()
  const { currentLanguage } = useI18n()
  const [searchParams, setSearchParams] = useSearchParams()
  const [items, setItems] = React.useState<NewsItem[]>([])
  const [loading, setLoading] = React.useState(false)
  const [error, setError] = React.useState<string | null>(null)

  const q = searchParams.get('q') || ''
  const tag = searchParams.get('tag') || ''

  const targetLang = (lang || currentLanguage || 'en')

  const fetchNews = React.useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const url = new URL('/api/v1/news', API_URL)
      if (q) url.searchParams.set('q', q)
      if (tag) url.searchParams.set('tag', tag)
      url.searchParams.set('lang', targetLang)
      const res = await fetch(url.toString(), { credentials: 'include' })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      setItems((data.items || []) as NewsItem[])
    } catch (e: any) {
      setError(e?.message || 'Failed to load news')
    } finally {
      setLoading(false)
    }
  }, [q, tag, targetLang])

  React.useEffect(() => { void fetchNews() }, [fetchNews])

  // JSON-LD NewsArticle für Top-Einträge
  const jsonLd = React.useMemo(() => {
    const top = items.slice(0, 10)
    const list = top.map((it) => ({
      '@context': 'https://schema.org',
      '@type': 'NewsArticle',
      headline: (it.title_translated || it.title || '').slice(0, 110),
      datePublished: it.published_at || undefined,
      inLanguage: targetLang,
      mainEntityOfPage: it.url,
      url: window?.location?.origin + `/${targetLang}/news?u=${encodeURIComponent(it.id)}`,
      description: (it.summary_translated || it.summary || '').slice(0, 160),
      publisher: {
        '@type': 'Organization',
        name: 'Blockchain Forensics Platform'
      }
    }))
    return JSON.stringify(list, null, 0)
  }, [items, targetLang])

  return (
    <div className="min-h-[70vh] py-10">
      <div className="container mx-auto max-w-5xl px-4">
        <h1 className="text-2xl font-semibold mb-2">News</h1>
        <p className="text-slate-600 dark:text-slate-400 mb-4">Aktuelle Meldungen aus Forensik, AML, Sanctions, KYT, Mixers, Bridges und Incidents – automatisch aggregiert und übersetzt.</p>

        {/* Filter */}
        <div className="flex flex-col sm:flex-row gap-2 mb-4">
          <input
            className="rounded border px-3 py-2 bg-transparent"
            placeholder="Suche"
            value={q}
            onChange={(e) => { const v = e.target.value; const p = new URLSearchParams(searchParams); if (v) p.set('q', v); else p.delete('q'); setSearchParams(p) }}
          />
          <select
            className="rounded border px-2 py-2 bg-transparent"
            value={tag}
            onChange={(e) => { const v = e.target.value; const p = new URLSearchParams(searchParams); if (v) p.set('tag', v); else p.delete('tag'); setSearchParams(p) }}
          >
            <option value="">Alle Tags</option>
            <option value="forensics">Forensics</option>
            <option value="aml">AML</option>
            <option value="kyt">KYT</option>
            <option value="sanctions">Sanctions</option>
            <option value="mixers">Mixers</option>
            <option value="bridges">Bridges</option>
            <option value="incidents">Incidents</option>
            <option value="travel_rule">Travel Rule</option>
          </select>
        </div>

        {loading && <div className="text-slate-500">Lade…</div>}
        {error && <div className="text-red-600">{error}</div>}

        <div className="grid gap-3">
          {items.map((it) => (
            <div key={it.id} className="rounded border border-slate-200 dark:border-slate-800 p-4 bg-white dark:bg-slate-900">
              <div className="flex items-center justify-between gap-3">
                <div className="text-xs text-slate-500">{it.source}</div>
                {it.published_at && <div className="text-xs text-slate-500">{new Date(it.published_at).toLocaleString()}</div>}
              </div>
              <div className="mt-1 text-lg font-medium">
                <a href={it.url} target="_blank" rel="noreferrer" className="text-primary-600">
                  {it.title_translated || it.title}
                </a>
              </div>
              {(it.summary_translated || it.summary) && (
                <div className="mt-1 text-sm text-slate-700 dark:text-slate-300">
                  {it.summary_translated || it.summary}
                </div>
              )}
              {it.tags && it.tags.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1">
                  {it.tags.map((t) => (
                    <span key={t} className="text-xs px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800">#{t}</span>
                  ))}
                </div>
              )}
            </div>
          ))}
          {!loading && items.length === 0 && (
            <div className="text-sm text-slate-500">Keine News gefunden.</div>
          )}
        </div>

        {/* JSON-LD */}
        <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLd }} />
      </div>
    </div>
  )
}
