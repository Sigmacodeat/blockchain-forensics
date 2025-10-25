/*
 * Responsive Layout Utilities für mobile und Tablet-Geräte
 */

import React, { ReactNode } from 'react'

interface ResponsiveGridProps {
  children: ReactNode
  // Neues, einfaches API: direkte Tailwind-Grid-Columns-Klassen als String
  columns?: string
  // Altes API: strukturierte Spaltenangaben
  cols?: {
    mobile?: number
    tablet?: number
    desktop?: number
  }
  // Akzeptiert entweder bereits komplette Klasse (z.B. 'gap-4') oder nur den Wert (z.B. '4')
  gap?: string
  className?: string
}

export const ResponsiveGrid: React.FC<ResponsiveGridProps> = ({
  children,
  columns,
  cols = { mobile: 1, tablet: 2, desktop: 4 },
  gap = 'gap-4',
  className = ''
}) => {
  // Gap normalisieren: '4' -> 'gap-4'
  const gapClass = /^gap-/.test(gap) ? gap : `gap-${gap}`

  const columnsClasses = columns
    ? columns // z.B. 'grid-cols-1 md:grid-cols-2 lg:grid-cols-4'
    : [
        cols.mobile && `grid-cols-${cols.mobile}`,
        cols.tablet && `md:grid-cols-${cols.tablet}`,
        cols.desktop && `lg:grid-cols-${cols.desktop}`
      ].filter(Boolean).join(' ')

  const gridClasses = [
    'grid',
    columnsClasses,
    gapClass,
    className
  ].filter(Boolean).join(' ')

  return (
    <div className={gridClasses}>
      {children}
    </div>
  )
}

interface ResponsiveContainerProps {
  children: ReactNode
  maxWidth?: 'sm' | 'md' | 'lg' | 'xl' | '2xl' | 'full'
  padding?: boolean
  className?: string
}

export const ResponsiveContainer: React.FC<ResponsiveContainerProps> = ({
  children,
  maxWidth = 'xl',
  padding = true,
  className = ''
}) => {
  const containerClasses = [
    'w-full',
    maxWidth !== 'full' && `max-w-${maxWidth}`,
    padding && 'px-4 sm:px-6 lg:px-8',
    'mx-auto',
    className
  ].filter(Boolean).join(' ')

  return (
    <div className={containerClasses}>
      {children}
    </div>
  )
}

interface MobileMenuProps {
  isOpen: boolean
  onClose: () => void
  children: ReactNode
}

export const MobileMenu: React.FC<MobileMenuProps> = ({ isOpen, onClose, children }) => {
  if (!isOpen) return null

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black bg-opacity-50 z-40 md:hidden"
        onClick={onClose}
      />

      {/* Menu */}
      <div className="fixed top-0 left-0 h-full w-80 bg-white dark:bg-gray-900 shadow-lg z-50 md:hidden transform transition-transform duration-300">
        <div className="p-4">
          <button
            onClick={onClose}
            className="float-right text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <div className="px-4 pb-4">
          {children}
        </div>
      </div>
    </>
  )
}

interface ResponsiveCardProps {
  children: ReactNode
  className?: string
  padding?: boolean
}

export const ResponsiveCard: React.FC<ResponsiveCardProps> = ({
  children,
  className = '',
  padding = true
}) => {
  return (
    <div className={`bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 ${padding ? 'p-4 sm:p-6' : ''} ${className}`}>
      {children}
    </div>
  )
}

interface ResponsiveButtonProps {
  children: ReactNode
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost'
  size?: 'sm' | 'md' | 'lg'
  fullWidth?: boolean
  className?: string
  onClick?: () => void
  disabled?: boolean
}

export const ResponsiveButton: React.FC<ResponsiveButtonProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  fullWidth = false,
  className = '',
  onClick,
  disabled = false
}) => {
  const baseClasses = 'inline-flex items-center justify-center rounded-md font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none'

  const variantClasses = {
    primary: 'bg-primary-600 text-white hover:bg-primary-700 focus:ring-primary-500',
    secondary: 'bg-gray-600 text-white hover:bg-gray-700 focus:ring-gray-500',
    outline: 'border border-gray-300 bg-transparent hover:bg-gray-50 focus:ring-primary-500 dark:border-gray-600 dark:hover:bg-gray-800',
    ghost: 'hover:bg-gray-100 focus:ring-primary-500 dark:hover:bg-gray-800'
  }

  const sizeClasses = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-sm',
    lg: 'px-6 py-3 text-base'
  }

  const widthClass = fullWidth ? 'w-full' : ''

  return (
    <button
      className={`${baseClasses} ${variantClasses[variant]} ${sizeClasses[size]} ${widthClass} ${className}`}
      onClick={onClick}
      disabled={disabled}
    >
      {children}
    </button>
  )
}

// Hook für Responsive Design
export const useResponsive = () => {
  const [isMobile, setIsMobile] = React.useState(false)
  const [isTablet, setIsTablet] = React.useState(false)
  const [isDesktop, setIsDesktop] = React.useState(false)

  React.useEffect(() => {
    const checkScreenSize = () => {
      const width = window.innerWidth
      setIsMobile(width < 768)
      setIsTablet(width >= 768 && width < 1024)
      setIsDesktop(width >= 1024)
    }

    checkScreenSize()
    window.addEventListener('resize', checkScreenSize)

    return () => window.removeEventListener('resize', checkScreenSize)
  }, [])

  return { isMobile, isTablet, isDesktop }
}

// Responsive Text Component
interface ResponsiveTextProps {
  children: ReactNode
  size?: 'xs' | 'sm' | 'base' | 'lg' | 'xl' | '2xl' | '3xl'
  weight?: 'normal' | 'medium' | 'semibold' | 'bold'
  className?: string
  responsive?: boolean
}

export const ResponsiveText: React.FC<ResponsiveTextProps> = ({
  children,
  size = 'base',
  weight = 'normal',
  className = '',
  responsive = true
}) => {
  const sizeClasses = {
    xs: responsive ? 'text-xs sm:text-sm' : 'text-xs',
    sm: responsive ? 'text-sm sm:text-base' : 'text-sm',
    base: responsive ? 'text-base sm:text-lg' : 'text-base',
    lg: responsive ? 'text-lg sm:text-xl' : 'text-lg',
    xl: responsive ? 'text-xl sm:text-2xl' : 'text-xl',
    '2xl': responsive ? 'text-2xl sm:text-3xl' : 'text-2xl',
    '3xl': responsive ? 'text-3xl sm:text-4xl' : 'text-3xl'
  }

  const weightClasses = {
    normal: 'font-normal',
    medium: 'font-medium',
    semibold: 'font-semibold',
    bold: 'font-bold'
  }

  return (
    <div className={`${sizeClasses[size]} ${weightClasses[weight]} ${className}`}>
      {children}
    </div>
  )
}

// Responsive Input Component
interface ResponsiveInputProps {
  placeholder?: string
  value?: string
  onChange?: (e: React.ChangeEvent<HTMLInputElement>) => void
  className?: string
  type?: string
  disabled?: boolean
}

export const ResponsiveInput: React.FC<ResponsiveInputProps> = ({
  placeholder,
  value,
  onChange,
  className = '',
  type = 'text',
  disabled = false
}) => {
  return (
    <input
      type={type}
      placeholder={placeholder}
      value={value}
      onChange={onChange}
      disabled={disabled}
      className={`w-full px-3 py-2 text-sm sm:text-base border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-600 focus:border-primary-600 dark:bg-gray-800 dark:text-white disabled:opacity-50 ${className}`}
    />
  )
}

// Responsive Select Component
interface ResponsiveSelectProps {
  value?: string
  onChange?: (value: string) => void
  options: Array<{ value: string; label: string }>
  placeholder?: string
  className?: string
  disabled?: boolean
}

export const ResponsiveSelect: React.FC<ResponsiveSelectProps> = ({
  value,
  onChange,
  options,
  placeholder = 'Auswählen...',
  className = '',
  disabled = false
}) => {
  return (
    <select
      value={value}
      onChange={(e) => onChange?.(e.target.value)}
      disabled={disabled}
      className={`w-full px-3 py-2 text-sm sm:text-base border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-800 dark:text-white disabled:opacity-50 ${className}`}
    >
      <option value="">{placeholder}</option>
      {options.map((option) => (
        <option key={option.value} value={option.value}>
          {option.label}
        </option>
      ))}
    </select>
  )
}

// Responsive Badge Component
interface ResponsiveBadgeProps {
  children: ReactNode
  variant?: 'default' | 'success' | 'warning' | 'error' | 'info'
  size?: 'sm' | 'md' | 'lg'
  className?: string
}

export const ResponsiveBadge: React.FC<ResponsiveBadgeProps> = ({
  children,
  variant = 'default',
  size = 'md',
  className = ''
}) => {
  const variantClasses = {
    default: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200',
    success: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
    warning: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
    error: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
    info: 'bg-primary-100 text-primary-800 dark:bg-primary-900 dark:text-primary-200'
  }

  const sizeClasses = {
    sm: 'px-2 py-1 text-xs',
    md: 'px-2 py-1 text-sm',
    lg: 'px-3 py-1 text-sm'
  }

  return (
    <span className={`inline-flex items-center rounded-full font-medium ${variantClasses[variant]} ${sizeClasses[size]} ${className}`}>
      {children}
    </span>
  )
}
