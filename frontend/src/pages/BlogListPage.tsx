import React from 'react'
import { Link, useParams } from 'react-router-dom'

interface BlogIndexItem {
  id?: string
  slug: string
  title: string
  description?: string
  datePublished?: string
  dateModified?: string
  author?: string
  category?: string
  tags?: string[]
  featuredImage?: { url: string; alt?: string; width?: number; height?: number }
}

export default function BlogListPage() {
  const { lang } = useParams()
  const locale = lang || 'en'
  const [items, setItems] = React.useState<BlogIndexItem[] | null>(null)
  const [error, setError] = React.useState<string | null>(null)

  React.useEffect(() => {
    let cancelled = false
    async function load() {
      setError(null)
      try {
        const tryLang = async (l: string) => {
          const res = await fetch(`/blog/index-${l}.json`, { cache: 'no-cache' })
          if (!res.ok) throw new Error(String(res.status))
          return res.json()
        }
        let data: BlogIndexItem[]
        try {
          data = await tryLang(locale)
        } catch {
          data = await tryLang('en')
        }
        if (!cancelled) setItems(data)
      } catch (e: any) {
        if (!cancelled) setError(e?.message || 'Fehler beim Laden')
      }
    }
    load()
    return () => { cancelled = true }
  }, [locale])

  if (error) return <div className="container mx-auto max-w-5xl px-4 py-10"><div className="text-red-600">{error}</div></div>
  if (!items) return <div className="container mx-auto max-w-5xl px-4 py-10"><div className="text-slate-500">Lade…</div></div>

  return (
    <div className="min-h-[70vh] py-10">
      <div className="container mx-auto max-w-5xl px-4">
        <h1 className="text-2xl font-semibold mb-4">Blog</h1>
        {items.length === 0 && <div className="text-slate-500">Noch keine Beiträge.</div>}
        <div className="grid gap-4">
          {items.map((it) => (
            <article key={it.slug} className="rounded-lg border border-slate-200 dark:border-slate-800 p-4 bg-white dark:bg-slate-900">
              <div className="flex items-start gap-4">
                {it.featuredImage?.url && (
                  <img src={it.featuredImage.url} alt={it.featuredImage.alt || it.title} className="w-32 h-20 object-cover rounded" />
                )}
                <div className="flex-1">
                  <h2 className="text-lg font-medium"><Link to={`/${locale}/blog/${encodeURIComponent(it.slug)}`}>{it.title}</Link></h2>
                  {it.description && <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">{it.description}</p>}
                  <div className="text-xs text-slate-500 mt-2 flex gap-3">
                    {it.datePublished && <span>{new Date(it.datePublished).toLocaleDateString()}</span>}
                    {it.author && <span>• {it.author}</span>}
                    {it.category && <span>• {it.category}</span>}
                  </div>
                </div>
              </div>
            </article>
          ))}
        </div>
      </div>
    </div>
  )
}
