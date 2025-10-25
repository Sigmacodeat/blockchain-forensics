/**
 * PlanGuard Component
 * 
 * Schützt Routen basierend auf Plan-Level
 */

import { ReactNode } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'
import { hasPlan, canAccessRoute, getUpgradeMessage, type PlanId } from '@/lib/features'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import LinkLocalized from '@/components/LinkLocalized'
import { Lock, ArrowRight } from 'lucide-react'
import { useI18n } from '@/contexts/I18nContext'

interface PlanGuardProps {
  children: ReactNode
  requiredPlan?: PlanId
  fallback?: ReactNode
  redirectTo?: string
}

export function PlanGuard({ children, requiredPlan, fallback, redirectTo }: PlanGuardProps) {
  const { user, isLoading } = useAuth()
  const location = useLocation()
  const { currentLanguage } = useI18n()
  const lang = currentLanguage || 'de'

  // Loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
      </div>
    )
  }

  // Not authenticated
  if (!user) {
    return <Navigate to={`/${lang}/login`} state={{ from: location }} replace />
  }

  // Check route access
  const hasAccess = canAccessRoute(user, location.pathname)
  
  // Check specific plan requirement
  const meetsRequirement = requiredPlan ? hasPlan(user, requiredPlan) : hasAccess

  // Access granted
  if (meetsRequirement) {
    return <>{children}</>
  }

  // Custom fallback
  if (fallback) {
    return <>{fallback}</>
  }

  // Redirect option
  if (redirectTo) {
    return <Navigate to={redirectTo} replace />
  }

  // Default upgrade prompt
  return (
    <div className="container mx-auto max-w-4xl px-4 py-16">
      <Card className="border-2 border-dashed">
        <CardHeader className="text-center">
          <div className="mx-auto w-12 h-12 bg-primary/10 rounded-full flex items-center justify-center mb-4">
            <Lock className="h-6 w-6 text-primary" />
          </div>
          <CardTitle className="text-2xl">Upgrade erforderlich</CardTitle>
          <p className="text-muted-foreground mt-2">
            {requiredPlan
              ? getUpgradeMessage(`plan.${requiredPlan}`)
              : 'Diese Funktion ist in deinem aktuellen Plan nicht verfügbar'}
          </p>
        </CardHeader>
        <CardContent className="text-center space-y-4">
          <div className="flex items-center justify-center gap-2">
            <span className="text-sm text-muted-foreground">Aktueller Plan:</span>
            <Badge variant="outline">{user.plan || 'Keiner'}</Badge>
          </div>
          {requiredPlan && (
            <div className="flex items-center justify-center gap-2">
              <span className="text-sm text-muted-foreground">Benötigt:</span>
              <Badge variant="default">{requiredPlan}</Badge>
            </div>
          )}
          <div className="flex gap-3 justify-center pt-4">
            <LinkLocalized to="/pricing">
              <Button size="lg">
                Pläne vergleichen
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </LinkLocalized>
            <LinkLocalized to={`/${lang}/dashboard`}>
              <Button size="lg" variant="outline">
                Zurück zum Dashboard
              </Button>
            </LinkLocalized>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

/**
 * Feature Guard für UI-Elemente
 */
interface FeatureGuardProps {
  children: ReactNode
  feature: string
  fallback?: ReactNode
  showUpgrade?: boolean
}

export function FeatureGuard({ children, feature, fallback, showUpgrade = false }: FeatureGuardProps) {
  const { user } = useAuth()
  
  // Import hasFeature inline to avoid circular deps
  const hasAccess = user?.features?.includes(feature) || false

  if (hasAccess) {
    return <>{children}</>
  }

  if (fallback) {
    return <>{fallback}</>
  }

  if (showUpgrade) {
    return (
      <div className="relative">
        <div className="opacity-50 pointer-events-none blur-sm">
          {children}
        </div>
        <div className="absolute inset-0 flex items-center justify-center">
          <Badge variant="default" className="shadow-lg">
            <Lock className="h-3 w-3 mr-1" />
            {getUpgradeMessage(feature)}
          </Badge>
        </div>
      </div>
    )
  }

  return null
}
