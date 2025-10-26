import React from 'react'
import { useTranslation } from 'react-i18next'
import { useI18n } from '@/contexts/I18nContext'
import api from '@/lib/api'

interface NewsItem {
  id: string
  title: string
  title_translated?: string
  summary?: string
  summary_translated?: string
  url: string
  source?: string
  published_at?: string
  tags?: string[]
  lang?: string
}

export default function NewsPage() {
  const { t } = useTranslation()
  const { currentLanguage } = useI18n()
  const [items, setItems] = React.useState<NewsItem[]>([])
  const [loading, setLoading] = React.useState(false)
  const [error, setError] = React.useState<string | null>(null)
  const [q, setQ] = React.useState('')

  const load = React.useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await api.get('/api/v1/news', {
        params: {
          lang: currentLanguage,
          q: q || undefined,
          limit: 50,
        }
      })
      const data = res.data || {}
      setItems(Array.isArray(data.items) ? data.items : [])
    } catch (e: any) {
      setError(e?.message || 'Failed to load news')
    } finally {
      setLoading(false)
    }
  }, [currentLanguage, q])

  React.useEffect(() => {
    const id = window.setTimeout(() => {
      load()
    }, 200)
    return () => window.clearTimeout(id)
  }, [load])

  return (
    <div className="container mx-auto max-w-4xl px-4 sm:px-6 py-8">
      <h1 className="text-2xl sm:text-3xl font-bold mb-4">{t('news.title', { defaultValue: 'Blockchain News' })}</h1>

      <div className="flex items-center gap-2 mb-4">
        <input
          type="search"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder={t('common.search', { defaultValue: 'Search' })}
          className="w-full px-3 py-2 border rounded-md bg-background text-foreground"
          aria-label={t('common.search', { defaultValue: 'Search' })}
        />
        <button
          onClick={load}
          className="px-3 py-2 rounded-md bg-primary text-primary-foreground"
        >
          {t('common.search', { defaultValue: 'Search' })}
        </button>
      </div>

      {loading && (
        <div className="text-sm text-muted-foreground">{t('common.loading', { defaultValue: 'Loading…' })}</div>
      )}
      {error && (
        <div className="text-sm text-red-600 dark:text-red-400">{error}</div>
      )}

      <ul className="divide-y divide-border rounded-lg border border-border overflow-hidden">
        {items.map((it) => (
          <li key={it.id} className="p-4 hover:bg-muted/50 transition">
            <a href={it.url} target="_blank" rel="noopener noreferrer" className="block">
              <div className="flex items-start justify-between gap-3">
                <h2 className="text-base sm:text-lg font-semibold">
                  {it.title_translated || it.title}
                </h2>
                {it.source && (
                  <span className="text-xs text-muted-foreground shrink-0">{it.source}</span>
                )}
              </div>
              {it.summary_translated || it.summary ? (
                <p className="mt-1 text-sm text-muted-foreground line-clamp-3">
                  {it.summary_translated || it.summary}
                </p>
              ) : null}
              <div className="mt-2 flex items-center gap-2 text-xs text-muted-foreground">
                {it.published_at && (
                  <time dateTime={it.published_at}>{new Date(it.published_at).toLocaleString()}</time>
                )}
                {Array.isArray(it.tags) && it.tags.length > 0 && (
                  <span className="inline-flex flex-wrap gap-1">
                    {it.tags.slice(0, 5).map(tag => (
                      <span key={tag} className="px-1.5 py-0.5 rounded bg-primary/10 text-primary">#{tag}</span>
                    ))}
                  </span>
                )}
              </div>
            </a>
          </li>
        ))}
        {!loading && !error && items.length === 0 && (
          <li className="p-4 text-sm text-muted-foreground">{t('common.no_results', { defaultValue: 'No results' })}</li>
        )}
      </ul>
    </div>
  )
}
