import { useEffect } from 'react'

interface KeyboardShortcuts {
  onToggleChat?: () => void
  onFocusInput?: () => void
  onClearChat?: () => void
}

export function useKeyboardShortcuts({
  onToggleChat,
  onFocusInput,
  onClearChat
}: KeyboardShortcuts) {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // ESC - Toggle Chat
      if (e.key === 'Escape' && onToggleChat) {
        e.preventDefault()
        onToggleChat()
      }

      // Ctrl/Cmd + K - Focus Input
      if ((e.ctrlKey || e.metaKey) && e.key === 'k' && onFocusInput) {
        e.preventDefault()
        onFocusInput()
      }

      // Ctrl/Cmd + Shift + Delete - Clear Chat
      if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'Delete' && onClearChat) {
        e.preventDefault()
        if (window.confirm('Chat-Historie wirklich löschen?')) {
          onClearChat()
        }
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [onToggleChat, onFocusInput, onClearChat])
}
