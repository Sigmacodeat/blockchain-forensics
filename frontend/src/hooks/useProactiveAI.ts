/**
 * useProactiveAI Hook
 * Erkennt User-Context und schlägt proaktiv Hilfe vor
 */
import { useState, useEffect, useRef } from 'react'
import { useLocation } from 'react-router-dom'
import { toast } from 'react-hot-toast'

interface ProactiveSuggestion {
  message: string
  icon: string
  action?: () => void
  priority: 'low' | 'medium' | 'high'
}

interface ProactiveAIOptions {
  enabled?: boolean
  idleTime?: number // Millisekunden bis Suggestion
  errorThreshold?: number // Anzahl Fehler bis Suggestion
}

export const useProactiveAI = (
  onSuggestionAccept: (message: string) => void,
  options: ProactiveAIOptions = {}
) => {
  const {
    enabled = true,
    idleTime = 30000, // 30 Sekunden
    errorThreshold = 3
  } = options

  const location = useLocation()
  const [suggestion, setSuggestion] = useState<ProactiveSuggestion | null>(null)
  const [errorCount, setErrorCount] = useState(0)
  const pageStartTime = useRef(Date.now())
  const idleTimer = useRef<NodeJS.Timeout>()
  const hasShownSuggestion = useRef(false)

  // Reset bei Page-Change
  useEffect(() => {
    pageStartTime.current = Date.now()
    hasShownSuggestion.current = false
    setErrorCount(0)
    setSuggestion(null)
  }, [location.pathname])

  // Idle-Detection
  useEffect(() => {
    if (!enabled || hasShownSuggestion.current) return

    // Clear existing timer
    if (idleTimer.current) {
      clearTimeout(idleTimer.current)
    }

    // Set new timer
    idleTimer.current = setTimeout(() => {
      const suggestions = getContextualSuggestions(location.pathname, errorCount)
      if (suggestions.length > 0) {
        const highPriority = suggestions.find(s => s.priority === 'high')
        showSuggestion(highPriority || suggestions[0])
      }
    }, idleTime)

    return () => {
      if (idleTimer.current) {
        clearTimeout(idleTimer.current)
      }
    }
  }, [location.pathname, idleTime, enabled, errorCount])

  // Error-Detection (Global Error Handler)
  useEffect(() => {
    const handleError = () => {
      setErrorCount(prev => prev + 1)
    }

    window.addEventListener('error', handleError)
    return () => window.removeEventListener('error', handleError)
  }, [])

  // Error-Threshold-Check
  useEffect(() => {
    if (errorCount >= errorThreshold && !hasShownSuggestion.current) {
      showSuggestion({
        message: '⚠️ Ich sehe du hast Probleme. Kann ich dir helfen?',
        icon: '🛟',
        priority: 'high',
        action: () => onSuggestionAccept('Ich habe Probleme, kannst du mir helfen?')
      })
    }
  }, [errorCount, errorThreshold])

  const getContextualSuggestions = (
    path: string, 
    errors: number
  ): ProactiveSuggestion[] => {
    const suggestions: ProactiveSuggestion[] = []

    // Remove language prefix (e.g. /de/trace -> /trace)
    const cleanPath = path.replace(/^\/[a-z]{2}(-[A-Z]{2})?/, '') || '/'

    // Trace-Page Suggestions
    if (cleanPath.startsWith('/trace')) {
      suggestions.push({
        message: '💡 Brauchst du Hilfe beim Tracing? Ich zeige dir wie es geht!',
        icon: '🔍',
        priority: 'medium',
        action: () => onSuggestionAccept('Wie funktioniert Transaction Tracing?')
      })
    }

    // Pricing-Page Suggestions
    if (cleanPath.startsWith('/pricing')) {
      suggestions.push({
        message: '💰 Fragen zu unseren Plänen? Ich erkläre dir gerne die Unterschiede!',
        icon: '💼',
        priority: 'medium',
        action: () => onSuggestionAccept('Was ist der Unterschied zwischen den Plänen?')
      })
    }

    // Investigator-Page Suggestions
    if (cleanPath.startsWith('/investigator')) {
      suggestions.push({
        message: '🔍 Der Graph-Explorer kann komplex sein. Willst du eine Tour?',
        icon: '🗺️',
        priority: 'medium',
        action: () => onSuggestionAccept('Wie benutze ich den Graph Explorer?')
      })
    }

    // Dashboard Suggestions (New Users)
    if (cleanPath === '/dashboard' || cleanPath === '/') {
      const isNewUser = !localStorage.getItem('onboarding_completed')
      if (isNewUser) {
        suggestions.push({
          message: '👋 Willkommen! Möchtest du eine kurze Tour?',
          icon: '🎯',
          priority: 'high',
          action: () => onSuggestionAccept('Ja, zeig mir eine Tour!')
        })
      }
    }

    // AI-Agent-Page Suggestions
    if (cleanPath.startsWith('/ai-agent')) {
      suggestions.push({
        message: '🤖 Der AI-Agent kann viele komplexe Aufgaben automatisieren. Brauchst du Hilfe?',
        icon: '⚡',
        priority: 'medium',
        action: () => onSuggestionAccept('Was kann der AI-Agent alles machen?')
      })
    }

    // Payment-Error Suggestions
    if (cleanPath.startsWith('/billing') && errors > 0) {
      suggestions.push({
        message: '💳 Zahlungsprobleme? Ich kann dir bei Krypto-Zahlungen helfen!',
        icon: '🆘',
        priority: 'high',
        action: () => onSuggestionAccept('Ich habe Probleme bei der Zahlung')
      })
    }

    return suggestions
  }

  const showSuggestion = (sug: ProactiveSuggestion) => {
    if (hasShownSuggestion.current) return

    setSuggestion(sug)
    hasShownSuggestion.current = true

    // Show as simple Toast (komplexes JSX würde React-Import brauchen)
    toast.success(
      `${sug.icon} ${sug.message}`,
      {
        duration: 10000,
        position: 'bottom-right'
      }
    )

    // Analytics
    try {
      if (window?.analytics?.track) {
        window.analytics.track('proactive_ai_suggestion_shown', {
          path: location.pathname,
          message: sug.message,
          priority: sug.priority,
          error_count: errorCount
        })
      }
    } catch {}
  }

  const dismissSuggestion = () => {
    setSuggestion(null)

    // Analytics
    try {
      if (window?.analytics?.track) {
        window.analytics.track('proactive_ai_suggestion_dismissed', {
          path: location.pathname
        })
      }
    } catch {}
  }

  return {
    suggestion,
    dismissSuggestion,
    triggerError: () => setErrorCount(prev => prev + 1)
  }
}
