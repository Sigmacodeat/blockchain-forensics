import { useEffect, useState } from 'react'

interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  timestamp?: Date
}

const STORAGE_KEY = 'chat_history'
const MAX_MESSAGES = 50

export function useChatHistory() {
  const [messages, setMessages] = useState<ChatMessage[]>([])

  // Load from localStorage on mount
  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY)
      if (stored) {
        const parsed = JSON.parse(stored)
        // Convert timestamp strings back to Date objects
        const withDates = parsed.map((msg: any) => ({
          ...msg,
          timestamp: msg.timestamp ? new Date(msg.timestamp) : undefined
        }))
        setMessages(withDates)
      }
    } catch (error) {
      console.error('Failed to load chat history:', error)
    }
  }, [])

  // Save to localStorage whenever messages change
  useEffect(() => {
    try {
      // Keep only last MAX_MESSAGES
      const toSave = messages.slice(-MAX_MESSAGES)
      localStorage.setItem(STORAGE_KEY, JSON.stringify(toSave))
    } catch (error) {
      console.error('Failed to save chat history:', error)
    }
  }, [messages])

  const addMessage = (message: ChatMessage) => {
    setMessages(prev => [...prev, message])
  }

  const clearHistory = () => {
    setMessages([])
    localStorage.removeItem(STORAGE_KEY)
  }

  const exportHistory = () => {
    const text = messages
      .map(m => `[${m.role.toUpperCase()}] ${m.content}`)
      .join('\n\n')
    return text
  }

  return {
    messages,
    addMessage,
    clearHistory,
    exportHistory,
    setMessages
  }
}
