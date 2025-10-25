import { useState } from 'react'
import { motion } from 'framer-motion'
import { 
  Copy, Check, ThumbsUp, ThumbsDown, Download, Share2, 
  Maximize2, Minimize2, Moon, Sun, Keyboard 
} from 'lucide-react'
import { toast } from 'react-hot-toast'

interface ChatFeaturesProps {
  isMinimized: boolean
  onToggleMinimize: () => void
  isDarkMode: boolean
  onToggleDarkMode: () => void
  onExportChat: () => void
  onShareChat: () => void
}

export default function ChatFeatures({
  isMinimized,
  onToggleMinimize,
  isDarkMode,
  onToggleDarkMode,
  onExportChat,
  onShareChat
}: ChatFeaturesProps) {
  const [showShortcuts, setShowShortcuts] = useState(false)

  return (
    <div className="flex items-center gap-1">
      {/* Minimize/Maximize */}
      <motion.button
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.9 }}
        onClick={onToggleMinimize}
        className="p-1.5 rounded-lg hover:bg-white/50 dark:hover:bg-slate-800/50 transition-colors"
        title={isMinimized ? "Maximieren" : "Minimieren"}
      >
        {isMinimized ? <Maximize2 className="w-4 h-4" /> : <Minimize2 className="w-4 h-4" />}
      </motion.button>

      {/* Dark/Light Mode */}
      <motion.button
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.9 }}
        onClick={onToggleDarkMode}
        className="p-1.5 rounded-lg hover:bg-white/50 dark:hover:bg-slate-800/50 transition-colors"
        title={isDarkMode ? "Light Mode" : "Dark Mode"}
      >
        {isDarkMode ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
      </motion.button>

      {/* Export Chat */}
      <motion.button
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.9 }}
        onClick={onExportChat}
        className="p-1.5 rounded-lg hover:bg-white/50 dark:hover:bg-slate-800/50 transition-colors"
        title="Chat als PDF exportieren"
      >
        <Download className="w-4 h-4" />
      </motion.button>

      {/* Share Chat */}
      <motion.button
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.9 }}
        onClick={onShareChat}
        className="p-1.5 rounded-lg hover:bg-white/50 dark:hover:bg-slate-800/50 transition-colors"
        title="Chat teilen"
      >
        <Share2 className="w-4 h-4" />
      </motion.button>

      {/* Keyboard Shortcuts */}
      <motion.button
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.9 }}
        onClick={() => setShowShortcuts(!showShortcuts)}
        className="p-1.5 rounded-lg hover:bg-white/50 dark:hover:bg-slate-800/50 transition-colors"
        title="Keyboard Shortcuts"
      >
        <Keyboard className="w-4 h-4" />
      </motion.button>

      {/* Shortcuts-Modal */}
      {showShortcuts && (
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.9 }}
          className="absolute top-12 right-0 bg-white dark:bg-slate-800 rounded-lg shadow-xl p-4 z-50 w-64 border border-slate-200 dark:border-slate-700"
        >
          <h3 className="font-semibold mb-3 text-sm">Keyboard Shortcuts</h3>
          <div className="space-y-2 text-xs">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Chat öffnen/schließen</span>
              <kbd className="px-2 py-1 bg-slate-100 dark:bg-slate-700 rounded">ESC</kbd>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Fokus auf Input</span>
              <kbd className="px-2 py-1 bg-slate-100 dark:bg-slate-700 rounded">Ctrl+K</kbd>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Nachricht senden</span>
              <kbd className="px-2 py-1 bg-slate-100 dark:bg-slate-700 rounded">Enter</kbd>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Neue Zeile</span>
              <kbd className="px-2 py-1 bg-slate-100 dark:bg-slate-700 rounded">Shift+Enter</kbd>
            </div>
          </div>
        </motion.div>
      )}
    </div>
  )
}

// Message Action Buttons
interface MessageActionsProps {
  message: string
  onReaction?: (reaction: 'like' | 'dislike') => void
  messageId?: string
}

export function MessageActions({ message, onReaction, messageId }: MessageActionsProps) {
  const [copied, setCopied] = useState(false)
  const [reaction, setReaction] = useState<'like' | 'dislike' | null>(null)

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(message)
      setCopied(true)
      toast.success('In Zwischenablage kopiert!')
      setTimeout(() => setCopied(false), 2000)
    } catch (error) {
      toast.error('Kopieren fehlgeschlagen')
    }
  }

  const handleReaction = (type: 'like' | 'dislike') => {
    setReaction(type)
    onReaction?.(type)
    toast.success(type === 'like' ? '👍 Feedback gesendet!' : '👎 Feedback gesendet!')
  }

  return (
    <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
      {/* Copy */}
      <motion.button
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.9 }}
        onClick={handleCopy}
        className="p-1 rounded hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
        title="Kopieren"
      >
        {copied ? <Check className="w-3 h-3 text-green-500" /> : <Copy className="w-3 h-3" />}
      </motion.button>

      {/* Like */}
      <motion.button
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.9 }}
        onClick={() => handleReaction('like')}
        className={`p-1 rounded hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors ${
          reaction === 'like' ? 'text-green-500' : ''
        }`}
        title="Hilfreich"
      >
        <ThumbsUp className="w-3 h-3" />
      </motion.button>

      {/* Dislike */}
      <motion.button
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.9 }}
        onClick={() => handleReaction('dislike')}
        className={`p-1 rounded hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors ${
          reaction === 'dislike' ? 'text-red-500' : ''
        }`}
        title="Nicht hilfreich"
      >
        <ThumbsDown className="w-3 h-3" />
      </motion.button>
    </div>
  )
}
