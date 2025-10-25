import { motion, AnimatePresence } from 'framer-motion'
import { X } from 'lucide-react'
import { useEffect, useState } from 'react'

interface ProactiveChatTeaserProps {
  onOpen: () => void
  onDismiss: () => void
}

const MESSAGES = [
  {
    text: "👋 Hey! Kann ich dir helfen?",
    delay: 5000, // 5 Sekunden
    id: 'greeting'
  },
  {
    text: "💡 Brauchst du Hilfe beim Tracing?",
    delay: 15000, // 15 Sekunden
    id: 'tracing'
  },
  {
    text: "🔍 Ich kann Adressen analysieren!",
    delay: 30000, // 30 Sekunden
    id: 'analysis'
  },
  {
    text: "🚀 Lass uns loslegen!",
    delay: 45000, // 45 Sekunden
    id: 'action'
  }
]

export default function ProactiveChatTeaser({ onOpen, onDismiss }: ProactiveChatTeaserProps) {
  const [currentMessage, setCurrentMessage] = useState<typeof MESSAGES[0] | null>(null)
  const [messageIndex, setMessageIndex] = useState(0)
  const [dismissed, setDismissed] = useState(false)

  useEffect(() => {
    // Prüfe ob User bereits dismissed hat (localStorage)
    const dismissedUntil = localStorage.getItem('chat_teaser_dismissed')
    if (dismissedUntil) {
      const until = parseInt(dismissedUntil)
      if (Date.now() < until) {
        setDismissed(true)
        return
      }
    }

    // Zeige Nachrichten nacheinander
    if (messageIndex >= MESSAGES.length) return

    const message = MESSAGES[messageIndex]
    const timer = setTimeout(() => {
      setCurrentMessage(message)
    }, message.delay)

    return () => clearTimeout(timer)
  }, [messageIndex])

  const handleDismiss = () => {
    setCurrentMessage(null)
    setDismissed(true)
    // Dismiss für 24 Stunden
    localStorage.setItem('chat_teaser_dismissed', String(Date.now() + 24 * 60 * 60 * 1000))
    onDismiss()
  }

  const handleClick = () => {
    setCurrentMessage(null)
    onOpen()
  }

  const handleClose = () => {
    setCurrentMessage(null)
    // Gehe zur nächsten Nachricht
    setMessageIndex(prev => prev + 1)
  }

  if (dismissed) return null

  return (
    <AnimatePresence>
      {currentMessage && (
        <motion.div
          initial={{ opacity: 0, y: 20, scale: 0.8 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: 10, scale: 0.9 }}
          transition={{ type: 'spring', damping: 20, stiffness: 300 }}
          className="fixed bottom-24 right-4 z-30 max-w-[280px]"
        >
          <motion.div
            className="relative bg-gradient-to-br from-blue-500 via-blue-600 to-blue-700 text-white rounded-2xl shadow-2xl p-4 pr-10"
            whileHover={{ scale: 1.02 }}
            animate={{ 
              y: [0, -5, 0],
              boxShadow: [
                '0 20px 25px -5px rgba(0, 0, 0, 0.1)',
                '0 25px 30px -5px rgba(0, 0, 0, 0.2)',
                '0 20px 25px -5px rgba(0, 0, 0, 0.1)'
              ]
            }}
            transition={{ 
              y: { duration: 2, repeat: Infinity, ease: 'easeInOut' },
              boxShadow: { duration: 2, repeat: Infinity }
            }}
          >
            {/* Schließen-Button */}
            <button
              onClick={handleClose}
              className="absolute top-2 right-2 p-1 rounded-full hover:bg-white/20 transition-colors"
              aria-label="Nachricht schließen"
            >
              <X className="w-4 h-4" />
            </button>

            {/* Pfeil nach unten rechts */}
            <div className="absolute -bottom-2 right-8 w-0 h-0 border-l-8 border-l-transparent border-r-8 border-r-transparent border-t-8 border-t-blue-600" />

            {/* Nachricht */}
            <motion.p
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.2 }}
              className="text-sm font-medium mb-3 pr-4"
            >
              {currentMessage.text}
            </motion.p>

            {/* Action Buttons */}
            <div className="flex gap-2">
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={handleClick}
                className="flex-1 px-3 py-1.5 bg-white text-primary-600 rounded-lg text-xs font-semibold hover:bg-gray-50 transition-colors"
              >
                Jetzt chatten
              </motion.button>
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={handleDismiss}
                className="px-3 py-1.5 bg-white/20 backdrop-blur-sm text-white rounded-lg text-xs font-medium hover:bg-white/30 transition-colors"
              >
                Später
              </motion.button>
            </div>

            {/* Pulsing Indicator */}
            <span className="absolute -top-1 -right-1 flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-white opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-white"></span>
            </span>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
