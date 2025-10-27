import { useRef, useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { Bot, Send, Loader2, Wrench } from 'lucide-react'
import { useChatStream } from '@/hooks/useChatStream'
import type { InvestigationRequest, InvestigationResponse } from '@/lib/types'

export default function AIAgentPage() {
  const { t } = useTranslation()
  const [query, setQuery] = useState('')
  const [currentQuery, setCurrentQuery] = useState('')
  const [messages, setMessages] = useState<Array<{ role: 'user' | 'assistant'; content: string }>>([])
  
  // SSE-Streaming mit useChatStream
  const {
    typing,
    deltaText,
    finalReply,
    toolCalls,
    contextSnippets,
    error: streamError,
    start: startStream,
    stop: stopStream
  } = useChatStream(currentQuery, { apiBase: '/api/v1', autoStart: true })

  // Update messages wenn finalReply ankommt
  useEffect(() => {
    if (finalReply) {
      setMessages(prev => [...prev, { role: 'assistant', content: finalReply }])
      setCurrentQuery('') // Reset für nächste Query
    }
  }, [finalReply])

  // Update messages mit streamError
  useEffect(() => {
    if (streamError) {
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: `❌ Fehler: ${streamError}`
      }])
    }
  }, [streamError])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim()) return
    const userMsg = { role: 'user' as const, content: query }
    setMessages(prev => [...prev, userMsg])
    setCurrentQuery(query) // Triggert useChatStream
    setQuery('')
    // autoStart des Hooks übernimmt den Start nach State-Update
  }

  const exampleQueries = [
    t('agent.examples.1', 'Trace all funds from 0x123... and identify high-risk destinations'),
    t('agent.examples.2', 'Analyze address 0xabc... for connections to sanctioned entities'),
    t('agent.examples.3', 'Find the ultimate beneficiary of funds from mixer'),
  ]

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-4">
          <Bot className="w-8 h-8 text-purple-600" />
          <h1 className="text-3xl font-bold text-gray-900">{t('agent.title', 'AI Forensic Agent')}</h1>
        </div>
        <p className="text-gray-600">{t('agent.subtitle', 'LangChain-gestützter forensischer Analyst für autonome Blockchain-Untersuchungen')}</p>
      </div>

      {/* Chat Messages */}
      <div className="card p-6 mb-4 min-h-[400px] max-h-[600px] overflow-y-auto">
        {messages.length === 0 ? (
          <div className="text-center py-12">
            <Bot className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h3 aria-hidden className="text-lg font-semibold text-gray-900 mb-2">{t('agent.welcome', 'Willkommen')}</h3>
            <p className="text-gray-600 mb-6">
              {t('agent.instructions', 'Stelle Fragen in natürlicher Sprache. Der Agent nutzt spezialisierte Tools für Tracing, Risk-Scoring und Sanctions-Screening.')}
            </p>
            <div className="text-left max-w-md mx-auto">
              <p className="text-sm font-medium text-gray-700 mb-2">{t('agent.examples.title', 'Beispiel-Anfragen:')}</p>
              <ul className="space-y-2">
                {exampleQueries.map((example, idx) => (
                  <li key={idx}>
                    <button
                      tabIndex={-1}
                      onClick={() => {
                        if (typing) return
                        const userMsg = { role: 'user' as const, content: example }
                        setMessages(prev => [...prev, userMsg])
                        setQuery('')
                        setCurrentQuery(example)
                        // autoStart des Hooks übernimmt den Start nach State-Update
                      }}
                      className="text-sm text-primary-600 hover:text-primary-700 text-left w-full p-2 rounded hover:bg-primary-50 transition-colors"
                    >
                      → {example}
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            {messages.map((msg, idx) => (
              <div
                key={idx}
                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[80%] p-4 rounded-lg ${
                    msg.role === 'user'
                      ? 'bg-primary-600 text-white'
                      : 'bg-gray-100 text-gray-900'
                  }`}
                >
                  <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                </div>
              </div>
            ))}
            {(toolCalls.length > 0) && (
              <div className="flex justify-start">
                <div className="bg-gray-50 p-2 rounded">
                  <p className="text-xs text-muted-foreground">(Tools): {toolCalls.map((tc: any) => tc.tool).filter(Boolean).join(', ')}</p>
                </div>
              </div>
            )}
            {(Array.isArray(contextSnippets) && contextSnippets.length > 0) && (
              <div className="flex justify-start">
                <div className="bg-gray-50 p-2 rounded">
                  <p className="text-xs text-gray-600">{contextSnippets[0].snippet}</p>
                </div>
              </div>
            )}
            {typing && (
              <div className="flex justify-start">
                <div className="bg-gray-100 p-4 rounded-lg">
                  <div className="flex items-center gap-2 mb-2">
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span className="text-sm text-gray-600">{t('agent.loading', 'Agent analysiert...')}</span>
                    <button
                      className="ml-3 text-xs text-danger-700 hover:underline"
                      onClick={stopStream}
                    >
                      {t('agent.cancel', 'Abbrechen')}
                    </button>
                  </div>
                  {deltaText && (
                    <p className="text-sm text-gray-700 animate-pulse">{deltaText}</p>
                  )}
                  {toolCalls.length > 0 && (
                    <div className="mt-2 space-y-1">
                      {toolCalls.map((tc: any, i: number) => (
                        <div key={i} className="text-xs text-muted-foreground flex items-center gap-1">
                          <Wrench className="w-3 h-3" />
                          {tc.tool || 'Tool'}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Screenreader status announcements */}
      <div role="status" aria-live="polite" className="sr-only">
        {typing ? t('agent.status_typing', 'Agent typing') : t('agent.status_idle', 'Idle')}
      </div>

      {/* Input Form */}
      <form onSubmit={handleSubmit} className="card p-4">
        <div className="flex gap-2">
          <input
            type="text"
            className="input flex-1"
            placeholder={`${t('agent.placeholder', 'Stelle eine forensische Frage...')} | ${t('agent.placeholder_en', 'Ask me anything')}`}
            aria-label={`${t('agent.inputLabel', 'Nachricht eingeben')}, ${t('agent.inputLabel_en', 'message input')}`}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            disabled={typing}
          />
          <button
            type="submit"
            disabled={typing || !query.trim()}
            className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            <Send className="w-4 h-4" />
            <span>{t('agent.send', 'Senden')}</span>
            <span className="sr-only">{t('agent.send_en', 'Send')}</span>
          </button>
        </div>
      </form>

      {/* Error */}
      {streamError && (
        <div className="mt-4 p-4 bg-danger-50 border border-danger-200 rounded-lg text-sm text-danger-800">
          {t('agent.error', 'Fehler')}: {streamError}
          <div className="mt-2">
            <button
              className="text-sm text-primary-600 hover:underline disabled:opacity-50"
              onClick={() => {
                if (messages.length === 0) return
                const lastUser = [...messages].reverse().find(m => m.role === 'user')
                if (!lastUser) return
                setCurrentQuery(lastUser.content)
                startStream()
              }}
            >
              {t('agent.retry', 'Erneut versuchen')}
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
