import React from 'react'

export type BadgeProps = React.HTMLAttributes<HTMLSpanElement> & {
  variant?: 'default' | 'secondary' | 'destructive' | 'outline' | 'success' | 'warning' | 'scan' | 'scan-border'
}

const base = 'inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors'
const variants: Record<NonNullable<BadgeProps['variant']>, string> = {
  default: 'border-transparent bg-primary text-primary-foreground',
  secondary: 'border-transparent bg-secondary text-secondary-foreground',
  destructive: 'border-transparent bg-red-600 text-white',
  outline: 'text-foreground',
  success: 'border-transparent bg-green-600 text-white',
  warning: 'border-transparent bg-amber-500 text-white',
  scan: 'border-transparent bg-secondary text-secondary-foreground badge-scan',
  'scan-border': 'border-transparent bg-secondary text-secondary-foreground badge-scan-border'
}

export const Badge: React.FC<BadgeProps> = ({ className, variant = 'default', ...props }) => (
  <span className={[base, variants[variant], className].filter(Boolean).join(' ')} {...props} />
)

export default Badge
