/**
 * Trial Banner Component
 * Zeigt aktiven Trial mit verbleibenden Tagen (wie Chainalysis)
 */

import { useEffect, useState } from 'react'
import { Clock, X, Sparkles } from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
import LinkLocalized from '@/components/LinkLocalized'

interface TrialStatus {
  has_trial: boolean
  trial_plan: string | null
  trial_active: boolean
  trial_ends_at: string | null
  days_remaining: number
  ever_had_trial: boolean
}

export default function TrialBanner() {
  const { user } = useAuth()
  const { t, i18n } = useTranslation()
  const [trialStatus, setTrialStatus] = useState<TrialStatus | null>(null)
  const [dismissed, setDismissed] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!user) {
      setLoading(false)
      return
    }

    // Fetch trial status
    fetchTrialStatus()
  }, [user])

  const fetchTrialStatus = async () => {
    try {
      const response = await fetch('/api/v1/trials/status', {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`
        }
      })

      if (response.ok) {
        const data = await response.json()
        setTrialStatus(data)
      }
    } catch (error) {
      console.error('Error fetching trial status:', error)
    } finally {
      setLoading(false)
    }
  }

  // Don't render if loading, no user, dismissed, or no active trial
  if (loading || !user || dismissed || !trialStatus?.trial_active) {
    return null
  }

  const daysLeft = trialStatus.days_remaining
  const trialPlan = trialStatus.trial_plan?.toUpperCase() || 'PRO'

  // Color based on days remaining
  const getBannerColor = () => {
    if (daysLeft <= 1) return 'bg-red-50 dark:bg-red-950 border-red-400 dark:border-red-600'
    if (daysLeft <= 3) return 'bg-orange-50 dark:bg-orange-950 border-orange-400 dark:border-orange-600'
    if (daysLeft <= 7) return 'bg-yellow-50 dark:bg-yellow-950 border-yellow-400 dark:border-yellow-600'
    return 'bg-blue-50 dark:bg-blue-950 border-blue-400 dark:border-blue-600'
  }

  const getTextColor = () => {
    if (daysLeft <= 1) return 'text-red-700 dark:text-red-300'
    if (daysLeft <= 3) return 'text-orange-700 dark:text-orange-300'
    if (daysLeft <= 7) return 'text-yellow-700 dark:text-yellow-300'
    return 'text-blue-700 dark:text-blue-300'
  }

  const getIconColor = () => {
    if (daysLeft <= 1) return 'text-red-500 dark:text-red-400'
    if (daysLeft <= 3) return 'text-orange-500 dark:text-orange-400'
    if (daysLeft <= 7) return 'text-yellow-500 dark:text-yellow-400'
    return 'text-blue-500 dark:text-blue-400'
  }

  return (
    <div
      className={`${getBannerColor()} border-l-4 p-4 mb-6 rounded-lg shadow-sm transition-all duration-300 animate-in fade-in slide-in-from-top-4`}
    >
      <div className="flex items-start justify-between">
        {/* Left: Icon + Text */}
        <div className="flex items-center gap-3 flex-1">
          {/* Icon */}
          <div className="flex-shrink-0">
            {daysLeft <= 1 ? (
              <Clock className={`h-5 w-5 ${getIconColor()} animate-pulse`} />
            ) : (
              <Sparkles className={`h-5 w-5 ${getIconColor()}`} />
            )}
          </div>

          {/* Text */}
          <div className="flex-1">
            <p className={`text-sm font-medium ${getTextColor()}`}>
              <span className="font-bold">{trialPlan} Trial</span>
              {' - '}
              {daysLeft === 0 && t('trial.ending_today', 'Ends today!')}
              {daysLeft === 1 && t('trial.one_day_left', '1 day remaining')}
              {daysLeft > 1 && t('trial.days_left', `${daysLeft} days remaining`)}
            </p>
            <p className={`text-xs ${getTextColor()} mt-1 opacity-80`}>
              {daysLeft <= 1
                ? t('trial.urgent_message', 'Upgrade now to keep your Pro features!')
                : t('trial.message', `Explore all ${trialPlan} features for free.`)}
            </p>
          </div>
        </div>

        {/* Right: CTA + Close */}
        <div className="flex items-center gap-2 ml-4">
          {/* Upgrade CTA */}
          <LinkLocalized
            to="/pricing"
            className={`
              px-4 py-2 text-sm font-medium rounded-lg
              transition-all duration-200
              ${
                daysLeft <= 1
                  ? 'bg-red-600 hover:bg-red-700 text-white shadow-md hover:shadow-lg'
                  : daysLeft <= 3
                  ? 'bg-orange-600 hover:bg-orange-700 text-white shadow-md hover:shadow-lg'
                  : 'bg-blue-600 hover:bg-blue-700 text-white shadow-md hover:shadow-lg'
              }
            `}
          >
            {daysLeft <= 1
              ? t('trial.upgrade_now', 'Upgrade Now')
              : t('trial.view_plans', 'View Plans')}
          </LinkLocalized>

          {/* Close Button */}
          <button
            onClick={() => setDismissed(true)}
            className={`
              p-1 rounded-lg transition-colors
              ${getTextColor()} hover:bg-black/10 dark:hover:bg-white/10
            `}
            aria-label="Dismiss"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Progress Bar (optional, für visual feedback) */}
      {daysLeft <= 7 && (
        <div className="mt-3 h-1.5 bg-black/10 dark:bg-white/10 rounded-full overflow-hidden">
          <div
            className={`
              h-full transition-all duration-500
              ${
                daysLeft <= 1
                  ? 'bg-red-500'
                  : daysLeft <= 3
                  ? 'bg-orange-500'
                  : 'bg-yellow-500'
              }
            `}
            style={{ width: `${(daysLeft / 14) * 100}%` }}
          />
        </div>
      )}
    </div>
  )
}
