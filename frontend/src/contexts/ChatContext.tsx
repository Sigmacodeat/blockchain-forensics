import { createContext, useContext, useEffect, useState, useRef, ReactNode } from 'react'

interface ChatConfig {
  enabled: boolean
  showRobotIcon: boolean
  showUnreadBadge: boolean
  showQuickReplies: boolean
  showProactiveMessages: boolean
  showVoiceInput: boolean
  enableCryptoPayments: boolean
  enableIntentDetection: boolean
  enableSentimentAnalysis: boolean
  enableOfflineMode: boolean
  enableDragDrop: boolean
  enableKeyboardShortcuts: boolean
  enableDarkMode: boolean
  enableMinimize: boolean
  enableExport: boolean
  enableShare: boolean
  showWelcomeTeaser: boolean
  proactiveMessageDelay: number
  welcomeTeaserDelay: number
  autoScrollEnabled: boolean
  maxMessages: number
  maxFileSize: number
  rateLimitPerMinute: number
  primaryColor: string
  position: string
  buttonSize: string
  schemaVersion?: number
}

const DEFAULT_CONFIG: ChatConfig = {
  enabled: true,
  showRobotIcon: true,
  showUnreadBadge: true,
  showQuickReplies: true,
  showProactiveMessages: true,
  showVoiceInput: true,
  enableCryptoPayments: true,
  enableIntentDetection: true,
  enableSentimentAnalysis: true,
  enableOfflineMode: true,
  enableDragDrop: true,
  enableKeyboardShortcuts: true,
  enableDarkMode: true,
  enableMinimize: true,
  enableExport: true,
  enableShare: true,
  showWelcomeTeaser: true,
  proactiveMessageDelay: 5,
  welcomeTeaserDelay: 10,
  autoScrollEnabled: true,
  maxMessages: 50,
  maxFileSize: 10,
  rateLimitPerMinute: 20,
  primaryColor: '#6366f1',
  position: 'bottom-right',
  buttonSize: 'medium',
  schemaVersion: 1
}

interface ChatContextType {
  config: ChatConfig
  updateConfig: (newConfig: Partial<ChatConfig>) => void
  reloadConfig: () => Promise<void>
  isOnline: boolean
  isLoading: boolean
}

const ChatContext = createContext<ChatContextType | undefined>(undefined)

export function ChatProvider({ children }: { children: ReactNode }) {
  const [config, setConfig] = useState<ChatConfig>(DEFAULT_CONFIG)
  const [isOnline, setIsOnline] = useState(true)
  const [isLoading, setIsLoading] = useState(true)
  const inflightRef = useRef<Promise<void> | null>(null)
  const hasLoggedErrorRef = useRef(false)
  const LS_KEY_CFG = 'chatbot_config'
  const LS_KEY_ETAG = 'chatbot_config_etag'
  const LS_KEY_OFFLINE = 'chatbot_offline_until'
  // Endpoints are constructed as absolute URLs at runtime to avoid relative-path fetches
  const getPublicConfigEndpoints = () => {
    const paths = ['/api/v1/admin/chatbot-config/public', '/api/v1/chatbot-config/public']
    // SSR: return relative paths (server-side won't fetch here anyway)
    if (typeof window === 'undefined') return paths
    const origin = window.location.origin
    // Prefer explicit backend base URL from env
    const envBackend = (import.meta as any)?.env?.VITE_BACKEND_URL as string | undefined
    // Dev heuristic: map :3000 -> :8000 if no explicit backend URL
    let devBackend: string | null = null
    try {
      const u = new URL(origin)
      if (!envBackend && (u.port === '3000' || u.port === '5173')) {
        const mapped = `${u.protocol}//${u.hostname}:8000`
        devBackend = mapped
      }
    } catch (_) {
      devBackend = null
    }
    const bases = [envBackend, devBackend, origin].filter(Boolean) as string[]
    const urls: string[] = []
    for (const b of bases) {
      for (const p of paths) {
        try { urls.push(new URL(p, b).toString()) } catch { /* ignore */ }
      }
    }
    // Fallback to relative paths as last resort
    return urls.length ? urls : paths
  }

  // Load config on mount
  useEffect(() => {
    reloadConfig()
  }, [])

  // Listen for config updates from admin panel
  useEffect(() => {
    const handleConfigUpdate = (event: Event) => {
      const customEvent = event as CustomEvent
      if (customEvent.detail) {
        setConfig(customEvent.detail)
      }
    }

    window.addEventListener('chatbot-config-updated', handleConfigUpdate)
    return () => window.removeEventListener('chatbot-config-updated', handleConfigUpdate)
  }, [])

  const fetchWithETag = async (url: string): Promise<boolean> => {
    const controller = new AbortController()
    const timeout = setTimeout(() => controller.abort(), 3000) // Reduced timeout
    try {
      const etag = typeof window !== 'undefined' ? localStorage.getItem(LS_KEY_ETAG) : null
      const res = await fetch(url, {
        headers: etag ? { 'If-None-Match': etag } : undefined,
        signal: controller.signal
      })
      if (res.status === 304) {
        const stored = typeof window !== 'undefined' ? localStorage.getItem(LS_KEY_CFG) : null
        if (stored) {
          const parsed = JSON.parse(stored)
          setConfig(parsed)
          setIsOnline(true)
          return true
        }
        return false
      }
      if (res.ok) {
        const data = await res.json()
        const newEtag = res.headers.get('ETag')
        if (typeof window !== 'undefined') {
          localStorage.setItem(LS_KEY_CFG, JSON.stringify(data))
          if (newEtag) localStorage.setItem(LS_KEY_ETAG, newEtag)
          localStorage.removeItem(LS_KEY_OFFLINE) // Clear offline flag
        }
        setConfig(data)
        setIsOnline(true)
        return true
      }
      return false
    } catch (err) {
      // Silent error - only log once
      if (!hasLoggedErrorRef.current) {
        console.debug(`[ChatConfig] Endpoint ${url} offline:`, err instanceof Error ? err.message : String(err))
        hasLoggedErrorRef.current = true
      }
      return false
    } finally {
      clearTimeout(timeout)
    }
  }

  const reloadConfig = async () => {
    if (inflightRef.current) return inflightRef.current
    setIsLoading(true)
    
    // Check if we're in offline backoff period
    if (typeof window !== 'undefined') {
      const offlineUntil = localStorage.getItem(LS_KEY_OFFLINE)
      if (offlineUntil && Date.now() < parseInt(offlineUntil)) {
        // Still in backoff, use cached/default config
        try {
          const stored = localStorage.getItem(LS_KEY_CFG)
          if (stored) {
            const parsed = JSON.parse(stored)
            setConfig(parsed)
          } else {
            setConfig(DEFAULT_CONFIG)
          }
        } catch (_) {
          setConfig(DEFAULT_CONFIG)
        }
        setIsOnline(false)
        setIsLoading(false)
        return
      }
    }
    
    inflightRef.current = (async () => {
      const endpoints = getPublicConfigEndpoints()
      let successCount = 0
      
      // Try each endpoint once (no retries per endpoint)
      for (const ep of endpoints) {
        const ok = await fetchWithETag(ep)
        if (ok) {
          successCount++
          setIsLoading(false)
          inflightRef.current = null
          return
        }
      }
      
      // All endpoints failed - use fallback
      if (successCount === 0) {
        setIsOnline(false)
        // Set exponential backoff (30 seconds)
        if (typeof window !== 'undefined') {
          const backoffMs = 30000 // 30 seconds before next retry
          localStorage.setItem(LS_KEY_OFFLINE, String(Date.now() + backoffMs))
        }
        
        // Load from cache or use defaults
        try {
          const stored = typeof window !== 'undefined' ? localStorage.getItem(LS_KEY_CFG) : null
          if (stored) {
            const parsed = JSON.parse(stored)
            setConfig(parsed)
            if (!hasLoggedErrorRef.current) {
              console.info('[ChatConfig] Using cached config (backend offline)')
            }
          } else {
            setConfig(DEFAULT_CONFIG)
            if (!hasLoggedErrorRef.current) {
              console.info('[ChatConfig] Using default config (backend offline, no cache)')
            }
          }
        } catch (_) {
          setConfig(DEFAULT_CONFIG)
        }
      }
      
      setIsLoading(false)
      inflightRef.current = null
    })()
    return inflightRef.current
  }

  const updateConfig = (newConfig: Partial<ChatConfig>) => {
    setConfig(prev => ({ ...prev, ...newConfig }))
  }

  return (
    <ChatContext.Provider value={{ config, updateConfig, reloadConfig, isOnline, isLoading }}>
      {children}
    </ChatContext.Provider>
  )
}

export function useChatConfig() {
  const context = useContext(ChatContext)
  if (!context) {
    throw new Error('useChatConfig must be used within ChatProvider')
  }
  return context
}
