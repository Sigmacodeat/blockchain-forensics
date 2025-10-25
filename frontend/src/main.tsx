import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { HelmetProvider } from 'react-helmet-async'
import App from './App'
import './index.css'
import './styles/transitions.css'
import { initWebSocket } from './lib/websocket'
import { setupAuthInterceptors } from './lib/auth'
import { authService } from './lib/auth'
import * as Sentry from '@sentry/react'
import { onConsentChange } from './lib/consent'
import { ToastProvider } from './contexts/ToastContext'
import { initializeTheme } from './lib/themes'
// WICHTIG: i18n MUSS vor React-Rendering importiert werden!
import './i18n/config-optimized'

// Initialize Theme
initializeTheme()

// Initialize Auth Interceptors
setupAuthInterceptors()
// Initialize auth session (proactive refresh & cross-tab sync)
authService.initSession()

// Initialize WebSocket
initWebSocket()

// Cookie consent helper
function getCookieConsent(): { analytics?: boolean } | null {
  try {
    const raw = localStorage.getItem('cookie_consent')
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

// Initialize Sentry/Web Vitals based on consent and keep them in sync on changes
const _dsn = import.meta.env.VITE_SENTRY_DSN as string | undefined
const _consent = getCookieConsent()
let __sentryInited = false
let __wvInited = false

function tryInitSentry() {
  if (__sentryInited || !_dsn) return
  Sentry.init({ dsn: _dsn, tracesSampleRate: 1.0 })
  __sentryInited = true
}
async function tryInitWebVitals() {
  if (__wvInited) return
  try {
    const mod = await import(/* @vite-ignore */ './monitoring/webvitals.ts')
    await mod.initWebVitals?.()
    __wvInited = true
  } catch (e) {
    // Silently ignore if module fails to load in dev
    console.debug('Web vitals not loaded:', e)
  }
}

if (_consent?.analytics) {
  tryInitSentry()
  tryInitWebVitals()
}

onConsentChange((consent) => {
  if (consent.analytics) {
    tryInitSentry()
    tryInitWebVitals()
  }
})

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      retry: 1,
    },
  },
})

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <HelmetProvider>
      <QueryClientProvider client={queryClient}>
        <ToastProvider>
          <BrowserRouter
            future={{
              v7_startTransition: true,
              v7_relativeSplatPath: true,
            }}
          >
            <App />
          </BrowserRouter>
        </ToastProvider>
      </QueryClientProvider>
    </HelmetProvider>
  </React.StrictMode>,
)
