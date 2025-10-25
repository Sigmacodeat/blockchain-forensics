import { useState, useEffect, useRef, useCallback } from 'react';

export type ChatEvent =
  | { type: 'chat.ready'; ok: boolean }
  | { type: 'chat.typing' }
  | { type: 'chat.keepalive'; ts: number }
  | { type: 'chat.context'; snippets: Array<{ source: string; snippet: string }> }
  | { type: 'chat.delta'; delta: string }
  | { type: 'chat.tools'; tool_calls: any[] }
  | { type: 'chat.answer'; reply: string }
  | { type: 'chat.error'; detail: string; retry_after?: number };

export interface UseChatStreamOptions {
  apiBase?: string;
  autoStart?: boolean;
}

export function useChatStream(query: string, opts: UseChatStreamOptions = {}) {
  const apiBase = opts.apiBase ?? '/api/v1';
  const [connected, setConnected] = useState(false);
  const [typing, setTyping] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [retryAfter, setRetryAfter] = useState<number | null>(null);
  const [contextSnippets, setContextSnippets] = useState<Array<{ source: string; snippet: string }>>([]);
  const [deltaText, setDeltaText] = useState('');
  const [finalReply, setFinalReply] = useState<string | null>(null);
  const [toolCalls, setToolCalls] = useState<any[]>([]);
  const esRef = useRef<EventSource | null>(null);

  const start = useCallback(() => {
    if (esRef.current) return; // already started
    if (!query.trim()) return;
    
    setTyping(false);
    setError(null);
    setRetryAfter(null);
    setContextSnippets([]);
    setDeltaText('');
    setFinalReply(null);
    setToolCalls([]);

    const url = `${apiBase}/chat/stream?q=${encodeURIComponent(query)}`;
    const es = new EventSource(url);
    esRef.current = es;

    es.addEventListener('chat.ready', () => {
      setConnected(true);
    });

    es.addEventListener('chat.typing', () => {
      setTyping(true);
    });

    es.addEventListener('chat.keepalive', () => {
      // Just a ping, no action needed
    });

    es.addEventListener('chat.context', (e: MessageEvent) => {
      try {
        const data = JSON.parse(e.data);
        setContextSnippets(data.snippets || []);
      } catch {}
    });

    es.addEventListener('chat.delta', (e: MessageEvent) => {
      try {
        const data = JSON.parse(e.data);
        setDeltaText(prev => prev + (data.delta || data.text || ''));
      } catch {}
    });

    es.addEventListener('chat.tools', (e: MessageEvent) => {
      try {
        const data = JSON.parse(e.data);
        setToolCalls(data.tool_calls || []);
      } catch {}
    });

    es.addEventListener('chat.answer', (e: MessageEvent) => {
      try {
        const data = JSON.parse(e.data);
        setFinalReply(data.reply || '');
        setTyping(false);
      } catch {}
    });

    es.addEventListener('chat.error', (e: MessageEvent) => {
      try {
        const data = JSON.parse(e.data);
        setError(data.detail || 'error');
        setRetryAfter(data.retry_after || null);
        setTyping(false);
      } catch {
        setError('error');
      }
    });

    es.onerror = () => {
      setError('connection_error');
      setTyping(false);
      setConnected(false);
    };
  }, [query, apiBase]);

  const stop = useCallback(() => {
    if (esRef.current) {
      esRef.current.close();
      esRef.current = null;
      setConnected(false);
      setTyping(false);
    }
  }, []);

  useEffect(() => {
    if (opts.autoStart !== false && query.trim()) {
      start();
    }
    return () => stop();
  }, [query, start, stop, opts.autoStart]);

  return {
    connected,
    typing,
    error,
    retryAfter,
    contextSnippets,
    deltaText,
    finalReply,
    toolCalls,
    start,
    stop,
  };
}
