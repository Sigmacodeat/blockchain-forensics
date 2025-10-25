import { useEffect, useRef, useState, useCallback } from 'react'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

type NewsCaseSnapshot = {
  slug: string
  name: string
  description?: string | null
  auto_trace?: boolean
  generated_at: number
  addresses: Array<{
    chain: string
    address: string
    balance?: number | null
    latest_tx?: any
  }>
}

type NewsCaseTxEvent = {
  type: 'news_case.tx'
  slug: string
  chain: string
  address: string
  tx: Record<string, any>
  trace_hint?: { source_address: string; chain?: string; direction?: string; max_depth?: number }
  timestamp: number
}

type NewsCaseKYTEvent = {
  type: 'news_case.kyt'
  slug: string
  tx_hash: string
  risk_level: 'critical' | 'high' | 'medium' | 'low' | 'safe'
  risk_score: number
  alerts: Array<Record<string, any>>
  from_labels: string[]
  to_labels: string[]
  trace_hint?: { source_address: string; chain?: string; direction?: string; max_depth?: number }
  analysis_time_ms: number
  timestamp: number
}

type NewsCaseStatusEvent = {
  type: 'news_case.status'
  slug: string
  snapshot: NewsCaseSnapshot
}

type NewsCaseSubscribed = { type: 'news_case.subscribed'; slug: string }

type NewsCaseSnapshotEvent = { type: 'news_case.snapshot'; slug: string; snapshot: NewsCaseSnapshot }

type ErrorEvent = { type: 'error'; detail?: string }

type Event = NewsCaseTxEvent | NewsCaseKYTEvent | NewsCaseStatusEvent | NewsCaseSubscribed | NewsCaseSnapshotEvent | ErrorEvent

export function useNewsCaseStream(slug?: string) {
  const [connected, setConnected] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [snapshot, setSnapshot] = useState<NewsCaseSnapshot | null>(null)
  const [events, setEvents] = useState<Event[]>([])
  const wsRef = useRef<WebSocket | null>(null)
  const backoffRef = useRef<number>(5000)
  const pollRef = useRef<number | null>(null)

  const stopPolling = useCallback(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current)
      pollRef.current = null
    }
  }, [])

  const startPolling = useCallback(() => {
    stopPolling()
    if (!slug) return
    pollRef.current = window.setInterval(async () => {
      try {
        const res = await fetch(`${API_URL}/api/v1/news-cases/${encodeURIComponent(slug)}/public`, {
          headers: { 'Accept': 'application/json' },
          credentials: 'omit',
        })
        if (res.ok) {
          const data = await res.json()
          setSnapshot(data as NewsCaseSnapshot)
        }
      } catch (_) {
        // ignore polling errors
      }
    }, 7000)
  }, [slug, stopPolling])

  const connect = useCallback(() => {
    if (!slug) return
    if (wsRef.current?.readyState === WebSocket.OPEN) return

    const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = API_URL.replace(/^https?:\/\//, '')
    const wsUrl = `${proto}//${host}/api/v1/ws/news-cases/${encodeURIComponent(slug)}`

    const ws = new WebSocket(wsUrl)

    ws.onopen = () => {
      setConnected(true)
      setError(null)
      backoffRef.current = 5000
      stopPolling()
    }

    ws.onmessage = (e) => {
      try {
        const msg: Event = JSON.parse(e.data)
        if (msg.type === 'news_case.snapshot') {
          setSnapshot(msg.snapshot)
        } else if (msg.type === 'news_case.status') {
          setSnapshot(msg.snapshot)
          setEvents((prev) => [{ ...msg }, ...prev].slice(0, 200))
        } else if (msg.type === 'news_case.tx' || msg.type === 'news_case.kyt') {
          setEvents((prev) => [msg, ...prev].slice(0, 200))
        } else if (msg.type === 'error') {
          setError(msg.detail || 'unknown error')
        }
      } catch (err) {
        console.error('Failed to parse news-case message', err)
      }
    }

    ws.onerror = () => {
      setError('connection error')
      setConnected(false)
    }

    ws.onclose = () => {
      setConnected(false)
      // auto-reconnect after 5s
      const wait = Math.min(backoffRef.current, 30000)
      setTimeout(() => {
        if (wsRef.current === ws) connect()
      }, wait)
      backoffRef.current = Math.min(backoffRef.current * 2, 30000)
      // start snapshot fallback polling while disconnected
      startPolling()
    }

    wsRef.current = ws
  }, [slug])

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
    setConnected(false)
    stopPolling()
  }, [])

  const clearEvents = useCallback(() => setEvents([]), [])

  useEffect(() => {
    connect()
    return () => disconnect()
  }, [connect, disconnect])

  return { connected, error, snapshot, events, connect, disconnect, clearEvents }
}
