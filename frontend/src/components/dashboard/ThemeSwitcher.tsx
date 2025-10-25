import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Palette, Check } from 'lucide-react'
import { BLOCKCHAIN_THEMES, applyTheme, getCurrentTheme } from '@/lib/themes'

export default function ThemeSwitcher() {
  const [isOpen, setIsOpen] = useState(false)
  const [currentTheme, setCurrentTheme] = useState(getCurrentTheme())

  const handleThemeChange = (themeId: string) => {
    applyTheme(themeId)
    setCurrentTheme(themeId)
    setIsOpen(false)
  }

  const activeTheme = BLOCKCHAIN_THEMES.find(t => t.id === currentTheme)

  return (
    <div className="relative">
      {/* Theme Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-4 py-2 bg-white dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-xl hover:shadow-lg transition-all"
        aria-label="Theme wechseln"
      >
        <Palette className="w-5 h-5 text-gray-600 dark:text-gray-400" />
        <span className="text-2xl">{activeTheme?.icon}</span>
        <span className="text-sm font-medium text-gray-700 dark:text-gray-300 hidden sm:inline">
          {activeTheme?.name}
        </span>
      </button>

      {/* Theme Dropdown */}
      <AnimatePresence>
        {isOpen && (
          <>
            {/* Backdrop */}
            <div
              className="fixed inset-0 z-40"
              onClick={() => setIsOpen(false)}
            />

            {/* Dropdown */}
            <motion.div
              initial={{ opacity: 0, y: -10, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -10, scale: 0.95 }}
              transition={{ type: 'spring', stiffness: 300, damping: 30 }}
              className="absolute right-0 top-full mt-2 w-80 bg-white dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-xl shadow-2xl p-4 z-50"
            >
              <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
                <Palette className="w-4 h-4" />
                Blockchain Theme wählen
              </h3>

              <div className="grid grid-cols-2 gap-3">
                {BLOCKCHAIN_THEMES.map(theme => (
                  <button
                    key={theme.id}
                    onClick={() => handleThemeChange(theme.id)}
                    className={`relative p-4 rounded-lg border-2 transition-all ${
                      currentTheme === theme.id
                        ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                        : 'border-gray-200 dark:border-slate-700 hover:border-gray-300 dark:hover:border-slate-600'
                    }`}
                  >
                    {/* Gradient Preview */}
                    <div className={`w-full h-12 rounded-lg bg-gradient-to-r ${theme.colors.gradient} mb-3`} />

                    {/* Icon & Name */}
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="text-2xl">{theme.icon}</span>
                        <div className="text-left">
                          <div className="text-sm font-semibold text-gray-900 dark:text-white">
                            {theme.name}
                          </div>
                        </div>
                      </div>

                      {/* Check Icon */}
                      {currentTheme === theme.id && (
                        <motion.div
                          initial={{ scale: 0 }}
                          animate={{ scale: 1 }}
                          className="flex-shrink-0 w-5 h-5 bg-primary-500 rounded-full flex items-center justify-center"
                        >
                          <Check className="w-3 h-3 text-white" />
                        </motion.div>
                      )}
                    </div>

                    {/* Hover Effect */}
                    {currentTheme !== theme.id && (
                      <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/5 to-transparent opacity-0 hover:opacity-100 transition-opacity pointer-events-none rounded-lg" />
                    )}
                  </button>
                ))}
              </div>

              <div className="mt-3 pt-3 border-t border-gray-200 dark:border-slate-700 text-xs text-gray-500 dark:text-gray-400">
                💡 Theme-Auswahl wird gespeichert
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  )
}
