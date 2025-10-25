import { useEffect, useRef, useState } from 'react'
import { getWebSocketClient, type WebSocketEventType } from '@/lib/websocket'

interface WebSocketMessage {
  type: string
  data: any
  trace_id?: string
}

// Legacy simple WebSocket hook
export function useWebSocket(url: string, enabled: boolean = true) {
  const [isConnected, setIsConnected] = useState(false)
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null)
  const ws = useRef<WebSocket | null>(null)

  useEffect(() => {
    if (!enabled) return

    // Create WebSocket connection
    ws.current = new WebSocket(url)

    ws.current.onopen = () => {
      console.log('WebSocket connected:', url)
      setIsConnected(true)
    }

    ws.current.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data)
        setLastMessage(message)
      } catch (e) {
        console.error('Failed to parse WebSocket message:', e)
      }
    }

    ws.current.onerror = (error) => {
      console.error('WebSocket error:', error)
    }

    ws.current.onclose = () => {
      console.log('WebSocket disconnected')
      setIsConnected(false)
    }

    // Cleanup
    return () => {
      if (ws.current) {
        ws.current.close()
      }
    }
  }, [url, enabled])

  const sendMessage = (message: any) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(message))
    }
  }

  return {
    isConnected,
    lastMessage,
    sendMessage,
  }
}

// Enhanced WebSocket hook with reconnection & event subscriptions
export function useWebSocketEvent<T = any>(
  eventType: WebSocketEventType,
  handler: (data: T) => void,
  enabled: boolean = true
) {
  const handlerRef = useRef(handler)
  
  // Keep handler reference fresh
  useEffect(() => {
    handlerRef.current = handler
  }, [handler])

  useEffect(() => {
    if (!enabled) return

    const client = getWebSocketClient()
    
    // Connect if not already
    if (!client.isConnected) {
      client.connect()
    }

    // Subscribe to event
    const unsubscribe = client.subscribe(eventType, (data) => {
      handlerRef.current(data)
    })

    // Cleanup
    return () => {
      unsubscribe()
    }
  }, [eventType, enabled])
}

export function useTraceUpdates(traceId: string | null) {
  const wsUrl = traceId
    ? `ws://localhost:8000/api/v1/ws/trace/${traceId}`
    : ''

  const { isConnected, lastMessage } = useWebSocket(wsUrl, !!traceId)

  return {
    isConnected,
    update: lastMessage?.type === 'trace_update' ? lastMessage.data : null,
  }
}
