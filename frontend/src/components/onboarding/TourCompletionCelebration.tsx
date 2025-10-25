import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import ConfettiExplosion from 'react-confetti-explosion'
import { Trophy, Rocket, Sparkles, X } from 'lucide-react'
import { Link } from 'react-router-dom'

interface TourCompletionCelebrationProps {
  onClose: () => void
}

export default function TourCompletionCelebration({ onClose }: TourCompletionCelebrationProps) {
  const [isExploding, setIsExploding] = useState(true)
  const [showSecondExplosion, setShowSecondExplosion] = useState(false)

  useEffect(() => {
    // Trigger second explosion after 500ms
    const timer = setTimeout(() => {
      setShowSecondExplosion(true)
    }, 500)

    return () => clearTimeout(timer)
  }, [])

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-[100] flex items-center justify-center">
        {/* Backdrop */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="absolute inset-0 bg-black/60 backdrop-blur-sm"
          onClick={onClose}
        />

        {/* Confetti Explosions */}
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2">
          {isExploding && (
            <ConfettiExplosion
              force={0.8}
              duration={3000}
              particleCount={100}
              width={1600}
              colors={['#6366f1', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981']}
            />
          )}
        </div>
        <div className="absolute top-1/4 left-1/4">
          {showSecondExplosion && (
            <ConfettiExplosion
              force={0.6}
              duration={2500}
              particleCount={60}
              width={1200}
              colors={['#3b82f6', '#a855f7', '#f472b6', '#fbbf24', '#34d399']}
            />
          )}
        </div>

        {/* Modal */}
        <motion.div
          initial={{ opacity: 0, scale: 0.8, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.8, y: 20 }}
          transition={{ type: 'spring', stiffness: 300, damping: 30 }}
          className="relative max-w-2xl mx-4 bg-white dark:bg-slate-800 rounded-2xl shadow-2xl overflow-hidden"
        >
          {/* Gradient Background */}
          <div className="absolute inset-0 bg-gradient-to-br from-primary-600 via-purple-600 to-pink-600 opacity-10" />
          
          {/* Close Button */}
          <button
            onClick={onClose}
            className="absolute top-4 right-4 z-10 p-2 rounded-lg hover:bg-black/10 dark:hover:bg-white/10 transition-colors"
            aria-label="Schließen"
          >
            <X className="w-5 h-5 text-gray-600 dark:text-gray-400" />
          </button>

          {/* Content */}
          <div className="relative p-8 text-center">
            {/* Animated Trophy */}
            <motion.div
              initial={{ scale: 0, rotate: -180 }}
              animate={{ scale: 1, rotate: 0 }}
              transition={{ type: 'spring', stiffness: 200, damping: 15, delay: 0.2 }}
              className="inline-block mb-6"
            >
              <div className="relative">
                <div className="absolute inset-0 bg-yellow-500 rounded-full blur-xl opacity-50 animate-pulse" />
                <div className="relative w-24 h-24 bg-gradient-to-br from-yellow-400 to-orange-500 rounded-full flex items-center justify-center shadow-2xl">
                  <Trophy className="w-12 h-12 text-white" />
                </div>
              </div>
            </motion.div>

            {/* Title */}
            <motion.h2
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="text-3xl font-bold text-gray-900 dark:text-white mb-3"
            >
              🎉 Glückwunsch!
            </motion.h2>

            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
              className="text-lg text-gray-600 dark:text-gray-300 mb-6"
            >
              Du hast die Onboarding-Tour erfolgreich abgeschlossen!
            </motion.p>

            {/* Achievement Badge */}
            <motion.div
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.5, type: 'spring', stiffness: 200 }}
              className="inline-block p-6 bg-gradient-to-br from-primary-50 to-purple-50 dark:from-primary-900/20 dark:to-purple-900/20 rounded-xl border-2 border-primary-200 dark:border-primary-800 mb-8"
            >
              <div className="flex items-center gap-4">
                <div className="text-5xl">🎓</div>
                <div className="text-left">
                  <div className="text-xl font-bold text-gray-900 dark:text-white mb-1">
                    Onboarding-Meister
                  </div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">
                    +50 Punkte • Erster Schritt abgeschlossen
                  </div>
                </div>
              </div>
            </motion.div>

            {/* Benefits */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.6 }}
              className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8"
            >
              <div className="p-4 bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/10 rounded-xl">
                <div className="text-3xl mb-2">🔍</div>
                <div className="text-sm font-semibold text-gray-900 dark:text-white">Transaction Tracing</div>
                <div className="text-xs text-gray-600 dark:text-gray-400 mt-1">Multi-Chain Support</div>
              </div>
              <div className="p-4 bg-gradient-to-br from-green-50 to-green-100 dark:from-green-900/20 dark:to-green-800/10 rounded-xl">
                <div className="text-3xl mb-2">📁</div>
                <div className="text-sm font-semibold text-gray-900 dark:text-white">Case Management</div>
                <div className="text-xs text-gray-600 dark:text-gray-400 mt-1">Gerichtsverwertbar</div>
              </div>
              <div className="p-4 bg-gradient-to-br from-purple-50 to-purple-100 dark:from-purple-900/20 dark:to-purple-800/10 rounded-xl">
                <div className="text-3xl mb-2">🤖</div>
                <div className="text-sm font-semibold text-gray-900 dark:text-white">AI Agent</div>
                <div className="text-xs text-gray-600 dark:text-gray-400 mt-1">KI-Unterstützung</div>
              </div>
            </motion.div>

            {/* CTA Buttons */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.7 }}
              className="flex flex-col sm:flex-row gap-3 justify-center"
            >
              <Link
                to="/trace"
                className="inline-flex items-center justify-center gap-2 px-6 py-3 bg-gradient-to-r from-primary-600 to-purple-600 hover:from-primary-700 hover:to-purple-700 text-white font-semibold rounded-xl shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 transition-all"
                onClick={onClose}
              >
                <Rocket className="w-5 h-5" />
                Ersten Trace starten
              </Link>
              <button
                onClick={onClose}
                className="inline-flex items-center justify-center gap-2 px-6 py-3 bg-white dark:bg-slate-700 border-2 border-gray-200 dark:border-slate-600 text-gray-700 dark:text-gray-200 font-semibold rounded-xl hover:bg-gray-50 dark:hover:bg-slate-600 transition-all"
              >
                <Sparkles className="w-5 h-5" />
                Dashboard erkunden
              </button>
            </motion.div>

            {/* Footer Message */}
            <motion.p
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.8 }}
              className="mt-6 text-sm text-gray-500 dark:text-gray-400"
            >
              💡 <strong>Tipp:</strong> Nutze <kbd className="px-2 py-1 bg-gray-100 dark:bg-slate-700 rounded text-xs font-mono">⌘+K</kbd> für schnellen Zugriff
            </motion.p>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  )
}
