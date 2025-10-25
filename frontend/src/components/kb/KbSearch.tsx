import { useState } from 'react'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

type Hit = { path: string; title: string; snippet: string }

export default function KbSearch() {
  const [q, setQ] = useState('')
  const [hits, setHits] = useState<Hit[]>([])
  const [loading, setLoading] = useState(false)

  async function search() {
    if (!q.trim()) return
    setLoading(true)
    try {
      const res = await fetch(`${API_URL}/api/v1/kb/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: q, limit: 10 }),
      })
      const data = await res.json()
      setHits(data.results || [])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        <input
          value={q}
          onChange={e => setQ(e.target.value)}
          onKeyDown={e => { if (e.key === 'Enter') search() }}
          placeholder="Suche in Knowledge Base (docs/)"
          className="flex-1 px-3 py-2 border rounded-md bg-background"
        />
        <button className="px-3 py-2 rounded-md bg-primary-600 hover:bg-primary-700 text-white" onClick={search}>
          Suchen
        </button>
      </div>

      <div className="border rounded-lg overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-muted/40">
            <tr>
              <th className="text-left px-3 py-2">Titel</th>
              <th className="text-left px-3 py-2">Pfad</th>
            </tr>
          </thead>
          <tbody>
            {hits.map((h, i) => (
              <tr key={i} className="border-t align-top">
                <td className="px-3 py-2 font-medium">{h.title}</td>
                <td className="px-3 py-2 font-mono text-xs whitespace-pre-wrap">{h.path}\n\n{h.snippet}</td>
              </tr>
            ))}
            {hits.length === 0 && (
              <tr>
                <td className="px-3 py-6 text-center text-muted-foreground" colSpan={2}>
                  {loading ? 'Lade…' : 'Keine Ergebnisse'}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
