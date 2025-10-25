import React from 'react'
import { useTranslation } from 'react-i18next'
import { usePageMeta } from '@/hooks/usePageMeta'

export default function SearchPage() {
  const { t } = useTranslation()
  usePageMeta(
    t('search.seo.title', 'Search | SIGMACODE Blockchain Forensics'),
    t('search.seo.description', 'Find content, features and documentation across SIGMACODE Blockchain Forensics.')
  )

  return (
    <div className="min-h-[60vh] container mx-auto max-w-4xl px-4 sm:px-6 py-12">
      <h1 className="text-3xl font-bold mb-4">{t('search.title', 'Suche')}</h1>
      <p className="text-muted-foreground mb-6">
        {t('search.subtitle', 'Durchsuche Inhalte, Features und Dokumentation. Globale i18n-Route, für SEO indexierbar.')}
      </p>
      <div className="border rounded-md p-4 bg-background">
        <input
          type="search"
          className="w-full bg-transparent outline-none"
          placeholder={t('search.placeholder', 'Suchbegriff eingeben...')}
          aria-label={t('search.aria', 'Suche')}
        />
      </div>
    </div>
  )
}
