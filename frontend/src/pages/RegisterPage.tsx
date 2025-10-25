import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useNavigate, Link } from 'react-router-dom'
import LinkLocalized from '@/components/LinkLocalized'
import { useLocalePath } from '@/hooks/useLocalePath'
import { useAuth } from '@/contexts/AuthContext'
import { Shield, Mail, Lock, User, Building, Loader2, AlertCircle } from 'lucide-react'
import GoogleLoginButton from '@/components/auth/GoogleLoginButton'
import OrganizationSelector from '@/components/auth/OrganizationSelector'

export default function RegisterPage() {
  const navigate = useNavigate()
  const { register, isLoading } = useAuth()
  const { t } = useTranslation()
  const localePath = useLocalePath()
  
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
  
  const [formData, setFormData] = useState({
    email: '',
    username: '',
    password: '',
    confirmPassword: '',
    organization: '',
    organization_type: undefined as string | undefined,
    organization_name: undefined as string | undefined,
    wants_institutional_discount: false,
  })
  const [error, setError] = useState<string | null>(null)

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: e.target.value
    }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    // Validation
    if (!formData.email || !formData.username || !formData.password) {
      setError(t('auth.register.fill_all_fields', 'Bitte alle Pflichtfelder ausfüllen'))
      return
    }

    if (formData.password !== formData.confirmPassword) {
      setError(t('auth.register.passwords_no_match', 'Passwörter stimmen nicht überein'))
      return
    }

    if (formData.password.length < 8) {
      setError(t('auth.register.password_too_short', 'Passwort muss mindestens 8 Zeichen lang sein'))
      return
    }

    try {
      await register({
        email: formData.email,
        username: formData.username,
        password: formData.password,
        organization: formData.organization || undefined,
        organization_type: formData.organization_type,
        organization_name: formData.organization_name,
        wants_institutional_discount: formData.wants_institutional_discount,
      })
      navigate(localePath('/dashboard'))
    } catch (err: any) {
      setError(err.response?.data?.detail || t('auth.register.failed', 'Registrierung fehlgeschlagen'))
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 via-white to-primary-50 dark:from-gray-950 dark:via-gray-900 dark:to-gray-950 flex items-center justify-center px-4 py-12">
      <div className="max-w-md w-full">
        {/* Logo & Title */}
        <div className="text-center mb-8">
          <div className="group inline-flex items-center justify-center w-16 h-16 bg-primary-600 rounded-2xl mb-4 shadow-[0_0_0_8px] shadow-primary-500/10">
            <Shield className="w-10 h-10 text-white transition-transform duration-300 group-hover:rotate-3" />
          </div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">{t('auth.register.title', 'Account erstellen')}</h1>
          <p className="text-gray-600 dark:text-gray-300">
            {t('auth.register.subtitle', 'Starte deine forensische Analyse')}
          </p>
        </div>

        {/* Register Form */}
        <div className="card p-8 rounded-2xl border border-gray-200/60 dark:border-gray-700/60 bg-white/80 dark:bg-gray-900/60 backdrop-blur shadow-2xl">
          <form onSubmit={handleSubmit} className="space-y-5" autoComplete="on">
            {/* Error Message */}
            {error && (
              <div className="bg-danger-50 dark:bg-danger-900/30 border border-danger-200/70 dark:border-danger-800/60 rounded-lg p-3 flex items-start gap-2">
                <AlertCircle className="w-5 h-5 text-danger-600 dark:text-danger-400 mt-0.5" />
                <p className="text-sm text-danger-800 dark:text-danger-200">{error}</p>
              </div>
            )}

            {/* Email */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                {t('auth.fields.email', 'E-Mail')} *
              </label>
              <div className="relative group">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 transition-colors group-focus-within:text-primary-500" />
                <input
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                  placeholder={t('auth.placeholders.email', 'analyst@example.com')}
                  className="w-full pl-10 pr-4 py-2.5 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:ring-2 focus:ring-primary-500/60 focus:border-transparent transition"
                  disabled={isLoading}
                  required
                  autoComplete="email"
                />
              </div>
            </div>

            {/* Username */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                {t('auth.fields.username', 'Benutzername')} *
              </label>
              <div className="relative group">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 transition-colors group-focus-within:text-primary-500" />
                <input
                  type="text"
                  name="username"
                  value={formData.username}
                  onChange={handleChange}
                  placeholder={t('auth.placeholders.username', 'john_analyst')}
                  className="w-full pl-10 pr-4 py-2.5 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:ring-2 focus:ring-primary-500/60 focus:border-transparent transition"
                  disabled={isLoading}
                  required
                  autoComplete="username"
                />
              </div>
            </div>

            {/* Organization Selector with Institutional Discount */}
            <OrganizationSelector
              value={formData.organization_type}
              organizationName={formData.organization_name}
              wantsDiscount={formData.wants_institutional_discount}
              onChange={(type, name, wantsDiscount) => {
                setFormData(prev => ({
                  ...prev,
                  organization_type: type,
                  organization_name: name,
                  wants_institutional_discount: wantsDiscount,
                  organization: name || prev.organization // Backward compatibility
                }))
              }}
              className="mb-0"
            />

            {/* Password */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                {t('auth.fields.password', 'Passwort')} *
              </label>
              <div className="relative group">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 transition-colors group-focus-within:text-primary-500" />
                <input
                  type="password"
                  name="password"
                  value={formData.password}
                  onChange={handleChange}
                  placeholder={t('auth.placeholders.password', '••••••••')}
                  className="w-full pl-10 pr-4 py-2.5 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:ring-2 focus:ring-primary-500/60 focus:border-transparent transition"
                  disabled={isLoading}
                  required
                  minLength={8}
                  autoComplete="new-password"
                />
              </div>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">{t('auth.register.password_hint', 'Mindestens 8 Zeichen')}</p>
            </div>

            {/* Confirm Password */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                {t('auth.fields.password_confirm', 'Passwort bestätigen')} *
              </label>
              <div className="relative group">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 transition-colors group-focus-within:text-primary-500" />
                <input
                  type="password"
                  name="confirmPassword"
                  value={formData.confirmPassword}
                  onChange={handleChange}
                  placeholder={t('auth.placeholders.password', '••••••••')}
                  className="w-full pl-10 pr-4 py-2.5 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:ring-2 focus:ring-primary-500/60 focus:border-transparent transition"
                  disabled={isLoading}
                  required
                  autoComplete="new-password"
                />
              </div>
            </div>

            {/* Terms */}
            <label className="flex items-start">
              <input
                type="checkbox"
                className="w-4 h-4 text-primary-600 border-gray-300 dark:border-gray-700 rounded focus:ring-primary-500 mt-1"
                required
              />
              <span className="ml-2 text-sm text-gray-600 dark:text-gray-300">
                {t('auth.register.accept', 'Ich akzeptiere die')}{' '}
                <LinkLocalized to="/terms" className="text-primary-600 hover:text-primary-700">
                  {t('footer.terms', 'AGB')}
                </LinkLocalized>{' '}
                {t('auth.register.and', 'und')}{' '}
                <LinkLocalized to="/privacy" className="text-primary-600 hover:text-primary-700">
                  {t('footer.privacy', 'Datenschutz')}
                </LinkLocalized>
              </span>
            </label>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isLoading}
              className="w-full btn-primary flex items-center justify-center gap-2 transition-transform will-change-transform hover:scale-[1.01] active:scale-[0.99]"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  {t('auth.register.submitting', 'Registrierung läuft...')}
                </>
              ) : (
                t('auth.register.submit', 'Registrieren')
              )}
            </button>

            {/* Social Register */}
            <div className="relative my-4">
              <div className="absolute inset-0 flex items-center" aria-hidden="true">
                <div className="w-full border-t border-gray-200 dark:border-gray-700" />
              </div>
              <div className="relative flex justify-center">
                <span className="bg-white dark:bg-gray-900 px-2 text-xs text-gray-500 dark:text-gray-400">{t('auth.login.or', 'oder')}</span>
              </div>
            </div>
            <GoogleLoginButton className="w-full" text={t('auth.register.google', 'Mit Google registrieren')} disabled={isLoading} />
          </form>

          {/* Login Link */}
          <div className="mt-6 text-center">
            <p className="text-sm text-gray-600 dark:text-gray-300">
              {t('auth.register.already', 'Bereits registriert?')}{' '}
              <LinkLocalized to="/login" className="font-medium text-primary-600 hover:text-primary-700">
                {t('auth.register.login_now', 'Jetzt anmelden')}
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
