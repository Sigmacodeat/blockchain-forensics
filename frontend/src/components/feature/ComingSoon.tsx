import React from 'react'
import { useTranslation } from 'react-i18next'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import LinkLocalized from '@/components/LinkLocalized'
import { AlertTriangle } from 'lucide-react'

export interface ComingSoonProps {
  docHref?: string
}

export default function ComingSoon({ docHref = '/features' }: ComingSoonProps) {
  const { t } = useTranslation()

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto max-w-3xl px-4 py-16" aria-live="polite" aria-atomic="true">
        <Card role="region" aria-labelledby="wip-title" aria-describedby="wip-desc">
          <CardHeader>
            <div className="flex items-center gap-2">
              <Badge variant="scan-border">{t('common.badge.wip', 'Preview')}</Badge>
            </div>
            <CardTitle id="wip-title" className="flex items-center gap-2">
              <AlertTriangle aria-hidden className="h-5 w-5 text-amber-500" />
              {t('common.wip.title')}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p id="wip-desc" className="text-muted-foreground mb-6">
              {t('common.wip.desc')}
            </p>
            <LinkLocalized to={docHref}>
              <Button aria-label={t('common.wip.cta')}>{t('common.wip.cta')}</Button>
            </LinkLocalized>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
