import { useEffect, useState } from 'react'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

type Kpis = { total_events: number; unique_users: number; pageviews: number }

type TopPath = { path: string; count: number }

export default function WebKpis() {
  const [range, setRange] = useState<'day'|'week'|'month'>('day')
  const [kpis, setKpis] = useState<Kpis | null>(null)
  const [paths, setPaths] = useState<TopPath[]>([])
  const [loading, setLoading] = useState(false)

  async function load() {
    setLoading(true)
    try {
      const [kpiRes, pathRes] = await Promise.all([
        fetch(`${API_URL}/api/v1/analytics/kpis?range=${range}`),
        fetch(`${API_URL}/api/v1/analytics/top-paths?limit=10`),
      ])
      const k = await kpiRes.json()
      const p = await pathRes.json()
      setKpis(k)
      setPaths(p.paths || [])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [range])

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Web KPIs</h2>
        <select
          value={range}
          onChange={e => setRange(e.target.value as any)}
          className="px-2 py-1 border rounded-md bg-background"
        >
          <option value="day">Letzte 24h</option>
          <option value="week">Letzte 7 Tage</option>
          <option value="month">Letzte 30 Tage</option>
        </select>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="p-4 border rounded-lg bg-muted/20">
          <div className="text-sm text-muted-foreground">Gesamt-Events</div>
          <div className="text-2xl font-bold">{kpis?.total_events ?? (loading ? '…' : 0)}</div>
        </div>
        <div className="p-4 border rounded-lg bg-muted/20">
          <div className="text-sm text-muted-foreground">Einzigartige Nutzer</div>
          <div className="text-2xl font-bold">{kpis?.unique_users ?? (loading ? '…' : 0)}</div>
        </div>
        <div className="p-4 border rounded-lg bg-muted/20">
          <div className="text-sm text-muted-foreground">Pageviews</div>
          <div className="text-2xl font-bold">{kpis?.pageviews ?? (loading ? '…' : 0)}</div>
        </div>
      </div>

      <div>
        <h3 className="text-md font-semibold mb-2">Top Seiten</h3>
        <div className="border rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-muted/40">
              <tr>
                <th className="text-left px-3 py-2">Pfad</th>
                <th className="text-right px-3 py-2">Aufrufe</th>
              </tr>
            </thead>
            <tbody>
              {paths.map((p, i) => (
                <tr key={i} className="border-t">
                  <td className="px-3 py-2 font-mono text-xs">{p.path}</td>
                  <td className="px-3 py-2 text-right">{p.count}</td>
                </tr>
              ))}
              {paths.length === 0 && (
                <tr>
                  <td className="px-3 py-6 text-center text-muted-foreground" colSpan={2}>
                    {loading ? 'Lade…' : 'Keine Daten'}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
