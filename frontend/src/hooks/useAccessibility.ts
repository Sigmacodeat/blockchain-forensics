import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'

/**
 * Hook für Barrierefreiheit-Features
 */
export const useAccessibility = () => {
  const { t } = useTranslation()
  const [highContrast, setHighContrast] = useState(false)
  const [reducedMotion, setReducedMotion] = useState(false)
  const [fontSize, setFontSize] = useState<'normal' | 'large' | 'xlarge'>('normal')

  // System-Präferenzen erkennen
  useEffect(() => {
    // Reduced Motion Detection
    const motionQuery = window.matchMedia('(prefers-reduced-motion: reduce)')
    setReducedMotion(motionQuery.matches)

    const handleMotionChange = (e: MediaQueryListEvent) => {
      setReducedMotion(e.matches)
    }
    motionQuery.addEventListener('change', handleMotionChange)

    // High Contrast Detection
    const contrastQuery = window.matchMedia('(prefers-contrast: high)')
    setHighContrast(contrastQuery.matches)

    const handleContrastChange = (e: MediaQueryListEvent) => {
      setHighContrast(e.matches)
    }
    contrastQuery.addEventListener('change', handleContrastChange)

    // Gespeicherte Präferenzen laden
    const savedFontSize = localStorage.getItem('accessibility_fontSize') as any
    if (savedFontSize) {
      setFontSize(savedFontSize)
    }

    return () => {
      motionQuery.removeEventListener('change', handleMotionChange)
      contrastQuery.removeEventListener('change', handleContrastChange)
    }
  }, [])

  // Font-Size ändern
  const changeFontSize = (size: 'normal' | 'large' | 'xlarge') => {
    setFontSize(size)
    localStorage.setItem('accessibility_fontSize', size)
    
    // CSS-Variable setzen
    const root = document.documentElement
    switch (size) {
      case 'large':
        root.style.fontSize = '18px'
        break
      case 'xlarge':
        root.style.fontSize = '20px'
        break
      default:
        root.style.fontSize = '16px'
    }
  }

  // Tastatur-Navigation verbessern
  const announceToScreenReader = (message: string, politeness: 'polite' | 'assertive' = 'polite') => {
    const announcement = document.createElement('div')
    announcement.setAttribute('role', 'status')
    announcement.setAttribute('aria-live', politeness)
    announcement.setAttribute('aria-atomic', 'true')
    announcement.className = 'sr-only'
    announcement.textContent = message
    
    document.body.appendChild(announcement)
    
    setTimeout(() => {
      document.body.removeChild(announcement)
    }, 1000)
  }

  return {
    highContrast,
    reducedMotion,
    fontSize,
    changeFontSize,
    announceToScreenReader,
    t
  }
}

/**
 * Hook für Fokus-Management
 */
export const useFocusManagement = () => {
  const [focusedElement, setFocusedElement] = useState<HTMLElement | null>(null)

  const trapFocus = (containerRef: React.RefObject<HTMLElement>) => {
    if (!containerRef.current) return

    const focusableElements = containerRef.current.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    )
    
    const firstElement = focusableElements[0] as HTMLElement
    const lastElement = focusableElements[focusableElements.length - 1] as HTMLElement

    const handleTabKey = (e: KeyboardEvent) => {
      if (e.key !== 'Tab') return

      if (e.shiftKey && document.activeElement === firstElement) {
        lastElement.focus()
        e.preventDefault()
      } else if (!e.shiftKey && document.activeElement === lastElement) {
        firstElement.focus()
        e.preventDefault()
      }
    }

    document.addEventListener('keydown', handleTabKey)
    return () => document.removeEventListener('keydown', handleTabKey)
  }

  const restoreFocus = () => {
    if (focusedElement) {
      focusedElement.focus()
      setFocusedElement(null)
    }
  }

  const saveFocus = () => {
    setFocusedElement(document.activeElement as HTMLElement)
  }

  return {
    trapFocus,
    restoreFocus,
    saveFocus
  }
}

/**
 * Hook für Tastatur-Shortcuts
 */
export const useKeyboardShortcuts = (shortcuts: Record<string, () => void>) => {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Prüfen, ob ein Input-Feld fokussiert ist
      const target = e.target as HTMLElement
      if (
        target.tagName === 'INPUT' ||
        target.tagName === 'TEXTAREA' ||
        target.isContentEditable
      ) {
        return
      }

      const key = e.key.toLowerCase()
      const modifiers = {
        ctrl: e.ctrlKey || e.metaKey,
        shift: e.shiftKey,
        alt: e.altKey
      }

      // Kombinationen prüfen
      Object.entries(shortcuts).forEach(([combo, handler]) => {
        const parts = combo.toLowerCase().split('+')
        const requiredKey = parts[parts.length - 1]
        const requiredCtrl = parts.includes('ctrl')
        const requiredShift = parts.includes('shift')
        const requiredAlt = parts.includes('alt')

        if (
          key === requiredKey &&
          modifiers.ctrl === requiredCtrl &&
          modifiers.shift === requiredShift &&
          modifiers.alt === requiredAlt
        ) {
          e.preventDefault()
          handler()
        }
      })
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [shortcuts])
}
