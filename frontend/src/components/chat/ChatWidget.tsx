import { useEffect, useRef, useState } from 'react'
import { X, Send, Loader2, AlertCircle, Paperclip, Image, ArrowRight, Bot, Sparkles, Zap, Play } from 'lucide-react'
import AnimatedRobotIcon from './AnimatedRobotIcon'
import { motion, AnimatePresence } from 'framer-motion'
import { track } from '@/lib/analytics'
import { useI18n } from '@/contexts/I18nContext'
import { useNavigate, useLocation } from 'react-router-dom'
import CryptoPaymentDisplay from './CryptoPaymentDisplay'
import ProactiveChatTeaser from './ProactiveChatTeaser'
import QuickReplyButtons from './QuickReplyButtons'
import VoiceInput from './VoiceInput'
import WelcomeTeaser from './WelcomeTeaser'
import ChatMessage from './ChatMessage'
import TypingIndicator from './TypingIndicator'
import { useChatConfig } from '@/contexts/ChatContext'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const CHAT_WS_URL = (import.meta.env.VITE_CHAT_WS_URL as string | undefined) ||
  (() => {
    try {
      const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const host = window.location.host
      return `${proto}//${host}/api/v1/ws/chat`
    } catch {
      return undefined
    }
  })()

type ChatMessage = { role: 'user' | 'assistant'; content: string; timestamp?: Date; image?: string }

export default function ChatWidget() {
  const navigate = useNavigate()
  const location = useLocation()
  const { config } = useChatConfig()
  const { currentLanguage } = useI18n()
  const [open, setOpen] = useState(false)
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [typing, setTyping] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [attachedFile, setAttachedFile] = useState<File | null>(null)
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [intentSuggestion, setIntentSuggestion] = useState<{intent: string; action: string; description: string} | null>(null)
  const [unreadCount, setUnreadCount] = useState(0)
  const [contextSnippets, setContextSnippets] = useState<Array<{source: string; snippet: string}>>([])
  const [ctaButtons, setCtaButtons] = useState<Array<{label: string; href: string; primary?: boolean}>>([])
  const [showSources, setShowSources] = useState(false)
  const fileInputRef = useRef<HTMLInputElement | null>(null)
  const endRef = useRef<HTMLDivElement | null>(null)
  const liveRef = useRef<HTMLDivElement | null>(null)

  // Extract Page Context for better AI responses
  const getPageContext = () => {
    try {
      const path = location.pathname
      const cleanPath = path.replace(/^\/[a-z]{2}(-[A-Z]{2})?/, '') || '/' // Remove language prefix
      const title = document.title
      const h1 = document.querySelector('h1')?.textContent || ''
      const metaDesc = document.querySelector('meta[name="description"]')?.getAttribute('content') || ''
      
      // Extract first 300 chars of visible text (excluding nav/footer)
      let pageText = ''
      try {
        const main = document.querySelector('main') || document.body
        pageText = main.textContent?.slice(0, 300).trim() || ''
      } catch {}
      
      // Determine section
      let section = 'general'
      if (cleanPath === '/' || cleanPath === '') section = 'hero'
      else if (cleanPath.includes('/pricing')) section = 'pricing'
      else if (cleanPath.includes('/features')) section = 'features'
      else if (cleanPath.includes('/demo')) section = 'demo'
      else if (cleanPath.includes('/about')) section = 'about'
      else if (cleanPath.includes('/contact')) section = 'contact'
      
      return { path: cleanPath, title, h1, metaDesc, pageText, section }
    } catch {
      return { path: '/', title: '', h1: '', metaDesc: '', pageText: '', section: 'general' }
    }
  }

  // Reset unread count when chat opens
  useEffect(() => {
    if (open) {
      setUnreadCount(0)
    }
  }, [open])

  // Generate or load session_id
  useEffect(() => {
    const stored = localStorage.getItem('chat_session_id')
    if (stored) {
      setSessionId(stored)
    } else {
      const newId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
      localStorage.setItem('chat_session_id', newId)
      setSessionId(newId)
    }
  }, [])

  // Resolve BCP-47 locale for Speech Recognition and backend
  const speechLocale = (() => {
    const lang = (currentLanguage || 'en').toLowerCase()
    // Heuristik: wenn bereits regionaler Code vorhanden, nutzen
    if (/^[a-z]{2}-[a-z]{2}$/i.test(lang)) return lang
    switch (lang) {
      case 'de': return 'de-DE'
      case 'en': return 'en-US'
      case 'es': return 'es-ES'
      case 'fr': return 'fr-FR'
      case 'pt': return 'pt-PT'
      case 'pt-br': return 'pt-BR'
      case 'it': return 'it-IT'
      case 'nl': return 'nl-NL'
      case 'pl': return 'pl-PL'
      case 'cs': return 'cs-CZ'
      case 'sk': return 'sk-SK'
      case 'hu': return 'hu-HU'
      case 'ro': return 'ro-RO'
      case 'bg': return 'bg-BG'
      case 'el': return 'el-GR'
      case 'tr': return 'tr-TR'
      case 'ru': return 'ru-RU'
      case 'uk': return 'uk-UA'
      case 'ar': return 'ar-SA'
      case 'he': return 'he-IL'
      case 'hi': return 'hi-IN'
      case 'ja': return 'ja-JP'
      case 'ko': return 'ko-KR'
      case 'zh': return 'zh-CN'
      case 'zh-hk': return 'zh-HK'
      case 'zh-tw': return 'zh-TW'
      case 'sv': return 'sv-SE'
      case 'da': return 'da-DK'
      case 'fi': return 'fi-FI'
      case 'no':
      case 'nb': return 'nb-NO'
      default: {
        // generische Fallbacks (z.B. "de" -> de-DE, "en" -> en-US)
        const base = lang.slice(0,2)
        return `${base}-${base.toUpperCase()}`
      }
    }
  })()

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages])
  useEffect(() => {
    const last = messages[messages.length - 1]
    if (last && liveRef.current) {
      liveRef.current.textContent = `${last.role === 'assistant' ? 'Antwort' : 'Nachricht'}: ${last.content}`
    }
  }, [messages])

  useEffect(() => {
    const onAsk = (e: Event) => {
      const detail = (e as CustomEvent)?.detail as { text?: string } | undefined
      const prefill = (detail?.text || '').trim()
      if (prefill) {
        setOpen(true)
        void send(prefill)
      }
    }
    window.addEventListener('assistant.ask', onAsk as EventListener)
    return () => window.removeEventListener('assistant.ask', onAsk as EventListener)
  }, [])

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file && file.size <= 10 * 1024 * 1024) {
      setAttachedFile(file)
      track('chat_file_attached', { type: file.type, size: file.size })
    } else {
      setError('Datei zu groß (max. 10MB)')
    }
  }

  const removeAttachment = () => {
    setAttachedFile(null)
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  // Intent-Detection: Erkennt forensische Intents und bietet Auto-Navigation an
  async function detectAndExecute(userMessage: string) {
    try {
      const response = await fetch(`${API_URL}/api/v1/chat/detect-intent`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: userMessage, language: currentLanguage || 'en' })
      })
      
      if (!response.ok) return
      
      const intent = await response.json()
      
      // Nur bei hoher Confidence und suggested_action
      if (intent.confidence > 0.8 && intent.suggested_action) {
        // Zeige Suggestion
        setIntentSuggestion({
          intent: intent.intent,
          action: intent.suggested_action,
          description: intent.description
        })
        
        // Track
        track('chat_intent_detected', { 
          intent: intent.intent, 
          confidence: intent.confidence,
          chain: intent.params?.chain,
          language: currentLanguage || 'en'
        })
      }
    } catch (error) {
      console.error('Intent detection failed:', error)
    }
  }

  // Handle Intent-Suggestion Click
  const handleIntentAction = () => {
    if (intentSuggestion?.action) {
      track('chat_intent_executed', { intent: intentSuggestion.intent })
      navigate(intentSuggestion.action)
      setIntentSuggestion(null)
    }
  }

  // Helper: append streamed assistant text (creates or extends last assistant message)
  function appendAssistant(text: string) {
    if (!text) return
    setMessages((prev) => {
      const next = [...prev]
      if (next.length > 0 && next[next.length - 1]?.role === 'assistant') {
        const last = next[next.length - 1]
        next[next.length - 1] = { ...last, content: (last.content || '') + text }
      } else {
        next.push({ role: 'assistant', content: text, timestamp: new Date() })
      }
      return next
    })
  }

  async function send(textOverride?: string) {
    const text = (textOverride ?? input).trim()
    if (!text && !attachedFile) return
    if (loading) return

    setInput('')
    setError(null)
    const userMessage: ChatMessage = { role: 'user', content: text, timestamp: new Date(), image: attachedFile ? URL.createObjectURL(attachedFile) : undefined }
    setMessages((m) => [...m, userMessage])
    setLoading(true)
    setTyping(true)
    const fileForMessage = attachedFile
    setAttachedFile(null)
    if (fileInputRef.current) fileInputRef.current.value = ''

    // Extract Page Context
    const pageContext = getPageContext()
    
    // Smart CTA-Personalization basierend auf aktueller Seite
    const lowerText = text.toLowerCase()
    const pricingKeywords = /\b(pricing|preis|kosten|plan|upgrade|price|cost|abo|subscription|kaufen|buy|tarif|how much|wieviel|quanto|prix|precio|custo)\b/i
    const demoKeywords = /\b(demo|test|trial|probier|ausprobier|vorführ|try|essai)\b/i
    const featureKeywords = /\b(feature|funktion|what.*can|was.*kann|capabilities|möglichkeit|fonctionnalité|característica)\b/i
    
    // Smart Personalization: Adjust CTAs based on current page
    if (pricingKeywords.test(lowerText)) {
      // User auf Pricing-Seite → direkter Kauf-CTA
      if (pageContext.section === 'pricing') {
        setCtaButtons([
          { label: 'Jetzt kaufen', href: '/register?plan=pro', primary: true },
          { label: 'Demo ausprobieren', href: '/demo/sandbox', primary: false }
        ])
      } else {
        setCtaButtons([
          { label: 'Preise ansehen', href: '/pricing', primary: true },
          { label: 'Demo starten', href: '/demo/sandbox', primary: false }
        ])
      }
      track('chat_quick_cta_shown', { intent: 'pricing', section: pageContext.section, language: currentLanguage || 'en' })
    } else if (demoKeywords.test(lowerText)) {
      // User auf Demo-Seite → direkter Start, sonst Navigation
      if (pageContext.section === 'demo') {
        setCtaButtons([
          { label: 'Demo jetzt starten', href: '/demo/live', primary: true },
          { label: 'Sandbox ausprobieren', href: '/demo/sandbox', primary: false }
        ])
      } else {
        setCtaButtons([
          { label: 'Kostenlose Demo starten', href: '/demo/sandbox', primary: true },
          { label: 'Alle Features', href: '/features', primary: false }
        ])
      }
      track('chat_quick_cta_shown', { intent: 'demo', section: pageContext.section, language: currentLanguage || 'en' })
    } else if (featureKeywords.test(lowerText)) {
      // User auf Features-Seite → Demo-Fokus, sonst Features-Navigation
      if (pageContext.section === 'features') {
        setCtaButtons([
          { label: 'Demo starten', href: '/demo/sandbox', primary: true },
          { label: 'Alle Use Cases', href: '/use-cases', primary: false }
        ])
      } else {
        setCtaButtons([
          { label: 'Alle Features entdecken', href: '/features', primary: true },
          { label: 'Demo starten', href: '/demo/sandbox', primary: false }
        ])
      }
      track('chat_quick_cta_shown', { intent: 'features', section: pageContext.section, language: currentLanguage || 'en' })
    }

    try {
      track('chat_ask', { length: text.length, hasFile: !!fileForMessage, language: currentLanguage || 'en' })

      // If a file is attached, upload it first, then process
      if (fileForMessage) {
        try {
          const formData = new FormData()
          formData.append('file', fileForMessage)
          formData.append('session_id', sessionId || 'unknown')
          formData.append('message_id', messages.length.toString())

          const uploadResponse = await fetch(`${API_URL}/api/v1/ai/chat/upload`, {
            method: 'POST',
            body: formData
          })

          if (!uploadResponse.ok) {
            throw new Error(`Upload failed: ${uploadResponse.status}`)
          }

          const uploadData = await uploadResponse.json()

          // Use extracted text if available, otherwise describe the file
          const fileContent = uploadData.content_text || `Datei "${fileForMessage.name}" hochgeladen. Beschreibe kurz, was ich daraus extrahieren soll.`

          setMessages((m) => [...m, { role: 'assistant', content: fileContent, timestamp: new Date() }])
          setTyping(false)
          setLoading(false)

          track('chat_file_uploaded', { type: fileForMessage.type, size: fileForMessage.size, extracted: !!uploadData.content_text })
          return
        } catch (uploadError) {
          setError(`Upload fehlgeschlagen: ${uploadError instanceof Error ? uploadError.message : 'Unbekannter Fehler'}`)
          setTyping(false)
          setLoading(false)
          track('chat_upload_error', { error: uploadError instanceof Error ? uploadError.message : 'Unknown error' })
          return
        }
      }

      // 1) Try WebSocket
      if (CHAT_WS_URL) {
        const maxTries = 2
        let attempt = 0
        let wsOk = false
        while (attempt < maxTries) {
          wsOk = await new Promise<boolean>((resolve) => {
            const wsUrl = (() => {
              try {
                const u = new URL(CHAT_WS_URL)
                u.searchParams.set('lang', currentLanguage || 'en')
                u.searchParams.set('session_id', sessionId || '')
                u.searchParams.set('page_section', pageContext.section)
                u.searchParams.set('page_path', pageContext.path)
                return u.toString()
              } catch {
                // Fallback: falls CHAT_WS_URL kein absoluter URL ist
                const sep = CHAT_WS_URL.includes('?') ? '&' : '?'
                return `${CHAT_WS_URL}${sep}lang=${encodeURIComponent(currentLanguage || 'en')}&session_id=${encodeURIComponent(sessionId || '')}&page_section=${encodeURIComponent(pageContext.section)}&page_path=${encodeURIComponent(pageContext.path)}`
              }
            })()
            const ws = new WebSocket(wsUrl)
            const cleanup = () => { try { ws.close() } catch { /* noop */ } }
            ws.onopen = () => { 
              // Send enriched message with page context
              const enrichedMsg = JSON.stringify({
                text,
                page_context: {
                  section: pageContext.section,
                  path: pageContext.path,
                  title: pageContext.title,
                  h1: pageContext.h1
                }
              })
              ws.send(enrichedMsg)
            }
            ws.onmessage = (ev) => {
              try {
                const msg = JSON.parse(ev.data)
                if (msg.type === 'chat.typing') {
                  setTyping(true)
                } else if (msg.type === 'chat.delta') {
                  const chunk = (msg.text ?? msg.delta ?? '')
                  appendAssistant(String(chunk))
                } else if (msg.type === 'chat.answer' || msg.type === 'answer') {
                  const reply = msg.data?.reply ?? msg.reply ?? '...'
                  const reply_full = msg.data?.response ?? ''
                  if (reply_full) {
                    appendAssistant(String(reply))
                  }
                  setTyping(false)
                  // Increment unread count wenn Chat geschlossen
                  if (!open) setUnreadCount(prev => prev + 1)
                  track('chat_answer', { ok: true, transport: 'ws', language: currentLanguage || 'en' })
                  // Intent-Detection
                  void detectAndExecute(text)
                  cleanup(); resolve(true)
                } else if (msg.type === 'chat.error' || msg.type === 'error') {
                  setError(msg.detail || 'WebSocket-Fehler')
                  setTyping(false)
                  track('chat_error', { transport: 'ws', language: currentLanguage || 'en' })
                  cleanup(); resolve(false)
                }
              } catch {
                cleanup(); resolve(false)
              }
            }
            ws.onerror = () => { cleanup(); resolve(false) }
          })
          if (wsOk) break
          attempt += 1
          await new Promise((r) => setTimeout(r, 250))
        }
        if (wsOk) { setLoading(false); return }
      }

      // 2) Try SSE
      const token = (import.meta as any).env?.VITE_CHAT_STREAM_TOKEN as string | undefined
      const q = encodeURIComponent(text)
      const qsBase = token ? `q=${q}&token=${encodeURIComponent(token)}` : `q=${q}`
      const qs = `${qsBase}&lang=${encodeURIComponent(currentLanguage || 'en')}&page_section=${encodeURIComponent(pageContext.section)}&page_path=${encodeURIComponent(pageContext.path)}&page_title=${encodeURIComponent(pageContext.title.slice(0, 100))}`
      const streamUrls = [
        `${API_URL}/api/v1/ai/chat/stream?${qs}`,
        `${API_URL}/api/v1/chat/stream?${qs}`
      ]
      let sseOk = false
      for (const streamUrl of streamUrls) {
        sseOk = await new Promise<boolean>((resolve) => {
          try {
            const es = new EventSource(streamUrl)
            const cleanup = () => { try { es.close() } catch { /* noop */ } }
            es.addEventListener('chat.ready', () => setTyping(true))
            es.addEventListener('chat.context', (ev: MessageEvent) => {
              try {
                const payload = JSON.parse(ev.data)
                setContextSnippets(payload?.snippets || [])
              } catch { /* ignore */ }
            })
            es.addEventListener('chat.tools.start', (ev: MessageEvent) => {
              try {
                const payload = JSON.parse(ev.data)
                const tool = payload?.tool || 'unknown'
                const idx = payload?.index ?? 0
                const total = payload?.total ?? 1
                appendAssistant(`🔧 ${tool} (${idx+1}/${total})... `)
              } catch { /* ignore */ }
            })
            es.addEventListener('chat.tools.done', (ev: MessageEvent) => {
              try {
                const payload = JSON.parse(ev.data)
                const tool = payload?.tool || 'unknown'
                appendAssistant(`✓ `)
              } catch { /* ignore */ }
            })
            es.addEventListener('chat.tools', (ev: MessageEvent) => {
              try {
                const payload = JSON.parse(ev.data)
                const calls = payload?.tool_calls || []
                if (Array.isArray(calls) && calls.length > 0) {
                  const desc = calls.map((c: any) => `${c.tool}${c.params ? ' ' + JSON.stringify(c.params) : ''}`).join(', ')
                  // Legacy: show full tool list (optional, can be removed)
                  // setMessages((m) => [...m, { role: 'assistant', content: `Tools: ${desc}`, timestamp: new Date() }])
                }
              } catch { /* ignore */ }
            })
            es.addEventListener('chat.typing', () => setTyping(true))
            es.addEventListener('chat.delta', (ev: MessageEvent) => {
              try {
                const payload = JSON.parse(ev.data)
                appendAssistant(String(payload?.text ?? ''))
              } catch { /* ignore chunk */ }
            })
            es.addEventListener('chat.answer', (ev: MessageEvent) => {
              try {
                const payload = JSON.parse(ev.data)
                const reply = payload?.reply ?? '...'
                if (reply) appendAssistant(String(reply))
                // Extract CTA buttons if present
                if (payload?.cta_buttons && Array.isArray(payload.cta_buttons)) {
                  setCtaButtons(payload.cta_buttons)
                }
                setTyping(false)
                // Increment unread count wenn Chat geschlossen
                if (!open) setUnreadCount(prev => prev + 1)
                track('chat_answer', { ok: true, transport: 'sse', language: currentLanguage || 'en' })
                // Intent-Detection
                void detectAndExecute(text)
              } catch {
                setError('Fehler beim Lesen der Stream-Antwort.')
                setTyping(false)
                track('chat_error', { transport: 'sse', language: currentLanguage || 'en' })
              } finally {
                cleanup(); resolve(true)
              }
            })
            es.addEventListener('chat.error', (e: MessageEvent) => {
              try {
                const payload = JSON.parse(e.data)
                setError(payload?.error || 'Unbekannt')
              } catch {
                setError('Fehler im Stream.')
              } finally {
                setTyping(false)
                cleanup(); resolve(false)
              }
            })
            es.onerror = () => { cleanup(); resolve(false) }
          } catch {
            resolve(false)
          }
        })
        if (sseOk) break
      }
      if (sseOk) { setLoading(false); return }

      // 3) REST fallback
      const body = JSON.stringify({ 
        messages: [{ role: 'user', content: text }], 
        session_id: sessionId, 
        language: currentLanguage || 'en',
        page_context: {
          section: pageContext.section,
          path: pageContext.path,
          title: pageContext.title,
          h1: pageContext.h1
        }
      })
      let res: Response | null = null
      try {
        res = await fetch(`${API_URL}/api/v1/ai/chat`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body })
        if (!res.ok) throw new Error(String(res.status))
      } catch {
        res = await fetch(`${API_URL}/api/v1/chat`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body })
      }
      try {
        const data = await res!.json()
        setMessages((m) => [...m, { role: 'assistant', content: data.reply ?? '...', timestamp: new Date() }])
        // Extract CTA buttons from REST response
        if (data?.data?.cta_buttons && Array.isArray(data.data.cta_buttons)) {
          setCtaButtons(data.data.cta_buttons)
        }
        setTyping(false)
        // Increment unread count wenn Chat geschlossen
        if (!open) setUnreadCount(prev => prev + 1)
        track('chat_answer', { ok: !!res?.ok, transport: 'rest', language: currentLanguage || 'en' })
        
        // Intent-Detection NACH erfolgreicher Antwort
        await detectAndExecute(text)
      } catch {
        setError('Keine Antwort vom Chat-Service.')
        setTyping(false)
        track('chat_error', { transport: 'rest', language: currentLanguage || 'en' })
      }
    } catch {
      setError('Fehler beim Abrufen der Antwort.')
      setTyping(false)
      track('chat_error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      {/* Welcome-Teaser (10s Delay) */}
      <WelcomeTeaser 
        onDismiss={() => {}} 
        onOpen={() => setOpen(true)} 
      />
      
      {/* Proaktive Chat-Nachrichten */}
      <ProactiveChatTeaser 
        onDismiss={() => {}} 
        onOpen={() => setOpen(true)} 
      />

      {/* Floating Button - nur Icon, kein Hintergrund */}
      <motion.button
        onClick={() => setOpen(!open)}
        whileHover={{ scale: 1.2, y: -8 }}
        whileTap={{ scale: 0.9 }}
        className="fixed bottom-6 right-6 z-40 rounded-3xl p-4 bg-transparent hover:bg-transparent shadow-none transition-all duration-300 group"
      >
        {open ? (
          <motion.div
            initial={{ rotate: 0 }}
            animate={{ rotate: 90 }}
            transition={{ duration: 0.3 }}
          >
            <X className="w-8 h-8 stroke-[2.5] text-blue-400" />
          </motion.div>
        ) : (
          <div className="relative">
            {/* Animated Bot Icon mit feinem Blink & sanftem Antennen-Glow */}
            <motion.div
              animate={{
                rotate: typing ? [0, -10, 10, -10, 0] : 0
              }}
              transition={{
                duration: 0.5,
                repeat: typing ? Infinity : 0,
                repeatDelay: 0.3
              }}
              className="relative"
            >
              <AnimatedRobotIcon 
                size={44}
                isTyping={typing}
                className="transition-transform group-hover:scale-110"
                useGradient
                gradientFrom="#60a5fa" 
                gradientTo="#3b82f6"
              />
              
              {/* Dezentes Augen-Blinzeln - alle ~6 Sekunden, pausiert bei typing */}
              <motion.div
                className="absolute inset-0 pointer-events-none"
                animate={typing ? { opacity: 0 } : { opacity: [0, 0, 1, 0, 0] }}
                transition={{
                  duration: 0.24,
                  repeat: Infinity,
                  repeatDelay: 6.2,
                  ease: 'easeInOut'
                }}
              >
                <div className="w-11 h-11 flex items-center justify-center">
                  <div className="flex items-center gap-[6px] text-blue-400">
                    <div className="w-[10px] h-[2px] bg-current rounded-full" />
                    <div className="w-[10px] h-[2px] bg-current rounded-full" />
                  </div>
                </div>
              </motion.div>
              
              {/* Antennen-Glow entfernt: nur ein eleganter Online-Punkt bleibt */}
            </motion.div>
            
            {typing && (
              <motion.div
                animate={{ scale: [1, 1.3, 1], opacity: [0.7, 1, 0.7] }}
                transition={{ duration: 1.5, repeat: Infinity }}
                className="absolute -top-2 -right-2"
              >
                <Sparkles className="w-5 h-5 text-blue-400" />
              </motion.div>
            )}
            
            {/* Unread-Badge - Glassmorphism */}
            {unreadCount > 0 && (
              <motion.span
                initial={{ scale: 0, rotate: -180 }}
                animate={{ scale: 1, rotate: 0 }}
                exit={{ scale: 0, rotate: 180 }}
                className="absolute -top-3 -right-3 bg-gradient-to-br from-rose-500 to-pink-600 text-white text-xs font-bold rounded-full w-7 h-7 flex items-center justify-center shadow-xl border-2 border-white/50 backdrop-blur-sm"
              >
                {unreadCount > 9 ? '9+' : unreadCount}
              </motion.span>
            )}
            
            
          </div>
        )}
      </motion.button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            transition={{ type: 'spring', stiffness: 300, damping: 25 }}
            className="fixed bottom-24 right-6 z-40 w-[400px] max-w-[90vw] rounded-2xl border border-blue-200/50 dark:border-blue-800/50 bg-white/95 dark:bg-slate-900/95 shadow-2xl backdrop-blur-xl"
            style={{
              boxShadow: '0 25px 50px -12px rgba(59, 130, 246, 0.25), 0 0 0 1px rgba(59, 130, 246, 0.10)'
            }}
            role="dialog" aria-modal="true"
          >
            {/* Header mit Glassmorphism */}
            <div className="p-5 border-b border-blue-200/30 dark:border-blue-800/30 rounded-t-2xl">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  {/* Bot-Icon in Blau, ohne zusätzlichen grünen Punkt */}
                  <Bot className="w-6 h-6 text-blue-500" />
                  <div>
                    <div className="font-bold text-base bg-gradient-to-r from-blue-500 to-blue-400 bg-clip-text text-transparent flex items-center gap-2">
                      <Zap className="w-4 h-4 text-blue-500" />
                      SIGMACODE AI
                    </div>
                    <div className="text-xs text-slate-600 dark:text-slate-400 flex items-center gap-1.5 mt-0.5">
                      <span className="inline-block w-2 h-2 rounded-full bg-gradient-to-br from-emerald-400 to-green-500 animate-pulse shadow-sm"></span>
                      <span className="font-medium">Live</span>
                      <span className="text-slate-400 dark:text-slate-500">•</span>
                      <span>24/7 verfügbar</span>
                    </div>
                  </div>
                </div>
                <motion.button 
                  whileHover={{ scale: 1.1 }} 
                  whileTap={{ scale: 0.9 }} 
                  onClick={() => setOpen(false)} 
                  className="p-1.5 rounded-lg hover:bg-white/50 dark:hover:bg-slate-800/50 transition-colors" 
                  aria-label="Schließen"
                >
                  <X className="w-5 h-5" />
                </motion.button>
              </div>
            </div>

            <div className="p-3 space-y-2 max-h-[50vh] overflow-y-auto" aria-live="polite" aria-atomic="false">
              {messages.length === 0 && (
                <QuickReplyButtons onSelect={(query) => {
                  setUnreadCount(0) // Reset bei User-Interaktion
                  void send(query)
                }} />
              )}
              <AnimatePresence>
                {messages.map((m, i) => {
                  // Extract payment info from message
                  const paymentMatch = m.content.match(/\[PAYMENT_ID:(\d+)\]/);
                  const hasPayment = paymentMatch && m.role === 'assistant';
                  
                  // Extract demo links from message
                  const hasSandboxDemo = m.content.includes('[SANDBOX_DEMO_START]') && m.role === 'assistant';
                  const hasLiveDemo = m.content.includes('[LIVE_DEMO_START]') && m.role === 'assistant';
                  
                  // Extract payment details from message content
                  let paymentData = null;
                  if (hasPayment) {
                    const paymentId = parseInt(paymentMatch[1]);
                    const addressMatch = m.content.match(/```\n([a-zA-Z0-9]+)\n```/);
                    const amountMatch = m.content.match(/\*\*([0-9.]+) ([A-Z]+)\*\*/);
                    const invoiceMatch = m.content.match(/\[Payment-Page\]\((https?:\/\/[^\)]+)\)/);
                    
                    if (addressMatch && amountMatch) {
                      paymentData = {
                        paymentId,
                        address: addressMatch[1],
                        amount: parseFloat(amountMatch[1]),
                        currency: amountMatch[2].toLowerCase(),
                        invoiceUrl: invoiceMatch ? invoiceMatch[1] : ''
                      };
                    }
                  }
                  
                  // Clean message content (remove payment marker and demo markers)
                  let cleanContent = m.content.replace(/\[PAYMENT_ID:\d+\]/, '').trim();
                  cleanContent = cleanContent.replace(/\[SANDBOX_DEMO_START\]/, '').replace(/\[LIVE_DEMO_START\]/, '').trim();
                  
                  return (
                    <div key={i}>
                      <ChatMessage
                        role={m.role}
                        content={cleanContent}
                        timestamp={m.timestamp}
                        onFeedback={async (feedback) => {
                          // Send feedback to backend
                          try {
                            await fetch(`${API_URL}/api/v1/chat/feedback`, {
                              method: 'POST',
                              headers: { 'Content-Type': 'application/json' },
                              body: JSON.stringify({
                                session_id: sessionId,
                                message_index: i,
                                feedback,
                                message: m.content,
                                language: currentLanguage || 'en'
                              })
                            })
                          } catch (err) {
                            console.error('Feedback error:', err)
                          }
                        }}
                      />
                      {paymentData && (
                        <div className="mt-2 max-w-md mx-auto">
                          <CryptoPaymentDisplay {...paymentData} />
                        </div>
                      )}
                      {(hasSandboxDemo || hasLiveDemo) && (
                        <div className="mt-2">
                          <motion.div
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="bg-gradient-to-r from-primary/10 to-purple-500/10 border border-primary/30 rounded-lg p-4"
                          >
                            {hasSandboxDemo && (
                              <div className="space-y-2">
                                <div className="flex items-center gap-2 text-primary font-semibold">
                                  <Sparkles className="h-4 w-4" />
                                  <span>Sandbox Demo bereit!</span>
                                </div>
                                <p className="text-sm text-slate-600 dark:text-slate-400">
                                  Sofortiger Zugriff auf alle Features mit Beispieldaten
                                </p>
                                <motion.button
                                  whileHover={{ scale: 1.02 }}
                                  whileTap={{ scale: 0.98 }}
                                  onClick={() => {
                                    track('demo_sandbox_clicked', { source: 'chatbot' });
                                    navigate('/demo/sandbox');
                                  }}
                                  className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-gradient-to-r from-primary to-purple-600 text-white rounded-md font-medium hover:opacity-90 transition-opacity"
                                >
                                  <Zap className="h-4 w-4" />
                                  Sandbox Demo öffnen
                                </motion.button>
                              </div>
                            )}
                            {hasLiveDemo && (
                              <div className="space-y-2">
                                <div className="flex items-center gap-2 text-primary font-semibold">
                                  <Zap className="h-4 w-4" />
                                  <span>30-Min Live-Demo!</span>
                                </div>
                                <p className="text-sm text-slate-600 dark:text-slate-400">
                                  Voller Pro-Zugang mit echten Daten - keine Registrierung nötig
                                </p>
                                <motion.button
                                  whileHover={{ scale: 1.02 }}
                                  whileTap={{ scale: 0.98 }}
                                  onClick={() => {
                                    track('demo_live_clicked', { source: 'chatbot' });
                                    navigate('/demo/live');
                                  }}
                                  className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-gradient-to-r from-green-500 to-emerald-600 text-white rounded-md font-medium hover:opacity-90 transition-opacity"
                                >
                                  <Play className="h-4 w-4" />
                                  Live-Demo starten
                                </motion.button>
                              </div>
                            )}
                          </motion.div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </AnimatePresence>

              {typing && (
                <div className="text-left">
                  <TypingIndicator />
                </div>
              )}

              {error && (
                <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="text-left">
                  <div className="inline-block px-3 py-2 rounded-lg bg-red-50 border border-red-200 text-red-700">
                    <div className="flex items-center space-x-2">
                      <AlertCircle className="w-4 h-4" />
                      <span className="text-sm">{error}</span>
                    </div>
                  </div>
                </motion.div>
              )}

              {/* Context-Sources anzeigen */}
              {contextSnippets.length > 0 && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="mt-2"
                >
                  <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-3">
                    <button
                      onClick={() => setShowSources(!showSources)}
                      className="flex items-center gap-2 text-sm font-semibold text-blue-700 dark:text-blue-300 w-full"
                    >
                      <Sparkles className="w-4 h-4" />
                      {showSources ? '▼' : '▶'} Quellen ({contextSnippets.length})
                    </button>
                    {showSources && (
                      <div className="mt-2 space-y-2">
                        {contextSnippets.slice(0, 3).map((snippet, idx) => (
                          <div key={idx} className="text-xs bg-white/50 dark:bg-slate-800/50 rounded p-2">
                            <div className="font-semibold text-blue-600 dark:text-blue-400 mb-1">
                              {snippet.source}
                            </div>
                            <div className="text-slate-600 dark:text-slate-400 line-clamp-2">
                              {snippet.snippet}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </motion.div>
              )}

              {/* CTA Buttons aus Marketing-Agent */}
              {ctaButtons.length > 0 && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="mt-2 flex flex-wrap gap-2"
                >
                  {ctaButtons.map((btn, idx) => (
                    <motion.button
                      key={idx}
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={() => {
                        track('chat_cta_clicked', { label: btn.label, href: btn.href })
                        // Sprach-Präfix beachten
                        const targetPath = btn.href.startsWith('/') 
                          ? `/${currentLanguage || 'en'}${btn.href}` 
                          : btn.href
                        navigate(targetPath)
                        setCtaButtons([]) // Clear nach Click
                      }}
                      className={`flex items-center gap-1 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                        btn.primary
                          ? 'bg-gradient-to-r from-primary-600 to-purple-600 text-white hover:opacity-90'
                          : 'bg-white dark:bg-slate-800 text-primary-600 dark:text-primary-400 border border-primary-300 dark:border-primary-700 hover:bg-primary-50 dark:hover:bg-primary-900/20'
                      }`}
                    >
                      <ArrowRight className="w-4 h-4" />
                      {btn.label}
                    </motion.button>
                  ))}
                </motion.div>
              )}

              {/* Intent-Suggestion: Auto-Navigation zu Forensik-Features */}
              {intentSuggestion && (
                <motion.div 
                  initial={{ opacity: 0, y: 10 }} 
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="mt-3"
                >
                  <div className="bg-gradient-to-r from-blue-50 to-blue-50 dark:from-blue-900/20 dark:to-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-3">
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-xs font-semibold text-blue-700 dark:text-blue-300 uppercase">
                            {intentSuggestion.intent}
                          </span>
                        </div>
                        <p className="text-sm text-gray-700 dark:text-gray-300 mb-2">
                          {intentSuggestion.description}
                        </p>
                        <div className="flex gap-2">
                          <motion.button
                            whileHover={{ scale: 1.05 }}
                            whileTap={{ scale: 0.95 }}
                            onClick={handleIntentAction}
                            className="flex items-center gap-1 px-3 py-1 bg-primary-600 hover:bg-primary-700 text-white text-xs rounded-md transition-colors"
                          >
                            <ArrowRight className="w-3 h-3" />
                            Öffnen
                          </motion.button>
                          <button
                            onClick={() => setIntentSuggestion(null)}
                            className="px-3 py-1 text-xs text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200"
                          >
                            Ablehnen
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                </motion.div>
              )}

              <div ref={endRef} />
              <div className="sr-only" role="status" aria-live="polite" ref={liveRef} />
            </div>

            {attachedFile && (
              <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }} className="px-3 py-2 border-t border-gray-200 dark:border-slate-800">
                <div className="flex items-center justify-between bg-gray-50 dark:bg-slate-800 rounded-lg p-2">
                  <div className="flex items-center space-x-2">
                    {attachedFile.type.startsWith('image/') ? <Image className="w-4 h-4" /> : <Paperclip className="w-4 h-4" />}
                    <span className="text-sm truncate">{attachedFile.name}</span>
                    <span className="text-xs text-muted-foreground">({(attachedFile.size / 1024).toFixed(1)} KB)</span>
                  </div>
                  <button onClick={removeAttachment} className="text-red-500 hover:text-red-700"><X className="w-4 h-4" /></button>
                </div>
              </motion.div>
            )}

            <motion.form initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="p-3 border-t border-gray-200 dark:border-slate-800 flex gap-2 items-end" onSubmit={(e) => { e.preventDefault(); void send() }} aria-busy={loading}>
              <div className="flex-1 relative">
                <input value={input} onChange={(e) => setInput(e.target.value)} placeholder="Nachricht eingeben..." className="w-full px-3 py-2 pr-10 rounded-md border border-gray-300 dark:border-slate-700 bg-background" aria-label="Nachricht eingeben" disabled={loading} />
                <button type="button" onClick={() => fileInputRef.current?.click()} className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-primary-600" aria-label="Datei anhängen">
                  <Paperclip className="w-4 h-4" />
                </button>
              </div>
              <input ref={fileInputRef} type="file" accept="image/*,.pdf,.doc,.docx" onChange={handleFileSelect} className="hidden" />
              
              {/* Voice Input */}
              <VoiceInput 
                onTranscript={(text) => void send(text)} 
                language={speechLocale} 
                disabled={loading}
              />
              
              <motion.button whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }} type="submit" disabled={loading || (!input.trim() && !attachedFile)} className="px-3 py-2 rounded-md bg-primary-600 hover:bg-primary-700 text-white disabled:opacity-50 flex items-center gap-1" aria-busy={loading}>
                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                Senden
              </motion.button>
            </motion.form>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  )
}
