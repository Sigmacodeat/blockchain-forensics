import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import { Moon, Sun } from 'lucide-react'

export type Theme = 'light' | 'dark' | 'system'

interface ThemeColors {
  // Hintergrundfarben
  background: string
  backgroundSecondary: string
  backgroundTertiary: string

  // Textfarben
  text: string
  textSecondary: string
  textMuted: string

  // Border-Farben
  border: string
  borderSecondary: string

  // Card-Farben
  card: string
  cardHover: string

  // Button-Farben
  buttonPrimary: string
  buttonSecondary: string
  buttonHover: string

  // Status-Farben
  success: string
  warning: string
  error: string
  info: string

  // Akzentfarben
  accent: string
  accentHover: string
}

interface ThemeContextType {
  theme: Theme
  setTheme: (theme: Theme) => void
  colors: ThemeColors
  isDark: boolean
  toggleTheme: () => void
}

const lightColors: ThemeColors = {
  background: '#ffffff',
  backgroundSecondary: '#f8fafc',
  backgroundTertiary: '#f1f5f9',

  text: '#1e293b',
  textSecondary: '#64748b',
  textMuted: '#94a3b8',

  border: '#e2e8f0',
  borderSecondary: '#cbd5e1',

  card: '#ffffff',
  cardHover: '#f8fafc',

  buttonPrimary: '#0284c7',
  buttonSecondary: '#6b7280',
  buttonHover: '#0369a1',

  success: '#10b981',
  warning: '#f59e0b',
  error: '#ef4444',
  info: '#0284c7',

  accent: '#8b5cf6',
  accentHover: '#7c3aed'
}

const darkColors: ThemeColors = {
  background: '#0f172a',
  backgroundSecondary: '#1e293b',
  backgroundTertiary: '#334155',

  text: '#f8fafc',
  textSecondary: '#cbd5e1',
  textMuted: '#94a3b8',

  border: '#334155',
  borderSecondary: '#475569',

  card: '#1e293b',
  cardHover: '#334155',

  buttonPrimary: '#0284c7',
  buttonSecondary: '#6b7280',
  buttonHover: '#0369a1',

  success: '#10b981',
  warning: '#f59e0b',
  error: '#ef4444',
  info: '#0284c7',

  accent: '#8b5cf6',
  accentHover: '#7c3aed'
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined)

export const useTheme = () => {
  const context = useContext(ThemeContext)
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider')
  }
  return context
}

interface ThemeProviderProps {
  children: ReactNode
  defaultTheme?: Theme
}

export const ThemeProvider: React.FC<ThemeProviderProps> = ({
  children,
  defaultTheme = 'system'
}) => {
  const [theme, setThemeState] = useState<Theme>(defaultTheme)
  const [mounted, setMounted] = useState(false)

  // System-Theme erkennen
  const getSystemTheme = (): 'light' | 'dark' => {
    if (typeof window !== 'undefined') {
      return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
    }
    return 'light'
  }

  // Theme anwenden
  const applyTheme = (newTheme: Theme) => {
    const root = document.documentElement

    if (newTheme === 'system') {
      const systemTheme = getSystemTheme()
      root.classList.toggle('dark', systemTheme === 'dark')
    } else {
      root.classList.toggle('dark', newTheme === 'dark')
    }
  }

  // Theme setzen
  const setTheme = (newTheme: Theme) => {
    setThemeState(newTheme)
    localStorage.setItem('theme', newTheme)
    applyTheme(newTheme)
  }

  // Theme umschalten
  const toggleTheme = () => {
    const currentTheme = theme === 'system' ? getSystemTheme() : theme
    const newTheme = currentTheme === 'light' ? 'dark' : 'light'
    setTheme(newTheme)
  }

  // Aktuelles Theme ermitteln
  const getCurrentTheme = (): 'light' | 'dark' => {
    if (theme === 'system') {
      return getSystemTheme()
    }
    return theme
  }

  // Colors basierend auf aktuellem Theme
  const colors = getCurrentTheme() === 'dark' ? darkColors : lightColors
  const isDark = getCurrentTheme() === 'dark'

  // Initialisierung
  useEffect(() => {
    // Theme aus localStorage laden
    const savedTheme = localStorage.getItem('theme') as Theme | null
    if (savedTheme && ['light', 'dark', 'system'].includes(savedTheme)) {
      setThemeState(savedTheme)
    }

    // System-Theme-Listener hinzufügen
    if (typeof window !== 'undefined') {
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')

      const handleChange = () => {
        if (theme === 'system') {
          applyTheme('system')
        }
      }

      mediaQuery.addEventListener('change', handleChange)
      setMounted(true)

      return () => mediaQuery.removeEventListener('change', handleChange)
    }
  }, [])

  // Theme anwenden wenn Komponente gemountet ist
  useEffect(() => {
    if (mounted) {
      applyTheme(theme)
    }
  }, [theme, mounted])

  const value: ThemeContextType = {
    theme,
    setTheme,
    colors,
    isDark,
    toggleTheme
  }

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  )
}

// Theme-Toggle-Komponente
interface ThemeToggleProps {
  className?: string
}

export const ThemeToggle: React.FC<ThemeToggleProps> = ({ className = '' }) => {
  const { isDark, toggleTheme } = useTheme()

  return (
    <button
      type="button"
      onClick={toggleTheme}
      aria-label="Theme umschalten"
      className={`inline-flex h-9 w-9 items-center justify-center rounded-full border border-border bg-white/60 dark:bg-white/5 text-gray-700 dark:text-slate-200 hover:bg-white/80 dark:hover:bg-white/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 transition-colors ${className}`}
    >
      {isDark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
    </button>
  )
}

// Hook für Theme-Styles
export const useThemeStyles = () => {
  const { colors, isDark } = useTheme()

  return {
    colors,
    isDark,
    // Utility-Klassen für bedingte Styles
    conditionalClass: (lightClass: string, darkClass: string) =>
      isDark ? darkClass : lightClass
  }
}
