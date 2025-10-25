/**
 * useKYTStream Hook - Real-Time Transaction Monitoring
 * 
 * Connects to KYT Engine WebSocket for live transaction risk analysis
 */
import { useState, useEffect, useRef, useCallback } from 'react'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export interface KYTAlert {
  type: string
  severity: string
  title: string
  description: string
  tx_hash: string
  from_address?: string
  to_address?: string
  value_usd?: number
}

export interface KYTResult {
  tx_hash: string
  risk_level: 'critical' | 'high' | 'medium' | 'low' | 'safe'
  risk_score: number
  alerts: KYTAlert[]
  from_labels: string[]
  to_labels: string[]
  analysis_time_ms: number
}

export function useKYTStream(userId?: string) {
  const [connected, setConnected] = useState(false)
  const [results, setResults] = useState<KYTResult[]>([])
  const [error, setError] = useState<string | null>(null)
  const wsRef = useRef<WebSocket | null>(null)

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return
    }

    const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = API_URL.replace(/^https?:\/\//, '')
    const wsUrl = `${proto}//${host}/api/v1/ws/kyt`

    const ws = new WebSocket(wsUrl)

    ws.onopen = () => {
      console.log('KYT WebSocket connected')
      setConnected(true)
      setError(null)
      
      // Send subscribe message
      ws.send(JSON.stringify({
        action: 'subscribe',
        user_id: userId || 'anonymous'
      }))
    }

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data)
        
        if (msg.type === 'kyt.result') {
          setResults(prev => [msg.data, ...prev].slice(0, 100)) // Keep last 100
        } else if (msg.type === 'error') {
          setError(msg.detail || 'Unknown error')
        }
      } catch (e) {
        console.error('Failed to parse KYT message:', e)
      }
    }

    ws.onerror = (e) => {
      console.error('KYT WebSocket error:', e)
      setError('Connection error')
      setConnected(false)
    }

    ws.onclose = () => {
      console.log('KYT WebSocket closed')
      setConnected(false)
      
      // Auto-reconnect after 5s
      setTimeout(() => {
        if (wsRef.current === ws) {
          connect()
        }
      }, 5000)
    }

    wsRef.current = ws
  }, [userId])

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
    setConnected(false)
  }, [])

  const clearResults = useCallback(() => {
    setResults([])
  }, [])

  // Auto-connect on mount
  useEffect(() => {
    connect()
    return () => {
      disconnect()
    }
  }, [connect, disconnect])

  return {
    connected,
    results,
    error,
    connect,
    disconnect,
    clearResults
  }
}
