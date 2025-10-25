import React from 'react'
import { useParams, Link } from 'react-router-dom'

interface BlogPostData {
  id?: string
  slug: string
  title: string
  description?: string
  content: string
  datePublished?: string
  dateModified?: string
  author?: string
  category?: string
  tags?: string[]
  featuredImage?: { url: string; alt?: string; width?: number; height?: number }
  alternates?: Record<string, string>
}

function renderContent(text: string) {
  // Minimal Markdown-ish renderer: split paragraphs, preserve code blocks (```)
  const blocks = String(text).split(/\n\n+/)
  return (
    <div className="prose prose-slate dark:prose-invert max-w-none">
      {blocks.map((b, i) => {
        if (/^```[\s\S]*```$/.test(b.trim())) {
          const code = b.trim().replace(/^```[a-zA-Z0-9]*\n?/, '').replace(/```$/, '')
          return <pre key={i} className="bg-slate-950/80 text-slate-100 p-3 rounded overflow-x-auto"><code>{code}</code></pre>
        }
        return <p key={i}>{b}</p>
      })}
    </div>
  )
}

export default function BlogPostPage() {
  const { lang, slug } = useParams()
  const locale = lang || 'en'
  const [post, setPost] = React.useState<BlogPostData | null>(null)
  const [error, setError] = React.useState<string | null>(null)

  React.useEffect(() => {
    let cancelled = false
    async function load() {
      setError(null)
      try {
        const tryLang = async (l: string) => {
          const res = await fetch(`/blog/${l}/${encodeURIComponent(slug || '')}.json`, { cache: 'no-cache' })
          if (!res.ok) throw new Error(String(res.status))
          return res.json()
        }
        let data: BlogPostData
        try {
          data = await tryLang(locale)
        } catch {
          data = await tryLang('en')
        }
        if (!cancelled) setPost(data)
      } catch (e: any) {
        if (!cancelled) setError(e?.message || 'Fehler beim Laden')
      }
    }
    if (slug) load()
    return () => { cancelled = true }
  }, [locale, slug])

  if (error) return <div className="container mx-auto max-w-3xl px-4 py-10"><div className="text-red-600">{error}</div></div>
  if (!post) return <div className="container mx-auto max-w-3xl px-4 py-10"><div className="text-slate-500">Lade…</div></div>

  return (
    <div className="min-h-[70vh] py-10">
      <div className="container mx-auto max-w-3xl px-4">
        <nav className="text-sm text-slate-500 mb-4"><Link to={`/${locale}/blog`} className="hover:text-primary">← Blog</Link></nav>
        {post.featuredImage?.url && (
          <img src={post.featuredImage.url} alt={post.featuredImage.alt || post.title} className="w-full h-64 object-cover rounded mb-4" />
        )}
        <h1 className="text-3xl font-semibold leading-tight">{post.title}</h1>
        <div className="text-xs text-slate-500 mt-2 flex gap-3 flex-wrap">
          {post.datePublished && <span>{new Date(post.datePublished).toLocaleDateString()}</span>}
          {post.author && <span>• {post.author}</span>}
          {post.category && <span>• {post.category}</span>}
          {post.tags && post.tags.length > 0 && (
            <span>• {post.tags.slice(0, 5).join(', ')}{post.tags.length > 5 ? '…' : ''}</span>
          )}
        </div>
        {post.description && <p className="mt-4 text-lg text-slate-700 dark:text-slate-300">{post.description}</p>}

        <div className="mt-6">
          {renderContent(post.content)}
        </div>
      </div>
    </div>
  )
}
