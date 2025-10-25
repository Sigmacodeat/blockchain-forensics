import { useEffect, useMemo, useRef, useState, useCallback } from 'react'
import { useAuth } from '@/contexts/AuthContext'

type CollaborationMessageType =
  | 'collab.snapshot'
  | 'collab.join'
  | 'collab.leave'
  | 'collab.cursor'
  | 'collab.selection'
  | 'collab.note'
  | 'collab.chat'

interface BaseMessage<TType extends CollaborationMessageType, TPayload = unknown> {
  type: TType
  payload?: TPayload
  case_id?: string
  user?: {
    user_id: string
    user_name: string
  }
}

type SnapshotMessage = BaseMessage<
  'collab.snapshot',
  {
    participants?: CollaborationParticipant[]
    notes?: CollaborationNote[]
    chat?: CollaborationChatMessage[]
    selections?: Record<string, unknown>
  }
>

type JoinMessage = BaseMessage<'collab.join'>
type LeaveMessage = BaseMessage<'collab.leave', { participants?: CollaborationParticipant[] }>
type CursorMessage = BaseMessage<'collab.cursor', { user_id?: string; cursor?: Record<string, unknown> }>
type SelectionMessage = BaseMessage<'collab.selection', { user_id?: string; selection?: Record<string, unknown> }>
type NoteMessage = BaseMessage<'collab.note', CollaborationNote>
type ChatMessage = BaseMessage<'collab.chat', CollaborationChatMessage>

type WSMessage =
  | SnapshotMessage
  | JoinMessage
  | LeaveMessage
  | CursorMessage
  | SelectionMessage
  | NoteMessage
  | ChatMessage

export interface CollaborationParticipant {
  user_id: string
  user_name: string
  joined_at: string
  cursor?: Record<string, any>
}

export interface CollaborationNote {
  id: string
  case_id: string
  user_id: string
  user_name: string
  text: string
  created_at: string
}

export interface CollaborationChatMessage extends CollaborationNote {}

export interface CollaborationSelectionEvent {
  user_id: string
  selection: Record<string, unknown>
}

export interface CollaborationState {
  participants: CollaborationParticipant[]
  notes: CollaborationNote[]
  chat: CollaborationChatMessage[]
  selections: Record<string, unknown>
  connected: boolean
  lastEvent?: WSMessage
  error?: string | null
}

const WS_URL = (() => {
  const envUrl = import.meta.env?.VITE_WS_URL as string | undefined
  if (envUrl) return envUrl.replace(/\/$/, '')
  try {
    const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    return `${proto}//${window.location.host}`
  } catch {
    return 'ws://localhost:8000'
  }
})()

interface UseCollaborationWorkspaceOptions {
  caseId: string | null
  enabled?: boolean
}

export const useCollaborationWorkspace = ({
  caseId,
  enabled = true,
}: UseCollaborationWorkspaceOptions) => {
  const { user } = useAuth()
  const [state, setState] = useState<CollaborationState>(() => ({
    participants: [],
    notes: [],
    chat: [],
    selections: {},
    connected: false,
    error: null,
  }))
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectAttempts = useRef(0)
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

  const disconnect = useCallback(() => {
    if (reconnectTimer.current) {
      clearTimeout(reconnectTimer.current)
      reconnectTimer.current = null
    }
    wsRef.current?.close()
    wsRef.current = null
  }, [])

  const resetState = useCallback(() => {
    setState({
      participants: [],
      notes: [],
      chat: [],
      selections: {},
      connected: false,
      error: null,
    })
  }, [])

  const connectRef = useRef<() => void>()

  const connect = useCallback(() => {
    if (!caseId || !user || !enabled || wsRef.current) return

    const url = new URL(`${WS_URL}/api/v1/ws/collab/${caseId}`)
    url.searchParams.set('user_id', user.id)
    url.searchParams.set('user_name', user.username || user.email || 'Analyst')

    const ws = new WebSocket(url.toString())
    wsRef.current = ws

    ws.onopen = () => {
      reconnectAttempts.current = 0
      setState((prev) => ({ ...prev, connected: true, error: null }))
    }

    ws.onmessage = (event) => {
      try {
        const message: WSMessage = JSON.parse(event.data)
        setState((prev) => {
          switch (message.type) {
            case 'collab.snapshot': {
              const payload = message.payload || {}
              return {
                ...prev,
                participants: payload.participants || [],
                notes: payload.notes || [],
                chat: payload.chat || [],
                selections: payload.selections || {},
                lastEvent: message,
              }
            }
            case 'collab.join': {
              const newParticipant = message.user
              const participants = newParticipant
                ? [
                    ...prev.participants.filter((p) => p.user_id !== newParticipant.user_id),
                    {
                      user_id: newParticipant.user_id,
                      user_name: newParticipant.user_name,
                      joined_at: new Date().toISOString(),
                    },
                  ]
                : prev.participants
              return { ...prev, participants: participants.slice(-50), lastEvent: message }
            }
            case 'collab.leave': {
              const payload = message.payload || {}
              const participants: CollaborationParticipant[] = payload.participants || []
              return { ...prev, participants, lastEvent: message }
            }
            case 'collab.cursor': {
              const payload = message.payload || {}
              const userId = payload.user_id ?? message.user?.user_id
              if (!userId) return { ...prev, lastEvent: message }
              return {
                ...prev,
                selections: {
                  ...prev.selections,
                  [`cursor:${userId}`]: payload.cursor ?? null,
                },
                lastEvent: message,
              }
            }
            case 'collab.selection': {
              const payload = message.payload || {}
              const userId = payload.user_id ?? message.user?.user_id
              if (!userId || !payload.selection) return { ...prev, lastEvent: message }
              return {
                ...prev,
                selections: {
                  ...prev.selections,
                  [userId]: payload.selection,
                },
                lastEvent: message,
              }
            }
            case 'collab.note': {
              const payload = message.payload as CollaborationNote
              return {
                ...prev,
                notes: [...prev.notes.slice(-99), payload],
                lastEvent: message,
              }
            }
            case 'collab.chat': {
              const payload = message.payload as CollaborationChatMessage
              return {
                ...prev,
                chat: [...prev.chat.slice(-99), payload],
                lastEvent: message,
              }
            }
            default:
              return { ...prev, lastEvent: message }
          }
        })
      } catch (error) {
        console.error('Collab WS parse error', error)
      }
    }

    ws.onerror = () => {
      setState((prev) => ({ ...prev, connected: false, error: 'WebSocket error' }))
    }

    ws.onclose = () => {
      wsRef.current = null
      setState((prev) => ({ ...prev, connected: false }))
      if (!caseId || !enabled) return
      if (reconnectAttempts.current >= 5) return
      const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 10000)
      reconnectAttempts.current += 1
      reconnectTimer.current = setTimeout(() => connectRef.current?.(), delay)
    }
  }, [caseId, user, enabled])

  connectRef.current = connect

  useEffect(() => {
    connect()
    return () => {
      disconnect()
      resetState()
    }
  }, [connect, disconnect, resetState])

  useEffect(() => {
    if (!enabled || !caseId || !user) {
      disconnect()
      resetState()
      return
    }
    connect()
  }, [enabled, caseId, user, connect, disconnect, resetState])

  const sendEvent = useCallback(
    (type: string, payload?: Record<string, any>) => {
      if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return
      wsRef.current.send(JSON.stringify({ type, payload }))
    },
    []
  )

  const api = useMemo(
    () => ({
      state,
      sendCursor: (cursor: Record<string, any>) => sendEvent('collab.cursor', cursor),
      sendSelection: (selection: Record<string, any>) => sendEvent('collab.selection', selection),
      sendNote: (text: string) => sendEvent('collab.note', { text }),
      sendChat: (text: string) => sendEvent('collab.chat', { text }),
      disconnect,
      reconnect: () => {
        disconnect()
        resetState()
        reconnectAttempts.current = 0
        connect()
      },
    }),
    [state, sendEvent, disconnect, resetState, connect]
  )

  return api
}

export type UseCollaborationWorkspaceReturn = ReturnType<typeof useCollaborationWorkspace>
