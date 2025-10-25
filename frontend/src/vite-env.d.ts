/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

// Analytics Integration (Segment, Plausible, etc.)
interface AnalyticsTrack {
  track: (event: string, properties?: Record<string, any>) => void
  page?: (name?: string, properties?: Record<string, any>) => void
  identify?: (userId: string, traits?: Record<string, any>) => void
}

interface Window {
  analytics?: AnalyticsTrack
  // Web Speech API (für VoiceInput)
  SpeechRecognition?: any
  webkitSpeechRecognition?: any
}
