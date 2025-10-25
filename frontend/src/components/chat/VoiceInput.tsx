/**
 * VoiceInput Component - Voice-to-Text für ChatWidget
 * Ermöglicht Hands-Free Chat via Mikrofon
 */
import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Mic, MicOff, Loader2 } from 'lucide-react'
import { toast } from 'react-hot-toast'

interface VoiceInputProps {
  onTranscript: (text: string) => void
  language?: string
  disabled?: boolean
}

export default function VoiceInput({ 
  onTranscript, 
  language = 'de-DE', 
  disabled = false 
}: VoiceInputProps) {
  const [recording, setRecording] = useState(false)
  const [processing, setProcessing] = useState(false)
  const [supported, setSupported] = useState(true)
  const [recognition, setRecognition] = useState<any>(null)

  useEffect(() => {
    // Check Browser-Support
    const SpeechRecognition = 
      window.SpeechRecognition || 
      window.webkitSpeechRecognition

    if (!SpeechRecognition) {
      setSupported(false)
      console.warn('Speech Recognition not supported')
      return
    }

    // Initialize Speech Recognition
    const recognitionInstance = new SpeechRecognition()
    recognitionInstance.lang = language
    recognitionInstance.continuous = false
    recognitionInstance.interimResults = false
    recognitionInstance.maxAlternatives = 1

    // Event Handlers
    recognitionInstance.onstart = () => {
      setRecording(true)
      toast.success('🎤 Aufnahme gestartet...', { duration: 1000 })
    }

    recognitionInstance.onresult = (event: any) => {
      const transcript = event.results[0][0].transcript
      const confidence = event.results[0][0].confidence
      
      setRecording(false)
      setProcessing(true)

      // Send transcript to chat
      onTranscript(transcript)
      
      // Analytics
      try {
        if (window?.analytics?.track) {
          window.analytics.track('voice_input_used', {
            transcript_length: transcript.length,
            confidence: confidence,
            language: language
          })
        }
      } catch {}

      setTimeout(() => setProcessing(false), 500)
      
      toast.success(`✓ "${transcript}"`, { duration: 2000 })
    }

    recognitionInstance.onerror = (event: any) => {
      setRecording(false)
      setProcessing(false)
      
      const errors: Record<string, string> = {
        'no-speech': 'Keine Sprache erkannt. Bitte erneut versuchen.',
        'audio-capture': 'Mikrofon nicht verfügbar.',
        'not-allowed': 'Mikrofon-Zugriff verweigert.',
        'network': 'Netzwerkfehler. Bitte Verbindung prüfen.'
      }
      
      const message = errors[event.error] || 'Fehler bei Spracherkennung.'
      toast.error(message, { duration: 3000 })
      
      // Analytics
      try {
        if (window?.analytics?.track) {
          window.analytics.track('voice_input_error', {
            error: event.error,
            language: language
          })
        }
      } catch {}
    }

    recognitionInstance.onend = () => {
      setRecording(false)
    }

    setRecognition(recognitionInstance)

    return () => {
      if (recognitionInstance) {
        try {
          recognitionInstance.stop()
        } catch {}
      }
    }
  }, [language, onTranscript])

  const startRecording = () => {
    if (!recognition || disabled || recording || processing) return
    
    try {
      recognition.start()
    } catch (error) {
      console.error('Error starting recognition:', error)
      toast.error('Fehler beim Starten der Aufnahme')
    }
  }

  const stopRecording = () => {
    if (!recognition || !recording) return
    
    try {
      recognition.stop()
    } catch (error) {
      console.error('Error stopping recognition:', error)
    }
  }

  if (!supported) {
    return (
      <div className="text-xs text-muted-foreground" title="Browser unterstützt keine Spracherkennung">
        <MicOff className="w-4 h-4 opacity-30" />
      </div>
    )
  }

  return (
    <motion.button
      type="button"
      onClick={recording ? stopRecording : startRecording}
      disabled={disabled || processing}
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
      className={`
        p-2 rounded-lg transition-all outline-none
        ${recording 
          ? 'bg-red-500 text-white animate-pulse' 
          : processing
          ? 'bg-blue-500 text-white'
          : 'bg-gray-100 dark:bg-slate-800 hover:bg-gray-200 dark:hover:bg-slate-700 text-gray-700 dark:text-gray-300'
        }
        ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
      `}
      aria-label={recording ? 'Aufnahme stoppen' : 'Sprachaufnahme starten'}
      title={recording ? 'Aufnahme stoppen' : 'Sprachaufnahme starten'}
    >
      {processing ? (
        <Loader2 className="w-5 h-5 animate-spin" />
      ) : recording ? (
        <MicOff className="w-5 h-5" />
      ) : (
        <Mic className="w-5 h-5" />
      )}
    </motion.button>
  )
}
