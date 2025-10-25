import { Navigate } from 'react-router-dom'
import i18n from '@/i18n/config-optimized'
import { useEffect } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { UserRole } from '@/lib/auth'
import { authService } from '@/lib/auth'
import { canAccessRoute, type PlanId } from '@/lib/features'
import LoadingSpinner from '@/components/ui/LoadingSpinner'
import LinkLocalized from '@/components/LinkLocalized'

interface ProtectedRouteProps {
  children: React.ReactNode
  requiredRoles?: UserRole[]
  requiredPlan?: PlanId
  routePath?: string  // für automatische Plan-Prüfung
}

export default function ProtectedRoute({ children, requiredRoles, requiredPlan, routePath }: ProtectedRouteProps) {
  const { user, isAuthenticated, isLoading, refreshUser } = useAuth()

  // If we have a token but no user yet, fetch current user instead of redirecting
  useEffect(() => {
    if (!isAuthenticated && authService.isAuthenticated()) {
      void refreshUser()
    }
  }, [isAuthenticated, refreshUser])

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  // While token exists but user not yet populated, keep loading to avoid flicker/redirect
  const hasToken = authService.isAuthenticated()
  if (!isAuthenticated && hasToken) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  if (!isAuthenticated) {
    const lang = i18n.language || 'en'
    return <Navigate to={`/${lang}/login`} replace />
  }

  // Check role-based access (Admin-only routes)
  if (requiredRoles && requiredRoles.length > 0) {
    const hasRequiredRole = user && requiredRoles.includes(user.role)
    
    if (!hasRequiredRole) {
      return (
        <div className="flex items-center justify-center min-h-screen">
          <div className="card p-8 max-w-md text-center">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">Zugriff verweigert</h2>
            <p className="text-gray-600 dark:text-gray-300 mb-4">
              Du hast keine Berechtigung, auf diese Seite zuzugreifen.
            </p>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Erforderliche Rolle: {requiredRoles.join(', ')}
            </p>
            <button
              onClick={() => window.history.back()}
              className="btn-secondary mt-6"
            >
              Zurück
            </button>
          </div>
        </div>
      )
    }
  }

  // Check plan-based access (SaaS-Features)
  if (requiredPlan || routePath) {
    const currentPath = routePath || window.location.pathname
    const hasAccess = canAccessRoute(user, currentPath)
    
    if (!hasAccess) {
      const currentPlan = user?.plan || 'community'
      return (
        <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-primary-50 to-blue-50 dark:from-slate-900 dark:to-slate-800">
          <div className="card p-8 max-w-lg text-center shadow-xl">
            <div className="mb-6">
              <div className="mx-auto w-16 h-16 bg-primary-100 dark:bg-primary-900 rounded-full flex items-center justify-center">
                <svg className="w-8 h-8 text-primary-600 dark:text-primary-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
              </div>
            </div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-3">Plan-Upgrade erforderlich</h2>
            <p className="text-gray-600 dark:text-gray-300 mb-2">
              Diese Funktion ist in Ihrem aktuellen Plan nicht verfügbar.
            </p>
            <div className="bg-gray-100 dark:bg-slate-700 rounded-lg p-4 mb-6">
              <p className="text-sm text-gray-700 dark:text-gray-300">
                <span className="font-semibold">Aktueller Plan:</span> {currentPlan.toUpperCase()}
              </p>
              {requiredPlan && (
                <p className="text-sm text-gray-700 dark:text-gray-300 mt-1">
                  <span className="font-semibold">Benötigt:</span> {requiredPlan.toUpperCase()}+
                </p>
              )}
            </div>
            <div className="flex gap-3 justify-center">
              <LinkLocalized
                to="/pricing"
                className="btn-primary"
              >
                Pläne ansehen
              </LinkLocalized>
              <button
                onClick={() => window.history.back()}
                className="btn-secondary"
              >
                Zurück
              </button>
            </div>
          </div>
        </div>
      )
    }
  }

  return <>{children}</>
}
