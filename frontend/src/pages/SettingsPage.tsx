import React from 'react'
import { useTranslation } from 'react-i18next'
import { Link, useLocation } from 'react-router-dom'
import { Settings, User, Key, CreditCard } from 'lucide-react'
import { useI18n } from '@/contexts/I18nContext'

export default function SettingsPage() {
  const { t } = useTranslation()
  const { currentLanguage } = useI18n()
  const location = useLocation()

  const withLang = (path: string) => `/${currentLanguage}${path === '/' ? '' : path}`

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 py-6">
      <div className="mb-6">
        <h1 className="text-2xl sm:text-3xl font-bold flex items-center gap-2">
          <Settings className="w-7 h-7 text-primary-600" />
          {t('settings.title', { defaultValue: 'Settings' })}
        </h1>
        <p className="text-sm text-muted-foreground mt-1">
          {t('settings.subtitle', { defaultValue: 'Manage your account, API keys and billing preferences.' })}
        </p>
      </div>

      <div className="grid sm:grid-cols-2 gap-4">
        <Link to={withLang('/dashboard')} className="group rounded-lg border border-border bg-background hover:border-primary/50 hover:bg-muted/50 transition p-4 flex items-start gap-3">
          <User className="w-5 h-5 text-primary-600" />
          <div>
            <div className="font-semibold">{t('settings.profile', { defaultValue: 'Profile' })}</div>
            <div className="text-sm text-muted-foreground">{t('settings.profile_desc', { defaultValue: 'Update your name, email and password.' })}</div>
          </div>
        </Link>

        <Link to={withLang('/api-keys')} className="group rounded-lg border border-border bg-background hover:border-primary/50 hover:bg-muted/50 transition p-4 flex items-start gap-3">
          <Key className="w-5 h-5 text-primary-600" />
          <div>
            <div className="font-semibold">{t('settings.api_keys', { defaultValue: 'API Keys' })}</div>
            <div className="text-sm text-muted-foreground">{t('settings.api_keys_desc', { defaultValue: 'Create and manage your API tokens.' })}</div>
          </div>
        </Link>

        <Link to={withLang('/billing')} className="group rounded-lg border border-border bg-background hover:border-primary/50 hover:bg-muted/50 transition p-4 flex items-start gap-3">
          <CreditCard className="w-5 h-5 text-primary-600" />
          <div>
            <div className="font-semibold">{t('settings.billing', { defaultValue: 'Billing' })}</div>
            <div className="text-sm text-muted-foreground">{t('settings.billing_desc', { defaultValue: 'Payment methods, receipts and subscriptions.' })}</div>
          </div>
        </Link>
      </div>

      <div className="mt-8 text-xs text-muted-foreground">
        <div>{t('settings.path', { defaultValue: 'Current path:' })} {location.pathname}</div>
      </div>
    </div>
  )
}
