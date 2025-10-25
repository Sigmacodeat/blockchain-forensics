import { useSanctionsScreen } from '@/hooks/useSanctions'
import { Badge } from '@/components/ui/badge'
import { AlertTriangle } from 'lucide-react'
import { cn } from '@/lib/utils'

interface SanctionsBadgeProps {
  address: string
  chain?: string
  className?: string
}

/**
 * Badge für Sanctions-Status einer Adresse
 */
export function SanctionsBadge({ address, chain = 'ethereum', className }: SanctionsBadgeProps) {
  const { data: screenResult, isLoading, error } = useSanctionsScreen({
    address,
    lists: ['ofac', 'un', 'eu', 'uk']
  })

  if (isLoading) {
    return (
      <Badge variant="outline" className={cn("animate-pulse", className)}>
        Checking...
      </Badge>
    )
  }

  if (error || !screenResult) {
    return (
      <Badge variant="outline" className={cn("text-muted-foreground", className)}>
        Unknown
      </Badge>
    )
  }

  if (screenResult.matched) {
    return (
      <Badge variant="destructive" className={cn("flex items-center gap-1", className)}>
        <AlertTriangle className="w-3 h-3" />
        Sanctioned
      </Badge>
    )
  }

  return (
    <Badge variant="outline" className={cn("text-green-600", className)}>
      Clean
    </Badge>
  )
}
