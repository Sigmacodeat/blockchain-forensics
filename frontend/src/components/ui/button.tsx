import React from 'react'
import type { ButtonHTMLAttributes } from 'react'

export type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: 'default' | 'secondary' | 'destructive' | 'outline' | 'ghost' | 'link' | 'success' | 'warning' | 'premium' | 'gradient'
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'icon'
}

const base = 'inline-flex items-center justify-center whitespace-nowrap rounded-lg text-sm font-semibold transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50'
const variants: Record<NonNullable<ButtonProps['variant']>, string> = {
  default: 'bg-primary text-white hover:bg-primary/90 shadow-md hover:shadow-lg focus-visible:ring-primary',
  secondary: 'bg-secondary text-secondary-foreground hover:bg-secondary/80 shadow-sm hover:shadow-md focus-visible:ring-secondary',
  destructive: 'bg-red-600 text-white hover:bg-red-700 shadow-md hover:shadow-lg focus-visible:ring-red-600',
  outline: 'border-2 border-input bg-transparent hover:bg-accent hover:text-accent-foreground hover:border-primary/50 focus-visible:ring-primary',
  ghost: 'hover:bg-accent hover:text-accent-foreground',
  link: 'text-primary underline-offset-4 hover:underline',
  success: 'bg-green-600 text-white hover:bg-green-700 shadow-md hover:shadow-lg focus-visible:ring-green-600',
  warning: 'bg-amber-500 text-white hover:bg-amber-600 shadow-md hover:shadow-lg focus-visible:ring-amber-500',
  premium: 'bg-gradient-to-r from-primary via-blue-600 to-purple-600 text-white hover:shadow-xl hover:-translate-y-0.5 shadow-lg focus-visible:ring-primary',
  gradient: 'bg-gradient-to-r from-blue-600 to-blue-700 text-white hover:from-blue-700 hover:to-blue-800 shadow-lg hover:shadow-xl hover:-translate-y-0.5 focus-visible:ring-blue-600'
}
const sizes: Record<NonNullable<ButtonProps['size']>, string> = {
  sm: 'h-8 px-3 py-1 text-xs',
  md: 'h-10 px-4 py-2 text-sm',
  lg: 'h-11 px-6 py-3 text-base',
  xl: 'h-14 px-8 py-4 text-lg',
  icon: 'h-10 w-10'
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>((
  { className, variant = 'default', size = 'md', ...props },
  ref
) => {
  const classes = [base, variants[variant], sizes[size], className]
    .filter(Boolean)
    .join(' ')
  return <button ref={ref} className={classes} {...props} />
})
Button.displayName = 'Button'

export default Button
