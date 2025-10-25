import { useEffect, useState } from 'react'
import { track } from '@/lib/analytics'

interface ExitIntentConfig {
  enabled?: boolean
  delay?: number  // Minimum time on site before showing (ms)
  onExitIntent: () => void
}

export function useExitIntent({ 
  enabled = true, 
  delay = 5000, 
  onExitIntent 
}: ExitIntentConfig) {
  const [hasShown, setHasShown] = useState(false)
  const [isReady, setIsReady] = useState(false)

  useEffect(() => {
    if (!enabled || hasShown) return

    // Check if user has dismissed exit intent before
    if (localStorage.getItem('exit_intent_dismissed')) {
      return
    }

    // Wait for delay before enabling
    const timer = setTimeout(() => {
      setIsReady(true)
    }, delay)

    return () => clearTimeout(timer)
  }, [enabled, delay, hasShown])

  useEffect(() => {
    if (!isReady) return

    const handleMouseLeave = (e: MouseEvent) => {
      // Only trigger if mouse leaves through top of viewport
      if (e.clientY < 10 && !hasShown) {
        setHasShown(true)
        track('exit_intent_shown')
        onExitIntent()
      }
    }

    document.addEventListener('mouseleave', handleMouseLeave)

    return () => {
      document.removeEventListener('mouseleave', handleMouseLeave)
    }
  }, [isReady, hasShown, onExitIntent])

  const dismiss = () => {
    setHasShown(true)
    localStorage.setItem('exit_intent_dismissed', 'true')
    track('exit_intent_dismissed')
  }

  return { hasShown, dismiss }
}
