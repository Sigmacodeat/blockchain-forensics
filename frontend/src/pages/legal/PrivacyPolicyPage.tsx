import React from 'react'
import { useTranslation } from 'react-i18next'
import { usePageMeta } from '@/hooks/usePageMeta'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

export default function PrivacyPolicyPage() {
  const { t, i18n } = useTranslation()
  const lang = i18n.language || 'en'

  usePageMeta(
    t('legal.privacy.seo.title', 'Privacy Policy | SIGMACODE'),
    t('legal.privacy.seo.description', 'Information about how we process personal data in compliance with GDPR/CCPA')
  )

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto max-w-4xl px-4 py-16">
        <div className="mb-8">
          <h1 className="text-4xl font-bold mb-4">{t('legal.privacy.title', 'Privacy Policy')}</h1>
          <p className="text-muted-foreground">{t('legal.privacy.subtitle', 'How we collect, use and protect your personal data')}</p>
        </div>

        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>{t('legal.privacy.controller.title', 'Controller')}</CardTitle>
            </CardHeader>
            <CardContent className="text-sm space-y-2">
              <p><strong>SIGMACODE</strong> {t('legal.privacy.controller.desc', 'is responsible for processing personal data on this website')}</p>
              <p className="text-muted-foreground">{t('legal.privacy.controller.contact', 'See our legal notice for contact details')}</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>{t('legal.privacy.data_processing.title', 'Data processing')}</CardTitle>
            </CardHeader>
            <CardContent className="text-sm space-y-2">
              <p>{t('legal.privacy.data_processing.desc', 'We process personal data only where necessary to provide our services, fulfill contracts, comply with legal obligations, and improve our products.')}</p>
              <ul className="list-disc ml-5 space-y-1 text-muted-foreground">
                <li>{t('legal.privacy.data_processing.analytics', 'Analytics and performance monitoring')}</li>
                <li>{t('legal.privacy.data_processing.auth', 'Authentication and account management')}</li>
                <li>{t('legal.privacy.data_processing.billing', 'Billing (if enabled)')}</li>
                <li>{t('legal.privacy.data_processing.security', 'Security and fraud prevention')}</li>
              </ul>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>{t('legal.privacy.rights.title', 'Your rights')}</CardTitle>
            </CardHeader>
            <CardContent className="text-sm space-y-2">
              <p>{t('legal.privacy.rights.desc', 'Depending on your jurisdiction (e.g., GDPR/CCPA), you may have the right to access, rectify, delete, restrict or object to processing, and data portability.')}</p>
              <p>{t('legal.privacy.rights.contact', 'To exercise your rights, please contact us using the details in the legal notice.')}</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>{t('legal.privacy.cookies.title', 'Cookies & tracking')}</CardTitle>
            </CardHeader>
            <CardContent className="text-sm space-y-2">
              <p>{t('legal.privacy.cookies.desc', 'We use cookies only where necessary for functionality and security. Optional analytics cookies are used only with your consent (EU).')}</p>
              <p className="text-muted-foreground">{t('legal.privacy.cookies.note', 'A cookie banner and preference center will be provided in the EU to manage consent.')}</p>
            </CardContent>
          </Card>

          <div className="text-xs text-muted-foreground pt-2">
            <p>{t('legal.privacy.last_updated', 'Last updated')}: {new Date().toLocaleDateString(lang)}</p>
          </div>
        </div>
      </div>
    </div>
  )
}
