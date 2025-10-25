import React, { useMemo, useState, useEffect } from 'react'
import axios from 'axios'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { useKYTStream } from '@/hooks/useKYTStream'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

interface MonitorAddressPanelProps {
  address: string
  onClose?: () => void
}

const levelColor: Record<string, string> = {
  critical: 'bg-red-600 text-white',
  high: 'bg-orange-500 text-white',
  medium: 'bg-yellow-400 text-black',
  low: 'bg-blue-500 text-white',
  safe: 'bg-green-500 text-white'
}

const MonitorAddressPanel: React.FC<MonitorAddressPanelProps> = ({ address, onClose }) => {
  const { connected, results, error } = useKYTStream()
  const [tab, setTab] = useState<'live' | 'history'>('live')
  const [historyData, setHistoryData] = useState<any[]>([])
  const [historyLoading, setHistoryLoading] = useState(false)
  const [page, setPage] = useState(1)
  const pageSize = 20

  useEffect(() => {
    if (tab === 'history' && address) {
      const load = async () => {
        setHistoryLoading(true)
        try {
          const resp = await axios.get(`${API_BASE_URL}/api/v1/kyt/alerts`, {
            params: { address, days: 7, limit: 100 }
          })
          setHistoryData(resp.data?.alerts || [])
        } catch (e) {
          console.error(e)
        } finally {
          setHistoryLoading(false)
        }
      }
      load()
    }
  }, [tab, address])

  const filtered = useMemo(() => {
    const a = (address || '').toLowerCase()
    return results.filter(r => {
      const alerts = r.alerts || []
      return alerts.some(al =>
        (al.from_address && al.from_address.toLowerCase() === a) ||
        (al.to_address && al.to_address.toLowerCase() === a)
      )
    })
  }, [results, address])

  return (
    <Card>
      <CardHeader className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Button size="sm" variant={tab === 'live' ? 'default' : 'outline'} onClick={() => setTab('live')}>Live</Button>
          <Button size="sm" variant={tab === 'history' ? 'default' : 'outline'} onClick={() => setTab('history')}>History</Button>
        </div>
        <div className="flex items-center gap-2">
          <span className={`text-xs px-2 py-0.5 rounded-full ${connected ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-700'}`}>
            {connected ? 'Connected' : 'Connecting...'}
          </span>
          {tab === 'history' && historyData.length > 0 && (
            <Button size="sm" variant="outline" onClick={() => {
              const csv = 'timestamp,risk_level,title,address,tx_hash\n' + historyData.map(h => `${h.timestamp},${h.risk_level},${h.title},${h.address || ''},${h.tx_hash || ''}`).join('\n')
              const blob = new Blob([csv], { type: 'text/csv' })
              const url = URL.createObjectURL(blob)
              const a = document.createElement('a')
              a.href = url
              a.download = `kyt-history-${address.slice(0,8)}.csv`
              a.click()
              URL.revokeObjectURL(url)
            }}>CSV</Button>
          )}
          {onClose && (
            <button onClick={onClose} className="text-xs px-2 py-1 rounded border hover:bg-gray-100 dark:hover:bg-slate-700">Close</button>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {error && (
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}
        {tab === 'live' && (
          <>
            <div className="text-xs text-muted-foreground">Monitoring address: <code className="font-mono">{address}</code></div>
            {filtered.length === 0 ? (
              <div className="text-sm text-muted-foreground">No live alerts yet.</div>
            ) : (
              <div className="space-y-2 max-h-64 overflow-auto">
                {filtered.map((r, idx) => (
                  <div key={`${r.tx_hash}-${idx}`} className="p-2 border rounded">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-mono truncate max-w-[70%]" title={r.tx_hash}>{r.tx_hash}</span>
                      <span className={`text-xs px-2 py-0.5 rounded-full ${levelColor[r.risk_level]}`}>{r.risk_level.toUpperCase()}</span>
                    </div>
                    <div className="mt-1 flex flex-wrap gap-1">
                      {r.alerts?.slice(0, 4).map((a: any, i: number) => (
                        <Badge key={`al-${i}`} variant="secondary">{a.title}</Badge>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </>
        )}
        {tab === 'history' && (
          <>
            <div className="text-xs text-muted-foreground">Last 7 days for: <code className="font-mono">{address}</code></div>
            {historyLoading ? (
              <div className="text-sm text-muted-foreground">Loading...</div>
            ) : historyData.length === 0 ? (
              <div className="text-sm text-muted-foreground">No history found.</div>
            ) : (
              <>
                <div className="space-y-2 max-h-64 overflow-auto">
                  {historyData.slice((page - 1) * pageSize, page * pageSize).map((h, i) => (
                    <div key={i} className="p-2 border rounded">
                      <div className="flex items-center justify-between">
                        <span className="text-xs">{new Date(h.timestamp).toLocaleString()}</span>
                        <span className={`text-xs px-2 py-0.5 rounded-full ${levelColor[h.risk_level] || 'bg-gray-100'}`}>{h.risk_level.toUpperCase()}</span>
                      </div>
                      <div className="text-sm font-medium">{h.title}</div>
                      {h.tx_hash && <div className="text-xs font-mono truncate">{h.tx_hash}</div>}
                    </div>
                  ))}
                </div>
                {historyData.length > pageSize && (
                  <div className="flex items-center gap-2 justify-center">
                    <Button size="sm" variant="outline" disabled={page === 1} onClick={() => setPage(p => p - 1)}>Prev</Button>
                    <span className="text-xs">Page {page} of {Math.ceil(historyData.length / pageSize)}</span>
                    <Button size="sm" variant="outline" disabled={page >= Math.ceil(historyData.length / pageSize)} onClick={() => setPage(p => p + 1)}>Next</Button>
                  </div>
                )}
              </>
            )}
          </>
        )}
      </CardContent>
    </Card>
  )
}

export default MonitorAddressPanel
