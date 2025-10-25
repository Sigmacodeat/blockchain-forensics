import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
import LinkLocalized from '@/components/LinkLocalized'
import { Shield, Mail, Loader2, CheckCircle } from 'lucide-react'
import api from '@/lib/api'
import { toast } from '@/lib/toast'

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isSubmitted, setIsSubmitted] = useState(false)
  const { t } = useTranslation()

  // SEO: Auth/Reset-Seite nicht indexieren
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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)

    try {
      await api.post('/api/v1/password/request', { email })
      setIsSubmitted(true)
      toast.success(t('auth.forgot.sent', 'Reset-Link wurde versendet!'))
    } catch (error: any) {
      toast.error(error.response?.data?.detail || t('auth.forgot.error', 'Fehler beim Senden'))
    } finally {
      setIsLoading(false)
    }
  }

  if (isSubmitted) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-primary-50 via-white to-primary-50 flex items-center justify-center px-4">
        <div className="max-w-md w-full">
          <div className="card p-8 text-center">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-green-100 rounded-full mb-4">
              <CheckCircle className="w-10 h-10 text-green-600" />
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-4">{t('auth.forgot.title_sent', 'E-Mail versendet!')}</h2>
            <p className="text-gray-600 mb-6">
              {t('auth.forgot.info_sent', 'Falls ein Account mit dieser E-Mail existiert, wurde ein Reset-Link versendet.')}
              <br /><br />
              <strong>{t('auth.forgot.dev_note_label', 'Hinweis (Dev-Mode):')}</strong> {t('auth.forgot.dev_note', 'Da kein E-Mail-Service konfiguriert ist, check die Server-Logs für den Reset-Link.')}
            </p>
            <LinkLocalized to="/login" className="btn-primary">
              {t('auth.forgot.back_to_login', 'Zurück zum Login')}
            </LinkLocalized>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 via-white to-primary-50 flex items-center justify-center px-4">
      <div className="max-w-md w-full">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-primary-600 rounded-2xl mb-4">
            <Shield className="w-10 h-10 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            {t('auth.forgot.title', 'Passwort vergessen?')}
          </h1>
          <p className="text-gray-600">
            {t('auth.forgot.subtitle', 'Kein Problem! Gib deine E-Mail ein und wir senden dir einen Reset-Link.')}
          </p>
        </div>

        <div className="card p-8">
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                {t('auth.fields.email', 'E-Mail-Adresse')}
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder={t('auth.placeholders.email', 'analyst@example.com')}
                  className="w-full pl-10 pr-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  required
                  disabled={isLoading}
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full btn-primary flex items-center justify-center gap-2"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  {t('auth.forgot.submitting', 'Sende...')}
                </>
              ) : (
                t('auth.forgot.submit', 'Reset-Link senden')
              )}
            </button>

            <div className="mt-6 text-center">
              <LinkLocalized to="/login" className="text-sm text-primary-600 hover:text-primary-700">
                ← {t('auth.forgot.back_to_login', 'Zurück zum Login')}
              </LinkLocalized>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}
