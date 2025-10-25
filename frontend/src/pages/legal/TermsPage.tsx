import React from 'react'
import { useTranslation } from 'react-i18next'
import { usePageMeta } from '@/hooks/usePageMeta'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

export default function TermsPage() {
  const { t, i18n } = useTranslation()
  const lang = i18n.language || 'en'

  usePageMeta(
    t('legal.terms.seo.title', 'Terms of Service | SIGMACODE'),
    t('legal.terms.seo.description', 'Contractual terms governing the use of SIGMACODE services')
  )

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto max-w-4xl px-4 py-16">
        <div className="mb-8">
          <h1 className="text-4xl font-bold mb-4">{t('legal.terms.title', 'Terms of Service')}</h1>
          <p className="text-muted-foreground">{t('legal.terms.subtitle', 'Please read these terms carefully before using our services')}</p>
        </div>

        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>{t('legal.terms.scope.title', 'Scope')}</CardTitle>
            </CardHeader>
            <CardContent className="text-sm space-y-2">
              <p>{t('legal.terms.scope.desc', 'These terms govern the relationship between SIGMACODE and users of our products and services.')}</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>{t('legal.terms.accounts.title', 'Accounts & eligibility')}</CardTitle>
            </CardHeader>
            <CardContent className="text-sm space-y-2">
              <p>{t('legal.terms.accounts.desc', 'You are responsible for maintaining the confidentiality of your account credentials and for all activities that occur under your account.')}</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>{t('legal.terms.liability.title', 'Liability')}</CardTitle>
            </CardHeader>
            <CardContent className="text-sm space-y-2">
              <p>{t('legal.terms.liability.desc', 'To the extent permitted by law, SIGMACODE shall not be liable for indirect, incidental, special or consequential damages.')}</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>{t('legal.terms.governing_law.title', 'Governing law & venue')}</CardTitle>
            </CardHeader>
            <CardContent className="text-sm space-y-2">
              <p>{t('legal.terms.governing_law.desc', 'The governing law and venue depend on your contracting entity and jurisdiction. Details will be specified in your order form or enterprise agreement.')}</p>
            </CardContent>
          </Card>

          <div className="text-xs text-muted-foreground pt-2">
            <p>{t('legal.terms.last_updated', 'Last updated')}: {new Date().toLocaleDateString(lang)}</p>
          </div>
        </div>
      </div>
    </div>
  )
}
