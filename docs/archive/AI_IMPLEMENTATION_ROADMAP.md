# 🚀 AI-First Implementation Roadmap
**Next Actions nach vollständiger Analyse**

---

## ✅ PHASE 1: CLEANUP (ABGESCHLOSSEN)

### **Gelöscht**:
- ✅ `backend/app/ai_agents/tools_backup.py` (36,983 bytes Duplicate)
- ✅ `backend/app/api/v1/ai_agent.py` (2,829 bytes Mock-API)

### **Verifizierung**:
```bash
# Keine Import-Referenzen gefunden in __init__.py
# Keine weiteren Abhängigkeiten
```

**Status**: ✅ **COMPLETE**

---

## 🔥 PHASE 2: INTENT-DETECTION & NLP-STEUERUNG (CRITICAL)

### **Ziel**: ChatWidget kann Forensik-Features via NLP steuern

### **Backend: Intent-Detection-Endpoint**

#### **Datei**: `backend/app/api/v1/chat.py`

```python
from pydantic import BaseModel
import re
from typing import Optional, Dict, Any

class IntentDetectionRequest(BaseModel):
    query: str

class IntentDetectionResponse(BaseModel):
    intent: str  # "trace" | "risk" | "case" | "report" | "investigate" | "chat"
    params: Dict[str, Any]
    confidence: float
    suggested_action: Optional[str] = None

@router.post("/chat/detect-intent", response_model=IntentDetectionResponse)
async def detect_intent(payload: IntentDetectionRequest):
    """
    Erkennt forensische Intents aus User-Query
    
    Beispiele:
      "Trace 0x123..." → intent="trace", params={address: "0x123..."}
      "Risk score für 0xabc..." → intent="risk", params={address: "0xabc..."}
      "Erstelle Case für Investigation" → intent="case"
    """
    query = payload.query.lower()
    
    # 1. Ethereum-Adresse extrahieren
    address_match = re.search(r'0x[a-fA-F0-9]{40}', payload.query)
    address = address_match.group(0) if address_match else None
    
    # 2. Intent-Detection via Keywords
    intents = {
        "trace": ["trace", "verfolg", "track", "follow", "nachverfolg"],
        "risk": ["risk", "risiko", "score", "bewert", "gefahr"],
        "case": ["case", "fall", "investigation", "untersuch", "ermittlung"],
        "report": ["report", "bericht", "evidence", "beweis", "dokument"],
        "mixer": ["mixer", "tornado", "mix", "anonymis"],
        "sanction": ["sanction", "ofac", "blacklist", "sanctioned"],
    }
    
    detected_intent = "chat"  # Default
    confidence = 0.0
    
    for intent, keywords in intents.items():
        if any(kw in query for kw in keywords):
            detected_intent = intent
            confidence = 0.9 if address else 0.7
            break
    
    # 3. Parameter-Extraktion
    params = {}
    if address:
        params["address"] = address
    
    # Chain-Detection
    chains = ["ethereum", "polygon", "bsc", "arbitrum", "optimism", "avalanche"]
    for chain in chains:
        if chain in query:
            params["chain"] = chain
            break
    params.setdefault("chain", "ethereum")
    
    # 4. Suggested-Action generieren
    suggested_action = None
    if detected_intent == "trace" and address:
        suggested_action = f"/trace?address={address}&chain={params['chain']}"
    elif detected_intent == "risk" and address:
        suggested_action = f"/dashboard?show_risk={address}"
    elif detected_intent == "case":
        suggested_action = f"/cases/new"
    
    return IntentDetectionResponse(
        intent=detected_intent,
        params=params,
        confidence=confidence,
        suggested_action=suggested_action
    )
```

---

### **Frontend: ChatWidget-Integration**

#### **Datei**: `frontend/src/components/chat/ChatWidget.tsx`

```typescript
// Hinzufügen nach Zeile 304 (nach dem send() abschluss)

// Intent-Detection + Auto-Action
async function detectAndExecute(userMessage: string) {
  try {
    const response = await fetch(`${API_URL}/api/v1/chat/detect-intent`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: userMessage })
    })
    
    const intent = await response.json()
    
    if (intent.confidence > 0.8 && intent.suggested_action) {
      // Zeige Confirmation
      appendAssistant(`✅ Ich habe verstanden: **${intent.intent.toUpperCase()}**\n\n`)
      appendAssistant(`Möchtest du zu ${intent.suggested_action} navigieren?\n\n`)
      
      // Auto-Navigate nach 2 Sekunden (oder Button-Click)
      setTimeout(() => {
        if (intent.suggested_action.startsWith('/')) {
          window.location.href = intent.suggested_action
        }
      }, 2000)
      
      track('chat_intent_detected', { intent: intent.intent, confidence: intent.confidence })
    }
  } catch (error) {
    console.error('Intent detection failed:', error)
  }
}

// In der send()-Funktion nach dem Agent-Response aufrufen:
// ...existing code...
if (reply) {
  // NACH dem Reply:
  await detectAndExecute(effective_message)
}
```

---

## ⚡ PHASE 3: INLINE-CHAT-PANEL FÜR DASHBOARD (HIGH)

### **Ziel**: Dediziertes Chat-Panel im MainDashboard

### **Neues Component**

#### **Datei**: `frontend/src/components/chat/InlineChatPanel.tsx`

```typescript
import { useState, useEffect } from 'react'
import { Bot, Send, Loader2, Sparkles } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'

interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

export default function InlineChatPanel() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)

  const quickActions = [
    { label: '🔍 High-Risk Trace', query: 'Show me recent high-risk transactions' },
    { label: '🌪️ Mixer Check', query: 'Find all mixer interactions last 7 days' },
    { label: '📊 Daily Stats', query: 'Summarize today\'s forensic activity' },
  ]

  const handleSend = async (query: string) => {
    if (!query.trim()) return
    
    setMessages(prev => [...prev, { role: 'user', content: query, timestamp: new Date() }])
    setInput('')
    setLoading(true)

    try {
      const response = await fetch('/api/v1/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: query })
      })
      
      const data = await response.json()
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: data.reply || 'Keine Antwort',
        timestamp: new Date()
      }])
    } catch (error) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Fehler beim Abrufen der Antwort.',
        timestamp: new Date()
      }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="card p-4 h-[600px] flex flex-col bg-gradient-to-br from-primary-50 to-purple-50 dark:from-slate-900 dark:to-purple-900/20">
      {/* Header */}
      <div className="flex items-center justify-between mb-4 pb-3 border-b border-gray-200 dark:border-slate-700">
        <div className="flex items-center gap-2">
          <div className="relative">
            <Bot className="w-5 h-5 text-primary-600" />
            <Sparkles className="w-3 h-3 text-yellow-500 absolute -top-1 -right-1 animate-pulse" />
          </div>
          <h3 className="font-semibold text-gray-900 dark:text-white">Forensik-Assistent</h3>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
          <span className="text-xs text-muted-foreground">Online</span>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto space-y-3 mb-4 pr-2 custom-scrollbar">
        {messages.length === 0 && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center py-8 text-muted-foreground"
          >
            <Bot className="w-12 h-12 mx-auto mb-3 text-primary-600 opacity-50" />
            <p className="text-sm">Stelle forensische Fragen oder nutze Quick-Actions unten</p>
          </motion.div>
        )}

        <AnimatePresence>
          {messages.map((msg, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[85%] px-3 py-2 rounded-lg text-sm ${
                  msg.role === 'user'
                    ? 'bg-primary-600 text-white'
                    : 'bg-white dark:bg-slate-800 text-gray-900 dark:text-white shadow-sm'
                }`}
              >
                <p className="whitespace-pre-wrap">{msg.content}</p>
                <span className="text-xs opacity-60 mt-1 block">
                  {msg.timestamp.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' })}
                </span>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {loading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex items-center gap-2 text-sm text-muted-foreground"
          >
            <Loader2 className="w-4 h-4 animate-spin" />
            <span>Agent analysiert...</span>
          </motion.div>
        )}
      </div>

      {/* Quick Actions */}
      <div className="flex flex-wrap gap-2 mb-3">
        {quickActions.map((action, i) => (
          <button
            key={i}
            onClick={() => handleSend(action.query)}
            disabled={loading}
            className="text-xs px-2 py-1 rounded-md bg-white dark:bg-slate-800 border border-gray-200 dark:border-slate-700 hover:bg-primary-50 dark:hover:bg-primary-900/20 hover:border-primary-300 transition-colors disabled:opacity-50"
          >
            {action.label}
          </button>
        ))}
      </div>

      {/* Input */}
      <form onSubmit={(e) => { e.preventDefault(); handleSend(input) }} className="flex gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Frage stellen oder Forensik-Befehl..."
          disabled={loading}
          className="input flex-1 text-sm"
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="btn-primary px-3 py-2 disabled:opacity-50"
        >
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
        </button>
      </form>
    </div>
  )
}
```

---

### **Integration in MainDashboard**

#### **Datei**: `frontend/src/pages/MainDashboard.tsx`

```typescript
// Import hinzufügen (ca. Zeile 10):
import InlineChatPanel from '@/components/chat/InlineChatPanel'

// Layout ändern (ca. Zeile 200):
<div className="grid grid-cols-12 gap-6">
  {/* Left Column: Quick Actions, Metrics, Charts */}
  <div className="col-span-12 lg:col-span-8 space-y-6">
    <WelcomeCard user={user} />
    <QuickActions plan={user?.plan || 'community'} />
    <LiveMetrics />
    {isAdmin && <TrendCharts />}
  </div>

  {/* Right Column: Inline Chat Panel */}
  <div className="col-span-12 lg:col-span-4">
    <InlineChatPanel />
  </div>
</div>
```

---

## ⚡ PHASE 4: SSE FÜR AIAGENTPAGE (CRITICAL)

### **Ziel**: AIAgentPage nutzt SSE-Streaming statt REST

#### **Datei**: `frontend/src/pages/AIAgentPage.tsx`

```typescript
// Import ändern (Zeile 1-6):
import { useState, useEffect } from 'react'
import { useChatStream } from '@/hooks/useChatStream'  // HINZUFÜGEN
import { Bot, Send, Loader2 } from 'lucide-react'

// State ändern (Zeile 10-12):
const [query, setQuery] = useState('')
const [messages, setMessages] = useState<Array<{ role: 'user' | 'assistant'; content: string }>>([])

// useMutation ERSETZEN durch useChatStream (Zeile 14-30):
const {
  start: startInvestigation,
  typing,
  deltaText,
  finalReply,
  toolCalls,
  error: streamError,
  stop
} = useChatStream(query, { apiBase: '/api/v1/agent' })

// useEffect für finalReply (NEU):
useEffect(() => {
  if (finalReply) {
    setMessages(prev => [...prev, { role: 'assistant', content: finalReply }])
  }
}, [finalReply])

// handleSubmit ändern (Zeile 32-40):
const handleSubmit = (e: React.FormEvent) => {
  e.preventDefault()
  if (!query.trim()) return
  
  const userMsg = { role: 'user' as const, content: query }
  setMessages(prev => [...prev, userMsg])
  setQuery('')
  
  // Start SSE-Stream statt Mutation
  startInvestigation()
}

// Render anpassen für Live-Streaming (Zeile 108-122):
{typing && (
  <div className="flex justify-start">
    <div className="bg-gray-100 p-4 rounded-lg">
      <div className="flex items-center gap-2 mb-2">
        <Loader2 className="w-4 h-4 animate-spin" />
        <span className="text-sm text-gray-600">Agent analysiert...</span>
      </div>
      
      {/* Live-Delta-Text */}
      {deltaText && (
        <div className="text-sm text-gray-800 whitespace-pre-wrap animate-pulse">
          {deltaText}
        </div>
      )}
      
      {/* Tool-Progress */}
      {toolCalls.map((tc, i) => (
        <div key={i} className="text-xs text-muted-foreground mt-1">
          🔧 {tc.tool} → {tc.status || 'Running...'}
        </div>
      ))}
      
      <button
        className="ml-3 text-xs text-danger-700 hover:underline"
        onClick={stop}
      >
        Abbrechen
      </button>
    </div>
  </div>
)}
```

---

## ✨ PHASE 5: USEAIORCHESTRATOR HOOK (HIGH)

### **Ziel**: Zentraler Hook für alle AI-Interaktionen

#### **Datei**: `frontend/src/hooks/useAIOrchestrator.ts` (NEU)

```typescript
import { useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { useChatStream } from './useChatStream'
import api from '@/lib/api'

interface ForensicAction {
  tool: 'trace-address' | 'risk-score' | 'bridge-lookup' | 'cluster-analysis'
  params: Record<string, any>
}

export function useAIOrchestrator() {
  const navigate = useNavigate()
  const { start: chatStart } = useChatStream('')

  // Standard-Chat
  const ask = async (message: string) => {
    return chatStart()  // Starts SSE stream
  }

  // Forensik-Investigation mit Streaming
  const investigate = useMutation({
    mutationFn: async (query: string) => {
      const response = await api.post('/api/v1/agent/investigate', { query })
      return response.data
    }
  })

  // Direkte Tool-Calls
  const forensicAction = useMutation({
    mutationFn: async ({ tool, params }: ForensicAction) => {
      const response = await api.post(`/api/v1/agent/tools/${tool}`, params)
      return response.data
    }
  })

  // Feature-Navigation mit Pre-Fill
  const openFeature = (
    feature: 'trace' | 'risk' | 'case' | 'investigator' | 'correlation',
    prefill?: Record<string, string>
  ) => {
    const routes: Record<string, string> = {
      trace: '/trace',
      risk: '/dashboard',
      case: '/cases/new',
      investigator: '/investigator',
      correlation: '/correlation',
    }

    const queryString = prefill ? `?${new URLSearchParams(prefill).toString()}` : ''
    navigate(`${routes[feature]}${queryString}`)
  }

  // Intent-Detection + Auto-Action
  const detectAndExecute = useMutation({
    mutationFn: async (message: string) => {
      const response = await api.post('/api/v1/chat/detect-intent', { query: message })
      const { intent, params, confidence, suggested_action } = response.data

      if (confidence > 0.8 && suggested_action) {
        // Auto-Execute nach User-Confirmation
        const confirmed = window.confirm(
          `Möchtest du ${intent.toUpperCase()} für ${params.address || 'diese Adresse'} ausführen?`
        )
        
        if (confirmed) {
          if (suggested_action.startsWith('/')) {
            navigate(suggested_action)
          } else {
            // Direct API-Call
            return forensicAction.mutateAsync({ tool: intent, params })
          }
        }
      }

      return response.data
    }
  })

  return {
    ask,
    investigate: investigate.mutateAsync,
    forensicAction: forensicAction.mutateAsync,
    openFeature,
    detectAndExecute: detectAndExecute.mutateAsync,
    isInvestigating: investigate.isPending,
    isExecutingAction: forensicAction.isPending,
  }
}
```

---

## 📋 TESTING-CHECKLIST

### **Phase 2: Intent-Detection**
```bash
# Backend-Test:
curl -X POST http://localhost:8000/api/v1/chat/detect-intent \
  -H "Content-Type: application/json" \
  -d '{"query": "Trace 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0"}'

# Expected:
{
  "intent": "trace",
  "params": { "address": "0x742d35...", "chain": "ethereum" },
  "confidence": 0.9,
  "suggested_action": "/trace?address=0x742d35...&chain=ethereum"
}

# Frontend-Test:
1. Öffne ChatWidget
2. Schreibe: "Trace 0x123..."
3. Erwarte: Auto-Navigation zu /trace nach 2 Sekunden
```

### **Phase 3: InlineChatPanel**
```bash
# Test:
1. Navigiere zu /dashboard
2. Rechte Spalte zeigt InlineChatPanel
3. Klicke Quick-Action "🔍 High-Risk Trace"
4. Erwarte: Chat-Response mit High-Risk-Adressen
```

### **Phase 4: SSE für AIAgentPage**
```bash
# Test:
1. Navigiere zu /ai-agent
2. Schreibe: "Analyze address 0x123..."
3. Erwarte:
   - "Agent analysiert..." mit Spinner
   - Live-Delta-Text wird angezeigt
   - Tool-Progress: "🔧 trace_address_tool → Running..."
   - Final-Response nach Tools fertig
```

---

## 🎯 SUCCESS-CRITERIA

### **Definition of Done**:
- [x] ✅ tools_backup.py gelöscht
- [x] ✅ ai_agent.py gelöscht
- [ ] ⚡ Intent-Detection-Endpoint funktioniert
- [ ] ⚡ ChatWidget navigiert zu Features
- [ ] ⚡ InlineChatPanel im Dashboard sichtbar
- [ ] ⚡ AIAgentPage nutzt SSE-Streaming
- [ ] ✨ useAIOrchestrator in 3+ Components integriert

### **KPIs**:
- **User-Engagement**: +30% mehr Chat-Interaktionen
- **Conversion**: ChatWidget → Feature-Pages (+20%)
- **Time-to-Action**: User findet Features 2x schneller via NLP
- **Agent-Latency**: <3 Sekunden für Tool-Progress-Feedback

---

**STATUS**: 🚀 **BEREIT FÜR PHASE 2**  
**NEXT ACTION**: Intent-Detection-Endpoint implementieren
