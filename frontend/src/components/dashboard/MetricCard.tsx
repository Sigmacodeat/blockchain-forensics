import React from 'react'
import { LucideIcon } from 'lucide-react'
import { InfoTooltip } from '@/components/ui/tooltip'
import { useTranslation } from 'react-i18next'

interface MetricCardProps {
  title: string
  value: string | number
  subtitle?: string
  icon: LucideIcon
  iconColor?: string
  iconBgColor?: string
  tooltip?: string
  tooltipKey?: string
  trend?: {
    value: number
    label: string
    isPositive?: boolean
  }
  loading?: boolean
  className?: string
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  subtitle,
  icon: Icon,
  iconColor = 'text-primary-600',
  iconBgColor = 'bg-primary-100',
  tooltip,
  tooltipKey,
  trend,
  loading = false,
  className = ''
}) => {
  const { t } = useTranslation()

  if (loading) {
    return (
      <div className={`bg-white p-6 rounded-lg shadow animate-pulse ${className}`}>
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <div className="h-4 bg-gray-200 rounded w-24 mb-3"></div>
            <div className="h-8 bg-gray-200 rounded w-16 mb-2"></div>
            {subtitle && <div className="h-3 bg-gray-200 rounded w-32"></div>}
          </div>
          <div className={`w-12 h-12 ${iconBgColor} rounded-lg`}></div>
        </div>
      </div>
    )
  }

  return (
    <div 
      className={`bg-white p-6 rounded-lg shadow hover:shadow-md transition-shadow ${className}`}
      role="article"
      aria-labelledby={`metric-${title.replace(/\s/g, '-')}`}
    >
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <h3 
              id={`metric-${title.replace(/\s/g, '-')}`}
              className="text-sm font-medium text-gray-600"
            >
              {title}
            </h3>
            {(tooltip || tooltipKey) && (
              <InfoTooltip
                content={tooltip}
                translationKey={tooltipKey}
                size="sm"
              />
            )}
          </div>

          <p className="text-2xl font-bold text-gray-900" aria-live="polite">
            {value}
          </p>

          {subtitle && (
            <p className="text-sm text-gray-500 mt-1">{subtitle}</p>
          )}

          {trend && (
            <div 
              className={`flex items-center gap-1 mt-2 text-sm ${
                trend.isPositive ? 'text-green-600' : 'text-red-600'
              }`}
              role="status"
              aria-label={`Trend: ${trend.value}% ${trend.label}`}
            >
              <span className="font-medium">
                {trend.value > 0 ? '↑' : '↓'} {Math.abs(trend.value)}%
              </span>
              <span className="text-gray-500">{trend.label}</span>
            </div>
          )}
        </div>

        <div 
          className={`p-3 ${iconBgColor} rounded-lg flex-shrink-0`}
          aria-hidden="true"
        >
          <Icon className={`h-6 w-6 ${iconColor}`} />
        </div>
      </div>
    </div>
  )
}

export default MetricCard
