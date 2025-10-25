# Chat Integration Guide
**Frontend Integration für Chat-Streaming & Retry-Backoff**

---

## Übersicht

Dieses Dokument beschreibt, wie Sie das Chat-System mit SSE-Streaming und Retry-Backoff in Ihre Frontend-Komponenten integrieren.

---

## 1. useChatStream Hook

### Basis-Verwendung

```typescript
import { useChatStream } from '@/hooks/useChatStream';

function ChatWidget() {
  const [query, setQuery] = useState('');
  const {
    connected,
    typing,
    deltaText,
    finalReply,
    error,
    retryAfter,
    contextSnippets,
    toolCalls,
  } = useChatStream(query, { autoStart: true });

  return (
    <div>
      <input
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Ask a question..."
      />
      
      {connected && <div className="status">Connected ✓</div>}
      {typing && <div className="typing">Typing...</div>}
      
      {/* Delta Streaming (inkrementell) */}
      {deltaText && <div className="delta">{deltaText}</div>}
      
      {/* Finale Antwort */}
      {finalReply && <div className="reply">{finalReply}</div>}
      
      {/* Fehlerbehandlung */}
      {error && (
        <div className="error">
          Error: {error}
          {retryAfter && ` (Retry in ${retryAfter}s)`}
        </div>
      )}
    </div>
  );
}
```

### Event-Typen

```typescript
export type ChatEvent =
  | { type: 'chat.ready'; ok: boolean }           // Verbindung hergestellt
  | { type: 'chat.typing' }                       // Agent tippt
  | { type: 'chat.keepalive'; ts: number }        // Keep-Alive Ping
  | { type: 'chat.context'; snippets: [...] }     // RAG Kontext
  | { type: 'chat.delta'; delta: string }         // Text-Chunk
  | { type: 'chat.tools'; tool_calls: any[] }     // Tool-Calls
  | { type: 'chat.answer'; reply: string }        // Finale Antwort
  | { type: 'chat.error'; detail: string; retry_after?: number };
```

---

## 2. Retry-Backoff System

### Verwendung mit Hook

```typescript
import { useRetryBackoff, formatRetryTime } from '@/utils/retryBackoff';

function MyComponent() {
  const { isLimited, remainingSeconds, retryAt } = useRetryBackoff();

  if (isLimited) {
    return (
      <div className="alert alert-warning">
        <AlertTriangle className="icon" />
        <span>
          Rate limited. Please wait {formatRetryTime(remainingSeconds)}
        </span>
      </div>
    );
  }

  return <ChatWidget />;
}
```

### Manuelle Verwendung

```typescript
import { 
  globalBackoffManager, 
  RetryBackoffManager,
  RateLimitError 
} from '@/utils/retryBackoff';

async function sendMessage(message: string) {
  try {
    const response = await fetch('/api/v1/chat', {
      method: 'POST',
      body: JSON.stringify({ message }),
    });
    
    // Auto-detect 429 und setze Backoff
    await RetryBackoffManager.handleResponse(response);
    
    return await response.json();
  } catch (e) {
    if (e instanceof RateLimitError) {
      // Setze globalen Backoff-State
      globalBackoffManager.setRateLimit(e.retryAfter);
      
      // Optional: Toast/Notification
      toast.error(`Rate limited. Retry in ${e.retryAfter}s`);
    }
    throw e;
  }
}
```

### Custom Manager

```typescript
// Eigener Manager für spezifischen Endpoint
const chatBackoff = new RetryBackoffManager();
const riskBackoff = new RetryBackoffManager();

function ChatComponent() {
  const chatState = useRetryBackoff(chatBackoff);
  // ...
}

function RiskComponent() {
  const riskState = useRetryBackoff(riskBackoff);
  // ...
}
```

---

## 3. Vollständiges Beispiel

### ChatWidget mit Retry-Backoff

```typescript
import React, { useState } from 'react';
import { useChatStream } from '@/hooks/useChatStream';
import { useRetryBackoff, formatRetryTime } from '@/utils/retryBackoff';
import { AlertTriangle, Send, Loader } from 'lucide-react';

export function ChatWidget() {
  const [input, setInput] = useState('');
  const [query, setQuery] = useState('');
  const { isLimited, remainingSeconds } = useRetryBackoff();
  
  const {
    connected,
    typing,
    deltaText,
    finalReply,
    error,
    retryAfter,
    contextSnippets,
    toolCalls,
  } = useChatStream(query, { autoStart: true });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLimited) return;
    setQuery(input);
    setInput('');
  };

  return (
    <div className="chat-widget">
      <div className="chat-header">
        <h3>AI Assistant</h3>
        {connected && <span className="status-dot" />}
      </div>

      <div className="chat-messages">
        {/* Context Snippets */}
        {contextSnippets.length > 0 && (
          <div className="context-snippets">
            <strong>Sources:</strong>
            {contextSnippets.map((s, i) => (
              <div key={i} className="snippet">
                <em>{s.source}</em>: {s.snippet}
              </div>
            ))}
          </div>
        )}

        {/* Typing Indicator */}
        {typing && (
          <div className="typing-indicator">
            <Loader className="animate-spin" />
            <span>Thinking...</span>
          </div>
        )}

        {/* Delta Text (Streaming) */}
        {deltaText && (
          <div className="message agent streaming">
            {deltaText}
            <span className="cursor">▊</span>
          </div>
        )}

        {/* Final Reply */}
        {finalReply && (
          <div className="message agent">
            {finalReply}
          </div>
        )}

        {/* Tool Calls */}
        {toolCalls.length > 0 && (
          <div className="tool-calls">
            <strong>Tools used:</strong>
            {toolCalls.map((t, i) => (
              <span key={i} className="tool-badge">
                {t.name}
              </span>
            ))}
          </div>
        )}

        {/* Error Display */}
        {error && (
          <div className="message error">
            <AlertTriangle />
            <span>{error}</span>
            {retryAfter && (
              <span className="retry-info">
                Retry in {retryAfter}s
              </span>
            )}
          </div>
        )}
      </div>

      <form onSubmit={handleSubmit} className="chat-input-form">
        {/* Rate Limit Warning */}
        {isLimited && (
          <div className="rate-limit-warning">
            Rate limited. Wait {formatRetryTime(remainingSeconds)}
          </div>
        )}

        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={isLimited ? "Rate limited..." : "Ask a question..."}
          disabled={isLimited || typing}
        />
        
        <button
          type="submit"
          disabled={!input.trim() || isLimited || typing}
        >
          <Send />
        </button>
      </form>
    </div>
  );
}
```

### Styling (TailwindCSS)

```css
.chat-widget {
  @apply flex flex-col h-full bg-white dark:bg-slate-900 rounded-lg shadow-lg;
}

.chat-header {
  @apply flex items-center justify-between p-4 border-b border-slate-200 dark:border-slate-700;
}

.status-dot {
  @apply w-2 h-2 bg-green-500 rounded-full animate-pulse;
}

.chat-messages {
  @apply flex-1 overflow-y-auto p-4 space-y-4;
}

.message {
  @apply p-3 rounded-lg max-w-[80%];
}

.message.agent {
  @apply bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-white;
}

.message.streaming .cursor {
  @apply inline-block animate-pulse;
}

.typing-indicator {
  @apply flex items-center gap-2 text-slate-600 dark:text-slate-400 text-sm;
}

.rate-limit-warning {
  @apply bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-300 dark:border-yellow-700 text-yellow-800 dark:text-yellow-200 px-3 py-2 rounded-t-lg text-sm;
}
```

---

## 4. Backend-Endpunkte

### SSE Stream
```
GET /api/v1/chat/stream?q=your+question&session_id=optional
```

**Events**:
- `chat.ready`
- `chat.typing`
- `chat.keepalive`
- `chat.context`
- `chat.delta`
- `chat.tools`
- `chat.answer`
- `chat.error`

### WebSocket
```
WS /api/v1/ws/chat
```

**Messages**:
```json
// Senden
{ "type": "message", "text": "your question" }

// Empfangen
{ "type": "chat.typing" }
{ "type": "chat.delta", "delta": "text chunk" }
{ "type": "answer", "reply": "full answer", "tool_calls": [...] }
```

### REST
```
POST /api/v1/chat
Content-Type: application/json

{
  "message": "your question",
  "messages": [
    { "role": "user", "content": "previous question" },
    { "role": "assistant", "content": "previous answer" }
  ],
  "session_id": "optional"
}
```

**Response**:
```json
{
  "reply": "answer",
  "tool_calls": [...],
  "data": null
}
```

**Rate Limit (429)**:
```
HTTP/1.1 429 Too Many Requests
Retry-After: 60
Content-Type: application/json

{"detail": "Too Many Requests"}
```

---

## 5. Best Practices

### Performance
1. **Debounce Input**: Verhindere zu viele Requests
2. **Cancel on Unmount**: Schließe EventSource in cleanup
3. **Memoize Handlers**: Nutze `useCallback` für Event-Handler

### User Experience
1. **Show Typing**: Nutze `typing` State für Loader
2. **Stream Delta**: Zeige Delta-Text mit Cursor-Animation
3. **Display Retry**: Zeige verbleibende Zeit bei Rate Limit
4. **Context Preview**: Zeige RAG-Snippets wenn verfügbar

### Error Handling
1. **Catch Errors**: Fange `RateLimitError` und andere Exceptions
2. **Retry Logic**: Implementiere Auto-Retry nach Backoff
3. **Fallback UI**: Zeige hilfreiche Fehlermeldungen

---

## 6. Konfiguration

### Environment Variables

```bash
# Backend (.env)
CHAT_RATE_LIMIT_PER_MIN=60
CHAT_MAX_INPUT_CHARS=8000
CHAT_MAX_HISTORY_ITEMS=30
CHAT_MAX_HISTORY_CHARS=4000
CHAT_MAX_UPLOAD_MB=10
CHAT_WS_CHUNK_SIZE=48
CHAT_API_KEY=optional_secret_key
```

### Frontend (.env)
```bash
VITE_API_BASE=/api/v1
VITE_WS_BASE=ws://localhost:8000/api/v1
```

---

## 7. Testing

### Unit Test für Hook
```typescript
import { renderHook, waitFor } from '@testing-library/react';
import { useChatStream } from '@/hooks/useChatStream';

test('useChatStream handles delta streaming', async () => {
  const { result } = renderHook(() =>
    useChatStream('test query', { autoStart: true })
  );

  await waitFor(() => {
    expect(result.current.connected).toBe(true);
  });

  // Simulate delta event
  // (requires MockEventSource)

  await waitFor(() => {
    expect(result.current.deltaText).toContain('chunk');
  });
});
```

---

## 8. Troubleshooting

### Problem: Stream bricht ab
**Lösung**: Check Keep-Alive, erweitere Timeout

### Problem: 429 zu häufig
**Lösung**: Erhöhe `CHAT_RATE_LIMIT_PER_MIN`

### Problem: Delta-Text fehlt
**Lösung**: Check Event-Name (`chat.delta` vs `chat.text`)

### Problem: Retry-After nicht sichtbar
**Lösung**: Stelle sicher, Backend sendet `Retry-After` Header

---

**Autor**: Cascade AI  
**Datum**: 18.10.2025  
**Version**: 1.0
