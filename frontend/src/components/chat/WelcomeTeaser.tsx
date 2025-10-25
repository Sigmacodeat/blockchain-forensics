/**
 * WelcomeTeaser Component
 * Zeigt nach 10 Sekunden einen kleinen Teaser neben dem Chat-Button
 * "Frag mich was! 💬" um Nutzer zum Klicken zu animieren
 */
import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, Sparkles } from 'lucide-react'

interface WelcomeTeaserProps {
  onDismiss: () => void
  onOpen: () => void
}

export default function WelcomeTeaser({ onDismiss, onOpen }: WelcomeTeaserProps) {
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    // Check if user has seen teaser before
    const hasSeenTeaser = localStorage.getItem('chat_teaser_seen')
    if (hasSeenTeaser) return

    // Show after 10 seconds
    const timer = setTimeout(() => {
      setVisible(true)
      // Track
      try {
        if (window?.analytics?.track) {
          window.analytics.track('chat_teaser_shown', { delay: 10000 })
        }
      } catch {}
    }, 10000)

    return () => clearTimeout(timer)
  }, [])

  const handleDismiss = () => {
    setVisible(false)
    localStorage.setItem('chat_teaser_seen', 'true')
    onDismiss()
    // Track
    try {
      if (window?.analytics?.track) {
        window.analytics.track('chat_teaser_dismissed', {})
      }
    } catch {}
  }

  const handleClick = () => {
    setVisible(false)
    localStorage.setItem('chat_teaser_seen', 'true')
    onOpen()
    // Track
    try {
      if (window?.analytics?.track) {
        window.analytics.track('chat_teaser_clicked', {})
      }
    } catch {}
  }

  if (!visible) return null

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, x: 100, scale: 0.8 }}
        animate={{ opacity: 1, x: 0, scale: 1 }}
        exit={{ opacity: 0, x: 100, scale: 0.8 }}
        transition={{ type: 'spring', stiffness: 200, damping: 20 }}
        className="fixed bottom-24 right-4 z-40 max-w-[280px]"
      >
        <div className="bg-gradient-to-br from-primary-600 via-purple-600 to-blue-600 text-white rounded-2xl shadow-2xl p-4 relative">
          {/* Close Button */}
          <button
            onClick={handleDismiss}
            className="absolute -top-2 -right-2 bg-white dark:bg-slate-800 rounded-full p-1.5 shadow-lg hover:scale-110 transition-transform"
            aria-label="Schließen"
          >
            <X className="w-3 h-3 text-gray-600 dark:text-gray-300" />
          </button>

          {/* Content */}
          <div className="flex items-start gap-3 mb-3">
            <div className="p-2 bg-white/20 rounded-lg backdrop-blur-sm">
              <Sparkles className="w-5 h-5" />
            </div>
            <div className="flex-1">
              <h3 className="font-semibold text-sm mb-1">
                Hallo! 👋
              </h3>
              <p className="text-xs opacity-90 leading-relaxed">
                Ich bin dein AI-Assistent. Frag mich zu Blockchain-Forensik, Tracing oder Compliance!
              </p>
            </div>
          </div>

          {/* CTA Button */}
          <button
            onClick={handleClick}
            className="w-full bg-white text-primary-700 font-semibold py-2 px-4 rounded-lg hover:bg-gray-50 transition-colors text-sm flex items-center justify-center gap-2 shadow-md"
          >
            Chat starten
            <span className="text-lg">💬</span>
          </button>

          {/* Arrow pointing to chat button */}
          <div className="absolute -bottom-2 right-8 w-0 h-0 border-l-[8px] border-l-transparent border-r-[8px] border-r-transparent border-t-[8px] border-t-blue-600" />
        </div>
      </motion.div>
    </AnimatePresence>
  )
}
