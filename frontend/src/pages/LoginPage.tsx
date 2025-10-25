import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useNavigate, Link } from 'react-router-dom'
import LinkLocalized from '@/components/LinkLocalized'
import { useLocalePath } from '@/hooks/useLocalePath'
import { useAuth } from '@/contexts/AuthContext'
import { authService } from '@/lib/auth'
import { Shield, Mail, Lock, Loader2, AlertCircle } from 'lucide-react'
import GoogleLoginButton from '@/components/auth/GoogleLoginButton'

export default function LoginPage() {
  const navigate = useNavigate()
  const { login, isLoading, refreshUser } = useAuth()
  const [oauthProcessing, setOauthProcessing] = useState(false)
  const { t, i18n } = useTranslation()
  const localePath = useLocalePath()
  
  // Handle Google OAuth callback (tokens passed via query)
  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const oauth = params.get('oauth')
    const data = params.get('data')
    if (oauth === 'google' && data) {
      void (async () => {
        setOauthProcessing(true)
        try {
          const pad = (4 - (data.length % 4)) % 4
          const b64 = data.replace(/-/g, '+').replace(/_/g, '/') + '='.repeat(pad)
          const decoded = JSON.parse(atob(b64))
          const { access_token, refresh_token, user } = decoded || {}
          if (access_token && refresh_token && user) {
            authService.setTokens({ access_token, refresh_token, token_type: 'bearer' })
            authService.setUser(user)
            await refreshUser()
            window.history.replaceState({}, document.title, window.location.pathname)
            navigate(localePath('/dashboard'))
          } else {
            throw new Error('invalid_oauth_payload')
          }
        } catch (e) {
          window.history.replaceState({}, document.title, window.location.pathname)
          setError(t('auth.login.oauth_failed', 'OAuth fehlgeschlagen. Bitte erneut versuchen.'))
        } finally {
          setOauthProcessing(false)
        }
      })()
    }
  }, [navigate])

  // SEO: Auth-Seiten sollen nicht indexiert werden
  useEffect(() => {
    const meta = document.createElement('meta')
    meta.setAttribute('name', 'robots')
    meta.setAttribute('content', 'noindex, nofollow')
    meta.setAttribute('data-managed', 'auth-robots')
    document.head.appendChild(meta)
    return () => {
      const el = document.head.querySelector('meta[data-managed="auth-robots"]')
      el?.parentElement?.removeChild(el)
    }
  }, [])
  
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    if (!email || !password) {
      setError(t('auth.login.fill_all_fields', 'Bitte alle Felder ausfüllen'))
      return
    }

    try {
      await login({ email, password })
      navigate(localePath('/dashboard'))
    } catch (err: any) {
      setError(err.response?.data?.detail || t('auth.login.failed', 'Login fehlgeschlagen'))
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 via-white to-primary-50 dark:from-gray-950 dark:via-gray-900 dark:to-gray-950 flex items-center justify-center px-4">
      <div className="max-w-md w-full">
        {/* Logo & Title */}
        <div className="text-center mb-8">
          <div className="group inline-flex items-center justify-center w-16 h-16 bg-primary-600 rounded-2xl mb-4 shadow-[0_0_0_8px] shadow-primary-500/10">
            <Shield className="w-10 h-10 text-white transition-transform duration-300 group-hover:rotate-3" aria-hidden />
          </div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">SIGMACODE</h1>
          <p className="text-gray-600 dark:text-gray-300">
            {t('auth.login.subtitle', 'Melde dich an, um fortzufahren')}
          </p>
        </div>

        {/* Login Form */}
        <div className="card p-8 rounded-2xl border border-gray-200/60 dark:border-gray-700/60 bg-white/80 dark:bg-gray-900/60 backdrop-blur shadow-2xl">
          {oauthProcessing && (
            <div className="mb-4 bg-primary/10 border border-primary/20 rounded-lg p-3 flex items-center gap-2 text-primary dark:text-primary-300">
              <Loader2 className="w-5 h-5 animate-spin" />
              <span className="text-sm">{t('auth.login.oauth_processing', 'OAuth-Anmeldung wird verarbeitet…')}</span>
            </div>
          )}
          <form onSubmit={handleSubmit} className="space-y-6" aria-busy={isLoading || oauthProcessing}>
            {/* Error Message */}
            {error && (
              <div className="bg-danger-50 dark:bg-danger-900/30 border border-danger-200/70 dark:border-danger-800/60 rounded-lg p-3 flex items-start gap-2" role="alert" aria-live="assertive">
                <AlertCircle className="w-5 h-5 text-danger-600 dark:text-danger-400 mt-0.5" />
                <p className="text-sm text-danger-800 dark:text-danger-200">{error}</p>
              </div>
            )}
            {error && !oauthProcessing && (
              <div className="-mt-2">
                <GoogleLoginButton className="w-full" text={t('auth.login.google_retry', 'Erneut mit Google anmelden')} />
              </div>
            )}

            {/* Email */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                {t('auth.fields.email', 'E-Mail')}
              </label>
              <div className="relative group">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 transition-colors group-focus-within:text-primary-500" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder={t('auth.placeholders.email', 'analyst@example.com')}
                  className="w-full pl-10 pr-4 py-2.5 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:ring-2 focus:ring-primary-500/60 focus:border-transparent transition"
                  disabled={isLoading || oauthProcessing}
                  name="email"
                  autoComplete="email"
                />
              </div>
            </div>

            {/* Password */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                {t('auth.fields.password', 'Passwort')}
              </label>
              <div className="relative group">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 transition-colors group-focus-within:text-primary-500" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder={t('auth.placeholders.password', '••••••••')}
                  className="w-full pl-10 pr-4 py-2.5 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:ring-2 focus:ring-primary-500/60 focus:border-transparent transition"
                  disabled={isLoading || oauthProcessing}
                  name="current-password"
                  autoComplete="current-password"
                />
              </div>
            </div>

            {/* Remember & Forgot */}
            <div className="flex items-center justify-between">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  className="w-4 h-4 text-primary-600 border-gray-300 dark:border-gray-700 rounded focus:ring-primary-500"
                />
                <span className="ml-2 text-sm text-gray-600 dark:text-gray-300">{t('auth.login.remember_me', 'Angemeldet bleiben')}</span>
              </label>
              <LinkLocalized to="/forgot-password" className="text-sm text-primary-600 hover:text-primary-700">
                {t('auth.login.forgot_password', 'Passwort vergessen?')}
              </LinkLocalized>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isLoading || oauthProcessing}
              className="w-full btn-primary flex items-center justify-center gap-2 transition-transform will-change-transform hover:scale-[1.01] active:scale-[0.99]"
            >
              {isLoading || oauthProcessing ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  {t('auth.login.submitting', 'Anmeldung läuft...')}
                </>
              ) : (
                t('auth.login.submit', 'Anmelden')
              )}
            </button>

            {/* Social Login */}
            <div className="relative my-4">
              <div className="absolute inset-0 flex items-center" aria-hidden="true">
                <div className="w-full border-t border-gray-200 dark:border-gray-700" />
              </div>
              <div className="relative flex justify-center">
                <span className="bg-white dark:bg-gray-900 px-2 text-xs text-gray-500 dark:text-gray-400">{t('auth.login.or', 'oder')}</span>
              </div>
            </div>
            <GoogleLoginButton 
              className="w-full" 
              text={t('auth.login.google', 'Mit Google anmelden')} 
              disabled={isLoading || oauthProcessing}
            />
          </form>

          {/* Register Link */}
          <div className="mt-6 text-center">
            <p className="text-sm text-gray-600 dark:text-gray-300">
              {t('auth.login.no_account', 'Noch kein Account?')}{' '}
              <LinkLocalized to="/register" className="font-medium text-primary-600 hover:text-primary-700">
                {t('auth.login.register_now', 'Jetzt registrieren')}
              </LinkLocalized>
            </p>
          </div>
        </div>

        {/* Footer */}
        <p className="text-center text-sm text-gray-500 dark:text-gray-400 mt-8">
          © 2025 SIGMACODE Blockchain Forensics. {t('footer.rights_reserved', 'Alle Rechte vorbehalten.')}
        </p>
      </div>
    </div>
  )
}
