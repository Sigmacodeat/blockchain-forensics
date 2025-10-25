import { useState, useEffect } from 'react'
import { useWebSocketEvent } from './useWebSocket'
import type { TraceResult } from '@/lib/types'

interface TraceProgressData {
  trace_id: string
  status: string
  progress_percentage: number
  nodes_discovered: number
  edges_discovered: number
  current_hop: number
  message?: string
}

export function useTraceProgress(traceId: string | undefined) {
  const [progress, setProgress] = useState<TraceProgressData | null>(null)
  const [isCompleted, setIsCompleted] = useState(false)
  const [result, setResult] = useState<TraceResult | null>(null)

  // Listen for progress updates
  useWebSocketEvent<TraceProgressData>(
    'trace.progress',
    (data) => {
      if (data.trace_id === traceId) {
        setProgress(data)
      }
    },
    !!traceId && !isCompleted
  )

  // Listen for completion
  useWebSocketEvent<TraceResult>(
    'trace.completed',
    (data) => {
      if (data.trace_id === traceId) {
        setIsCompleted(true)
        setResult(data)
        setProgress(null)
      }
    },
    !!traceId && !isCompleted
  )

  // Reset on trace ID change
  useEffect(() => {
    setProgress(null)
    setIsCompleted(false)
    setResult(null)
  }, [traceId])

  return {
    progress,
    isCompleted,
    result,
  }
}
