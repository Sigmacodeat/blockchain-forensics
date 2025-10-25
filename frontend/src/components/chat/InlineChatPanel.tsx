/**
 * InlineChatPanel - Dediziertes Chat-Panel für MainDashboard
 * 
 * Features:
 * - Inline-Chat (nicht als Modal)
 * - Quick-Actions für häufige Forensik-Aufgaben
 * - Live-Tool-Progress
 * - Dark-Mode optimiert
 * - Glassmorphism-Design
 */

import { useState, useEffect, useRef } from 'react'
import { useI18n } from '@/contexts/I18nContext'
import { Bot, Send, Loader2, Sparkles, TrendingUp, Shield, Search, FolderPlus } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { useAIOrchestrator } from '@/hooks/useAIOrchestrator'
import ForensicWizard from '@/components/chat/ForensicWizard'
import ForensicResultDisplay from '@/components/chat/ForensicResultDisplay'

interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  markers?: ForensicMarker[]
}

interface ForensicMarker {
  type: 'download' | 'case' | 'result'
  category?: 'trace' | 'risk' | 'case' | 'report'
  id: string
  format?: string
  openLink?: string
  summary?: Record<string, any>
}

export default function InlineChatPanel() {
  const { currentLanguage, t } = useI18n()
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [showCommandPalette, setShowCommandPalette] = useState(false)
  const [showWizard, setShowWizard] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const commandPaletteRef = useRef<HTMLDivElement>(null)
  const firstPaletteActionRef = useRef<HTMLButtonElement>(null)
  const wizardButtonRef = useRef<HTMLButtonElement>(null)
  
  const ai = useAIOrchestrator()

  // Auto-scroll zu letzter Message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Keyboard Shortcuts (Ctrl/Cmd + K für Command Palette)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault()
        setShowCommandPalette(prev => !prev)
      }
      if (e.key === 'Escape') {
        setShowCommandPalette(false)
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [])

  // Focus input on mount
  useEffect(() => {
    inputRef.current?.focus()
  }, [])

  // Focus and keyboard trap for Command Palette
  useEffect(() => {
    if (!showCommandPalette) return
    // focus first action
    firstPaletteActionRef.current?.focus()
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.preventDefault()
        setShowCommandPalette(false)
        return
      }
      if (e.key === 'Tab') {
        const container = commandPaletteRef.current
        if (!container) return
        const focusable = container.querySelectorAll<HTMLElement>('button, a[href], [tabindex]:not([tabindex="-1"])')
        const first = focusable[0]
        const last = focusable[focusable.length - 1]
        if (!first || !last) return
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault(); (last as HTMLElement).focus()
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault(); (first as HTMLElement).focus()
        }
      }
    }
    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [showCommandPalette])

  // When Command Palette closes, return focus to input
  useEffect(() => {
    if (!showCommandPalette) {
      inputRef.current?.focus()
    }
  }, [showCommandPalette])

  const quickActions = [
    { 
      label: t('chat.quick_actions.high_risk_trace.label'),
      query: t('chat.quick_actions.high_risk_trace.query'),
      icon: Search,
      category: 'analysis'
    },
    { 
      label: t('chat.quick_actions.mixer_activity.label'),
      query: t('chat.quick_actions.mixer_activity.query'),
      icon: Shield,
      category: 'compliance'
    },
    { 
      label: t('chat.quick_actions.daily_summary.label'),
      query: t('chat.quick_actions.daily_summary.query'),
      icon: TrendingUp,
      category: 'reporting'
    },
    { 
      label: t('chat.quick_actions.sanctions_check.label'),
      query: t('chat.quick_actions.sanctions_check.query'),
      icon: Shield,
      category: 'compliance'
    },
    { 
      label: t('chat.quick_actions.bridge_transfers.label'),
      query: t('chat.quick_actions.bridge_transfers.query'),
      icon: TrendingUp,
      category: 'analysis'
    },
    { 
      label: t('chat.quick_actions.active_cases.label'),
      query: t('chat.quick_actions.active_cases.query'),
      icon: Search,
      category: 'cases'
    },
  ]

  const handleSend = async (query: string) => {
    if (!query.trim()) return
    
    // User-Message
    setMessages(prev => [...prev, { role: 'user', content: query, timestamp: new Date() }])
    setInput('')

    try {
      // AI-Response
      const result = await ai.ask(query)
      const reply = result.reply || 'Keine Antwort'
      
      // Detect forensic markers in response
      const markers = detectForensicMarkers(reply)
      const cleanContent = cleanMarkers(reply)
      
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: cleanContent,
        timestamp: new Date(),
        markers
      }])
    } catch (error) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: t('chat.error_fetch'),
        timestamp: new Date()
      }])
    }
  }

  // Detect markers in AI response
  const detectForensicMarkers = (text: string): ForensicMarker[] => {
    const markers: ForensicMarker[] = []
    
    // [DOWNLOAD:type:id:format]
    const downloadRegex = /\[DOWNLOAD:(\w+):([^:]+):(\w+)\]/g
    let match
    while ((match = downloadRegex.exec(text)) !== null) {
      markers.push({
        type: 'download',
        category: match[1] as any,
        id: match[2],
        format: match[3]
      })
    }
    
    // [CASE_CREATED:id]
    const caseRegex = /\[CASE_CREATED:([^\]]+)\]/g
    while ((match = caseRegex.exec(text)) !== null) {
      markers.push({
        type: 'case',
        category: 'case',
        id: match[1],
        openLink: `/cases/${match[1]}`
      })
    }
    
    return markers
  }

  // Clean markers from text
  const cleanMarkers = (text: string): string => {
    return text
      .replace(/\[DOWNLOAD:\w+:[^:]+:\w+\]/g, '')
      .replace(/\[CASE_CREATED:[^\]]+\]/g, '')
      .trim()
  }

  const handleQuickAction = (query: string) => {
    void handleSend(query)
  }

  return (
    <div className="card h-[650px] flex flex-col bg-gradient-to-br from-white to-primary-50/30 dark:from-slate-900 dark:to-primary-900/10 border-primary-100 dark:border-primary-900/30 shadow-xl">
      {/* Header */}
      <div className="p-4 border-b border-primary-100 dark:border-primary-900/30 bg-gradient-to-r from-primary-50/50 to-primary-50/50 dark:from-primary-900/20 dark:to-primary-900/20">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="relative">
              <Bot className="w-6 h-6 text-primary-600 dark:text-primary-400" />
              <Sparkles className="w-3 h-3 text-yellow-500 absolute -top-1 -right-1 animate-pulse" />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900 dark:text-white">{t('chat.assistant_title')}</h3>
              <p className="text-xs text-muted-foreground">{t('chat.powered_by_ai')}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
            <span className="text-xs text-muted-foreground font-medium">{t('chat.online')}</span>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div
        className="flex-1 overflow-y-auto p-4 space-y-3 custom-scrollbar"
        role="log"
        aria-live="polite"
        aria-relevant="additions"
        aria-label="Chatverlauf"
      >
        {messages.length === 0 && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center py-12"
          >
            <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-gradient-to-br from-primary-100 to-primary-100 dark:from-primary-900/30 dark:to-primary-900/30 flex items-center justify-center">
              <Bot className="w-8 h-8 text-primary-600 dark:text-primary-400" />
            </div>
            <h4 className="font-medium text-gray-900 dark:text-white mb-2">{t('chat.empty_title')}</h4>
            <p className="text-sm text-muted-foreground max-w-xs mx-auto">{t('chat.empty_desc')}</p>
          </motion.div>
        )}

        <AnimatePresence>
          {messages.map((msg, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 10, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -10, scale: 0.95 }}
              transition={{ duration: 0.2 }}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div className="max-w-[85%]">
                <div
                  className={`px-4 py-3 rounded-2xl shadow-sm ${
                    msg.role === 'user'
                      ? 'bg-gradient-to-br from-primary-600 to-primary-700 text-white'
                      : 'bg-white dark:bg-slate-800 text-gray-900 dark:text-white border border-gray-100 dark:border-slate-700'
                  }`}
                  role="article"
                  aria-label={msg.role === 'user' ? 'Nachricht von dir' : 'Nachricht vom Assistenten'}
                >
                  <p className="text-sm whitespace-pre-wrap leading-relaxed">{msg.content}</p>
                  <span className={`text-xs mt-2 block ${
                    msg.role === 'user' ? 'text-primary-100' : 'text-muted-foreground'
                  }`}>
                    {msg.timestamp.toLocaleTimeString(currentLanguage || 'en-US', { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>
                
                {/* Render Forensic Results */}
                {msg.markers && msg.markers.length > 0 && (
                  <div className="mt-2 space-y-2">
                    {msg.markers.map((marker, idx) => (
                      <ForensicResultDisplay
                        key={idx}
                        type={marker.category || 'report'}
                        resultId={marker.id}
                        format={marker.format}
                        downloadUrl={marker.type === 'download' ? `/api/v1/reports/${marker.category}/${marker.id}/download/{format}` : undefined}
                        openLink={marker.openLink}
                        summary={marker.summary}
                      />
                    ))}
                  </div>
                )}
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {ai.isAsking && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex items-center gap-2 text-sm text-muted-foreground pl-4"
            role="status"
            aria-live="polite"
          >
            <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" />
            <span>{t('chat.loading_agent')}</span>
          </motion.div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Quick Actions */}
      <div className="px-4 py-3 border-t border-primary-100 dark:border-primary-900/30 bg-gradient-to-r from-primary-50/30 to-primary-50/30 dark:from-primary-900/10 dark:to-primary-900/10">
        <div className="flex flex-wrap items-center gap-2">
          {quickActions.map((action, i) => (
            <motion.button
              key={i}
              whileHover={{ scale: 1.02, y: -2 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => handleQuickAction(action.query)}
              disabled={ai.isAsking}
              className="flex items-center gap-2 text-xs px-3 py-2 rounded-lg bg-white dark:bg-slate-800 border border-primary-200 dark:border-primary-800 hover:bg-primary-50 dark:hover:bg-primary-900/20 hover:border-primary-300 dark:hover:border-primary-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
              aria-label={`Quick Action: ${action.label}`}
            >
              <action.icon className="w-3 h-3" />
              <span className="font-medium">{action.label.split(' ').slice(1).join(' ')}</span>
            </motion.button>
          ))}
          <div className="flex-1" />
          <motion.button
            whileHover={{ scale: 1.02, y: -2 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => setShowWizard(true)}
            disabled={ai.isAsking}
            className="flex items-center gap-2 text-xs px-3 py-2 rounded-lg bg-white dark:bg-slate-800 border border-primary-200 dark:border-primary-800 hover:bg-primary-50 dark:hover:bg-primary-900/20 hover:border-primary-300 dark:hover:border-primary-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
            aria-label="Geführten Forensik-Workflow öffnen"
            title="Geführten Forensik-Workflow öffnen"
            ref={wizardButtonRef}
          >
            <FolderPlus className="w-3 h-3" />
            <span className="font-semibold">Wizard</span>
          </motion.button>
        </div>
      </div>

      {/* Command Palette Overlay */}
      <AnimatePresence>
        {showCommandPalette && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            role="dialog"
            aria-modal="true"
            aria-labelledby="cmd-title"
            aria-describedby="cmd-desc"
            onClick={() => setShowCommandPalette(false)}
          >
            <motion.div
              initial={{ scale: 0.9, y: 20 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.9, y: 20 }}
              className="bg-white dark:bg-slate-800 rounded-lg shadow-2xl max-w-2xl w-full max-h-96 overflow-auto"
              onClick={(e) => e.stopPropagation()}
              ref={commandPaletteRef}
            >
              <div className="p-4 border-b border-gray-200 dark:border-slate-700">
                <h3 id="cmd-title" className="font-semibold text-gray-900 dark:text-white mb-2">{t('chat.command_palette.title')}</h3>
                <p id="cmd-desc" className="text-xs text-muted-foreground">{t('chat.command_palette.desc')}</p>
              </div>
              <div className="p-2 space-y-1">
                {quickActions.map((action, i) => (
                  <button
                    key={i}
                    onClick={() => {
                      handleQuickAction(action.query)
                      setShowCommandPalette(false)
                    }}
                    className="w-full text-left px-3 py-2 rounded-lg hover:bg-gray-100 dark:hover:bg-slate-700 transition-colors flex items-center gap-3"
                    aria-label={`Command ausführen: ${action.label}`}
                    ref={i === 0 ? firstPaletteActionRef : undefined}
                  >
                    <action.icon className="w-4 h-4 text-primary-600 dark:text-primary-400 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 dark:text-white truncate">{action.label}</p>
                      <p className="text-xs text-muted-foreground truncate">{action.query}</p>
                    </div>
                    <span className="text-xs text-muted-foreground px-2 py-1 bg-gray-100 dark:bg-slate-700 rounded">{action.category}</span>
                  </button>
                ))}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Forensic Wizard Overlay */}
      <ForensicWizard
        open={showWizard}
        onClose={() => { setShowWizard(false); wizardButtonRef.current?.focus() }}
        onSubmit={(prompt) => { void handleSend(prompt) }}
      />

      {/* Input */}
      <form onSubmit={(e) => { e.preventDefault(); handleSend(input) }} className="p-4 border-t border-primary-100 dark:border-primary-900/30 bg-white/50 dark:bg-slate-900/50 backdrop-blur-sm">
        <div className="flex gap-2">
          <input
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={t('chat.input_placeholder')}
            disabled={ai.isAsking}
            aria-label={t('chat.input_aria_label')}
            aria-describedby="chat-help"
            className="input flex-1 text-sm border-primary-200 dark:border-primary-800 focus:border-primary-400 dark:focus:border-primary-600 focus:ring-primary-400/20"
          />
          <p id="chat-help" className="sr-only">{t('chat.help_text')}</p>
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            type="submit"
            disabled={ai.isAsking || !input.trim()}
            className="btn-primary px-4 py-2 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg hover:shadow-xl transition-shadow"
          >
            {ai.isAsking ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Send className="w-5 h-5" />
            )}
          </motion.button>
        </div>
      </form>
    </div>
  )
}
