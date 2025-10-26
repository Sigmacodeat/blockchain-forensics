import React from 'react'
import { Helmet } from 'react-helmet-async'
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
  alternates?: Record<string, string>
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

  const pageTitle = locale === 'de' ? 'Blog - SIGMACODE Forensics' : 'Blog - SIGMACODE Forensics'
  const pageDescription = locale === 'de' 
    ? 'Entdecken Sie tiefgehende Einblicke in Blockchain-Forensik, Tracing-Techniken und Case Studies.'
    : 'Discover deep insights into blockchain forensics, tracing techniques, and case studies.'

  return (
    <>
      <Helmet>
        <title>{pageTitle}</title>
        <meta name="description" content={pageDescription} />
        <meta property="og:title" content={pageTitle} />
        <meta property="og:description" content={pageDescription} />
        <meta property="og:type" content="website" />
        <meta property="og:url" content={`https://forensics.ai/${locale}/blog`} />
        <meta name="twitter:card" content="summary_large_image" />
        <meta name="twitter:title" content={pageTitle} />
        <meta name="twitter:description" content={pageDescription} />
        <link rel="canonical" href={`https://forensics.ai/${locale}/blog`} />
        {/* hreflang alternates - dynamically from index files */}
        {items?.some(it => it.alternates) && (
          <>
            {Object.keys(items.find(it => it.alternates)?.alternates || {}).map(altLang => (
              <link key={altLang} rel="alternate" hrefLang={altLang} href={`https://forensics.ai/${altLang}/blog`} />
            ))}
            <link rel="alternate" hrefLang="x-default" href="https://forensics.ai/en/blog" />
          </>
        )}
      </Helmet>

      <div className="min-h-[70vh] py-10">
        <div className="container mx-auto max-w-5xl px-4">
          <h1 className="text-2xl font-semibold mb-4">{locale === 'de' ? 'Blog' : 'Blog'}</h1>
          {items?.length === 0 && <div className="text-slate-500">{locale === 'de' ? 'Noch keine Beiträge.' : 'No posts yet.'}</div>}
          {error && <div className="text-red-600">{error}</div>}
          <div className="grid gap-4">
            {items?.map((it) => (
              <article key={it.slug} className="rounded-lg border border-slate-200 dark:border-slate-800 p-4 bg-white dark:bg-slate-900">
                <div className="flex items-start gap-4">
                  {it.featuredImage?.url && (
                    <img src={it.featuredImage.url} alt={it.featuredImage.alt || it.title} className="w-32 h-20 object-cover rounded" />
                  )}
                  <div className="flex-1">
                    <h2 className="text-lg font-medium">
                      <Link to={`/${locale}/blog/${encodeURIComponent(it.slug)}`}>{it.title}</Link>
                    </h2>
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
    </>
  )
}
