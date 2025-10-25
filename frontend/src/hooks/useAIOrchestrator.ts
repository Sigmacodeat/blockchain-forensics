/**
 * useAIOrchestrator - Zentraler Hook für alle AI-Interaktionen
 * 
 * Vereint ChatWidget, AIAgentPage und forensische Aktionen in einen Hook.
 * 
 * Features:
 * - ask(): Standard-Chat-Nachricht senden
 * - investigate(): Forensische Investigation mit Streaming
 * - forensicAction(): Direkte Tool-Calls (trace, risk, bridge, etc.)
 * - openFeature(): Navigate zu Features mit Pre-Fill
 * - detectAndExecute(): Intent-Detection + Auto-Action
 */

import { useNavigate } from 'react-router-dom'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useState, useCallback } from 'react'
import { useI18n } from '@/contexts/I18nContext'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Types
interface ForensicAction {
  tool: 'trace-address' | 'risk-score' | 'bridge-lookup' | 'cluster-analysis' | 'trigger-alert'
  params: Record<string, any>
}

interface IntentResult {
  intent: string
  params: Record<string, any>
  confidence: number
  suggested_action?: string
  description: string
}

interface InvestigationResult {
  response: string
  tool_calls?: Array<{tool: string; params: any}>
  data?: any
  success: boolean
}

export function useAIOrchestrator() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [lastIntent, setLastIntent] = useState<IntentResult | null>(null)
  const { currentLanguage } = useI18n()

  // 1. Standard-Chat (einfach, ohne spezielle Features)
  const askMutation = useMutation({
    mutationFn: async (message: string) => {
      const response = await fetch(`${API_URL}/api/v1/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Accept-Language': currentLanguage || 'en' },
        body: JSON.stringify({ message, language: currentLanguage || 'en' })
      })
      if (!response.ok) throw new Error(`HTTP ${response.status}`)
      return response.json()
    }
  })

  const ask = useCallback(async (message: string) => {
    return askMutation.mutateAsync(message)
  }, [askMutation])

  // 2. Forensische Investigation (mit optionalem Streaming)
  const investigateMutation = useMutation({
    mutationFn: async ({ query, stream }: { query: string; stream?: boolean }) => {
      if (stream) {
        // SSE-Streaming via useChatStream (extern)
        // Wird von Komponenten genutzt die useChatStream direkt verwenden
        throw new Error('Streaming via useChatStream - use component integration')
      } else {
        // REST-Call
        const response = await fetch(`${API_URL}/api/v1/agent/investigate`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'Accept-Language': currentLanguage || 'en' },
          body: JSON.stringify({ query, language: currentLanguage || 'en' })
        })
        if (!response.ok) throw new Error(`HTTP ${response.status}`)
        return response.json() as Promise<InvestigationResult>
      }
    }
  })

  const investigate = useCallback(async (query: string) => {
    return investigateMutation.mutateAsync({ query, stream: false })
  }, [investigateMutation])

  // 3. Direkte Tool-Calls (für fortgeschrittene User)
  const forensicActionMutation = useMutation({
    mutationFn: async ({ tool, params }: ForensicAction) => {
      const response = await fetch(`${API_URL}/api/v1/agent/tools/${tool}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Accept-Language': currentLanguage || 'en' },
        body: JSON.stringify({ ...params, language: currentLanguage || 'en' })
      })
      if (!response.ok) throw new Error(`HTTP ${response.status}`)
      return response.json()
    }
  })

  const forensicAction = useCallback(async (tool: ForensicAction['tool'], params: Record<string, any>) => {
    return forensicActionMutation.mutateAsync({ tool, params })
  }, [forensicActionMutation])

  // 4. Feature-Navigation mit Pre-Fill
  const openFeature = useCallback((
    feature: 'trace' | 'risk' | 'case' | 'investigator' | 'correlation' | 'graph',
    prefill?: Record<string, string>
  ) => {
    const routes: Record<string, string> = {
      trace: '/trace',
      risk: '/dashboard',
      case: '/cases/new',
      investigator: '/investigator',
      correlation: '/correlation',
      graph: '/investigator', // Graph = Investigator
    }

    const queryString = prefill ? `?${new URLSearchParams(prefill).toString()}` : ''
    navigate(`${routes[feature]}${queryString}`)
  }, [navigate])

  // 5. Intent-Detection + Auto-Action
  const detectIntentMutation = useMutation({
    mutationFn: async (message: string) => {
      const response = await fetch(`${API_URL}/api/v1/chat/detect-intent`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Accept-Language': currentLanguage || 'en' },
        body: JSON.stringify({ query: message, language: currentLanguage || 'en' })
      })
      if (!response.ok) throw new Error(`HTTP ${response.status}`)
      return response.json() as Promise<IntentResult>
    },
    onSuccess: (data) => {
      setLastIntent(data)
    }
  })

  const detectAndExecute = useCallback(async (message: string, autoExecute = false) => {
    const intent = await detectIntentMutation.mutateAsync(message)
    
    if (autoExecute && intent.confidence > 0.8 && intent.suggested_action) {
      // Auto-Execute: Navigate direkt
      if (intent.suggested_action.startsWith('/')) {
        navigate(intent.suggested_action)
      }
    }
    
    return intent
  }, [detectIntentMutation, navigate])

  // 6. Hilfs-Funktionen
  const quickTrace = useCallback(async (address: string, chain = 'ethereum') => {
    return forensicActionMutation.mutateAsync({
      tool: 'trace-address',
      params: { address, max_depth: 5, chain }
    })
  }, [forensicActionMutation])

  const quickRisk = useCallback(async (address: string) => {
    return forensicActionMutation.mutateAsync({
      tool: 'risk-score',
      params: { address }
    })
  }, [forensicActionMutation])

  return {
    // Haupt-Funktionen
    ask,
    investigate,
    forensicAction,
    openFeature,
    detectAndExecute,
    
    // Quick-Actions
    quickTrace,
    quickRisk,
    
    // State
    lastIntent,
    isAsking: askMutation.isPending,
    isInvestigating: investigateMutation.isPending,
    isExecutingAction: forensicActionMutation.isPending,
    isDetecting: detectIntentMutation.isPending,
    
    // Errors
    askError: askMutation.error,
    investigateError: investigateMutation.error,
    forensicError: forensicActionMutation.error,
    detectError: detectIntentMutation.error,
  }
}
