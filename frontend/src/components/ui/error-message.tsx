import { AlertCircle } from 'lucide-react'
import { cn } from '@/lib/utils'

interface ErrorMessageProps {
  title?: string
  message: string
  className?: string
}

export default function ErrorMessage({ 
  title = 'Fehler',
  message,
  className 
}: ErrorMessageProps) {
  return (
    <div className={cn(
      'p-4 bg-danger-50 border border-danger-200 rounded-lg',
      className
    )}>
      <div className="flex items-start gap-3">
        <AlertCircle className="w-5 h-5 text-danger-600 flex-shrink-0 mt-0.5" />
        <div>
          <h3 className="font-medium text-danger-900 mb-1">{title}</h3>
          <p className="text-sm text-danger-800">{message}</p>
        </div>
      </div>
    </div>
  )
}
