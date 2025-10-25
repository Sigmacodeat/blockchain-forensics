import React from 'react'
import { motion } from 'framer-motion'
import { AlertTriangle, RefreshCw, Bug } from 'lucide-react'

interface Props {
  children: React.ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
  errorInfo: React.ErrorInfo | null
}

export default class ChatErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null
    }
  }

  static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      error,
      errorInfo: null
    }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    // Log to error reporting service
    console.error('ChatWidget Error:', error, errorInfo)
    
    this.setState({
      error,
      errorInfo
    })

    // Send to analytics
    try {
      if ((window as any).analytics?.track) {
        ;(window as any).analytics.track('chat_error', {
          error: error.message,
          stack: error.stack,
          componentStack: errorInfo.componentStack
        })
      }
    } catch (e) {
      console.error('Failed to track error:', e)
    }
  }

  handleReload = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null
    })
    window.location.reload()
  }

  handleReset = () => {
    // Clear localStorage
    localStorage.removeItem('chat_session_id')
    localStorage.removeItem('chat_history')
    localStorage.removeItem('chatbot_config')
    
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null
    })
  }

  render() {
    if (this.state.hasError) {
      return (
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="fixed bottom-4 right-4 z-50 w-[360px] max-w-[90vw] bg-white dark:bg-slate-800 rounded-lg shadow-2xl border-2 border-red-500 p-6"
        >
          {/* Error Icon */}
          <div className="flex items-center justify-center mb-4">
            <div className="w-16 h-16 bg-red-100 dark:bg-red-900/20 rounded-full flex items-center justify-center">
              <AlertTriangle className="w-8 h-8 text-red-600" />
            </div>
          </div>

          {/* Error Message */}
          <h3 className="text-lg font-semibold text-center mb-2 text-slate-900 dark:text-white">
            Chat-Fehler
          </h3>
          <p className="text-sm text-center text-slate-600 dark:text-slate-400 mb-4">
            Der Chatbot ist auf einen Fehler gestoßen. Keine Sorge, deine Daten sind sicher!
          </p>

          {/* Error Details (collapsed) */}
          {this.state.error && (
            <details className="mb-4">
              <summary className="text-xs text-slate-500 cursor-pointer hover:text-slate-700 dark:hover:text-slate-300 flex items-center gap-2">
                <Bug className="w-3 h-3" />
                Technische Details anzeigen
              </summary>
              <div className="mt-2 p-3 bg-slate-100 dark:bg-slate-900 rounded text-xs font-mono overflow-x-auto">
                <p className="text-red-600 dark:text-red-400">{this.state.error.message}</p>
                {this.state.error.stack && (
                  <pre className="mt-2 text-slate-600 dark:text-slate-400 text-[10px]">
                    {this.state.error.stack.split('\n').slice(0, 5).join('\n')}
                  </pre>
                )}
              </div>
            </details>
          )}

          {/* Actions */}
          <div className="space-y-2">
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={this.handleReset}
              className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors"
            >
              <RefreshCw className="w-4 h-4" />
              Chat zurücksetzen
            </motion.button>

            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={this.handleReload}
              className="w-full px-4 py-2 bg-slate-200 hover:bg-slate-300 dark:bg-slate-700 dark:hover:bg-slate-600 text-slate-700 dark:text-slate-200 rounded-lg transition-colors text-sm"
            >
              Seite neu laden
            </motion.button>
          </div>

          {/* Help Text */}
          <p className="text-xs text-center text-slate-500 mt-4">
            Wenn das Problem weiterhin besteht, kontaktiere bitte den Support.
          </p>
        </motion.div>
      )
    }

    return this.props.children
  }
}
