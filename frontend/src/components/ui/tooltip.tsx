import * as React from 'react'
import * as TooltipPrimitive from '@radix-ui/react-tooltip'
import { cn } from '@/lib/utils'
import { Info, HelpCircle } from 'lucide-react'
import { useTranslation } from 'react-i18next'

const TooltipProvider = TooltipPrimitive.Provider

const TooltipRoot = TooltipPrimitive.Root

const TooltipTrigger = TooltipPrimitive.Trigger

const TooltipContent = React.forwardRef<
  React.ElementRef<typeof TooltipPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof TooltipPrimitive.Content>
>(({ className, sideOffset = 4, ...props }, ref) => (
  <TooltipPrimitive.Content
    ref={ref}
    sideOffset={sideOffset}
    className={cn(
      'z-50 overflow-hidden rounded-md bg-gray-900 px-3 py-1.5 text-xs text-white shadow-md',
      'animate-in fade-in-0 zoom-in-95 data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=closed]:zoom-out-95',
      'data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-right-2',
      'data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2',
      'max-w-xs break-words',
      className
    )}
    {...props}
  />
))
TooltipContent.displayName = TooltipPrimitive.Content.displayName

// Basis-Tooltip-Komponente
interface TooltipProps {
  children: React.ReactNode
  content: React.ReactNode
  side?: 'top' | 'right' | 'bottom' | 'left'
  delayDuration?: number
  className?: string
  ariaLabel?: string
}

const Tooltip = ({
  children,
  content,
  side = 'top',
  delayDuration = 200,
  className,
  ariaLabel
}: TooltipProps) => {
  return (
    <TooltipProvider delayDuration={delayDuration}>
      <TooltipRoot>
        <TooltipTrigger asChild aria-label={ariaLabel}>
          {children}
        </TooltipTrigger>
        <TooltipContent side={side} className={className}>
          {content}
        </TooltipContent>
      </TooltipRoot>
    </TooltipProvider>
  )
}

// Info-Icon mit Tooltip
interface InfoTooltipProps {
  content: React.ReactNode
  translationKey?: string
  side?: 'top' | 'right' | 'bottom' | 'left'
  className?: string
  iconClassName?: string
  size?: 'sm' | 'md' | 'lg'
}

const InfoTooltip = ({
  content,
  translationKey,
  side = 'top',
  className,
  iconClassName,
  size = 'md'
}: InfoTooltipProps) => {
  const { t } = useTranslation()
  
  const sizeClasses = {
    sm: 'h-3 w-3',
    md: 'h-4 w-4',
    lg: 'h-5 w-5'
  }

  const tooltipContent = translationKey ? t(translationKey) : content

  return (
    <Tooltip 
      content={tooltipContent} 
      side={side} 
      className={className}
      ariaLabel="Informationen"
    >
      <button
        type="button"
        className={cn(
          'inline-flex items-center justify-center text-muted-foreground hover:text-foreground transition-colors',
          'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 rounded-full',
          iconClassName
        )}
        aria-label="Weitere Informationen"
      >
        <Info className={cn(sizeClasses[size])} aria-hidden="true" />
      </button>
    </Tooltip>
  )
}

// Hilfe-Icon mit Tooltip
interface HelpTooltipProps {
  content: React.ReactNode
  translationKey?: string
  side?: 'top' | 'right' | 'bottom' | 'left'
  className?: string
  iconClassName?: string
  size?: 'sm' | 'md' | 'lg'
}

const HelpTooltip = ({
  content,
  translationKey,
  side = 'top',
  className,
  iconClassName,
  size = 'md'
}: HelpTooltipProps) => {
  const { t } = useTranslation()
  
  const sizeClasses = {
    sm: 'h-3 w-3',
    md: 'h-4 w-4',
    lg: 'h-5 w-5'
  }

  const tooltipContent = translationKey ? t(translationKey) : content

  return (
    <Tooltip 
      content={tooltipContent} 
      side={side} 
      className={className}
      ariaLabel="Hilfe"
    >
      <button
        type="button"
        className={cn(
          'inline-flex items-center justify-center text-muted-foreground hover:text-foreground transition-colors',
          'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 rounded-full',
          iconClassName
        )}
        aria-label="Hilfe anfordern"
      >
        <HelpCircle className={cn(sizeClasses[size])} aria-hidden="true" />
      </button>
    </Tooltip>
  )
}

// Label mit Tooltip
interface LabelWithTooltipProps {
  label: string
  tooltip: React.ReactNode
  translationKey?: string
  required?: boolean
  htmlFor?: string
  className?: string
}

const LabelWithTooltip = ({
  label,
  tooltip,
  translationKey,
  required,
  htmlFor,
  className
}: LabelWithTooltipProps) => {
  return (
    <div className={cn('flex items-center gap-2 mb-1', className)}>
      <label 
        htmlFor={htmlFor}
        className="text-sm font-medium text-gray-700"
      >
        {label}
        {required && <span className="text-red-500 ml-1" aria-label="Pflichtfeld">*</span>}
      </label>
      <InfoTooltip 
        content={tooltip} 
        translationKey={translationKey}
        size="sm"
      />
    </div>
  )
}

export {
  Tooltip,
  TooltipProvider,
  TooltipRoot,
  TooltipTrigger,
  TooltipContent,
  InfoTooltip,
  HelpTooltip,
  LabelWithTooltip
}
