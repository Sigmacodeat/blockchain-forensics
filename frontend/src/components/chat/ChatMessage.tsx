/**
 * ChatMessage Component
 * Einzelne Chat-Nachricht mit Timestamps, Copy-Button und Feedback
 */
import { useState } from 'react'
import { motion } from 'framer-motion'
import { Copy, Check, ThumbsUp, ThumbsDown } from 'lucide-react'
import { toast } from 'react-hot-toast'

interface ChatMessageProps {
  role: 'user' | 'assistant'
  content: string
  timestamp?: Date
  onFeedback?: (feedback: 'positive' | 'negative') => void
}

export default function ChatMessage({ role, content, timestamp, onFeedback }: ChatMessageProps) {
  const [copied, setCopied] = useState(false)
  const [feedback, setFeedback] = useState<'positive' | 'negative' | null>(null)

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(content)
      setCopied(true)
      toast.success('In Zwischenablage kopiert')
      setTimeout(() => setCopied(false), 2000)
      
      // Analytics
      try {
        if (window?.analytics?.track) {
          window.analytics.track('chat_message_copied', { role })
        }
      } catch {}
    } catch (error) {
      toast.error('Fehler beim Kopieren')
    }
  }

  const handleFeedback = async (type: 'positive' | 'negative') => {
    setFeedback(type)
    onFeedback?.(type)
    toast.success(type === 'positive' ? '👍 Danke für dein Feedback!' : '👎 Danke, wir werden besser!')
    
    // Send to Backend
    try {
      const sessionId = localStorage.getItem('chat_session_id')
      if (sessionId) {
        await fetch('/api/v1/chat/feedback', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            session_id: sessionId,
            message_index: 0,
            feedback: type,
            message: content.substring(0, 1000)
          })
        })
      }
    } catch (error) {
      // Silent fail - feedback is non-critical
      console.error('Failed to send feedback:', error)
    }
    
    // Analytics
    try {
      if (window?.analytics?.track) {
        window.analytics.track('chat_message_feedback', { 
          role, 
          feedback: type 
        })
      }
    } catch {}
  }

  const formatTimestamp = (date?: Date) => {
    if (!date) return ''
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    
    // Weniger als 1 Minute
    if (diff < 60000) return 'Gerade eben'
    
    // Weniger als 1 Stunde
    if (diff < 3600000) {
      const minutes = Math.floor(diff / 60000)
      return `vor ${minutes} Min`
    }
    
    // Heute
    if (date.toDateString() === now.toDateString()) {
      return date.toLocaleTimeString('de-DE', { 
        hour: '2-digit', 
        minute: '2-digit' 
      })
    }
    
    // Älter
    return date.toLocaleDateString('de-DE', { 
      day: '2-digit', 
      month: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const isUser = role === 'user'

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={`group relative ${isUser ? 'text-right' : 'text-left'}`}
    >
      <div className="flex flex-col gap-1">
        {/* Message Bubble */}
        <div
          className={`inline-block px-3 py-2 rounded-lg text-sm max-w-[85%] ${
            isUser
              ? 'bg-primary-600 text-white ml-auto'
              : 'bg-gray-100 dark:bg-slate-800 text-gray-900 dark:text-gray-100'
          }`}
        >
          {content}
        </div>

        {/* Timestamp & Actions */}
        <div
          className={`flex items-center gap-2 text-xs text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity ${
            isUser ? 'justify-end' : 'justify-start'
          }`}
        >
          {/* Timestamp */}
          {timestamp && (
            <span className="text-xs">
              {formatTimestamp(timestamp)}
            </span>
          )}

          {/* Copy Button (nur für AI) */}
          {!isUser && (
            <motion.button
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
              onClick={handleCopy}
              className="p-1 rounded hover:bg-gray-200 dark:hover:bg-slate-700 transition-colors"
              title="Kopieren"
            >
              {copied ? (
                <Check className="w-3 h-3 text-green-500" />
              ) : (
                <Copy className="w-3 h-3" />
              )}
            </motion.button>
          )}

          {/* Feedback Buttons (nur für AI) */}
          {!isUser && onFeedback && (
            <div className="flex items-center gap-1">
              <motion.button
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.9 }}
                onClick={() => handleFeedback('positive')}
                className={`p-1 rounded hover:bg-green-100 dark:hover:bg-green-900/20 transition-colors ${
                  feedback === 'positive' ? 'text-green-500' : ''
                }`}
                title="Hilfreich"
                disabled={feedback !== null}
              >
                <ThumbsUp className="w-3 h-3" />
              </motion.button>
              <motion.button
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.9 }}
                onClick={() => handleFeedback('negative')}
                className={`p-1 rounded hover:bg-red-100 dark:hover:bg-red-900/20 transition-colors ${
                  feedback === 'negative' ? 'text-red-500' : ''
                }`}
                title="Nicht hilfreich"
                disabled={feedback !== null}
              >
                <ThumbsDown className="w-3 h-3" />
              </motion.button>
            </div>
          )}
        </div>
      </div>
    </motion.div>
  )
}
