import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

interface CaseSummaryProps {
  caseData?: {
    case?: {
      case_id?: string
      title?: string
      description?: string
      lead_investigator?: string
      status?: string
      created_at?: string
      updated_at?: string
    }
    entities?: Array<unknown>
    evidence?: Array<unknown>
  } | null
}

const formatTimestamp = (value?: string) => {
  if (!value) return '—'
  try {
    return new Date(value).toLocaleString()
  } catch {
    return value
  }
}

export function CaseSummary({ caseData }: CaseSummaryProps) {
  const details = caseData?.case

  if (!details) {
    return null
  }

  const entitiesCount = caseData?.entities?.length ?? 0
  const evidenceCount = caseData?.evidence?.length ?? 0

  return (
    <Card>
      <CardHeader>
        <CardTitle>Case Summary</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <p className="text-sm text-muted-foreground">Case ID</p>
            <p className="font-medium">{details.case_id ?? '—'}</p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Status</p>
            {details.status ? (
              <Badge variant={details.status === 'active' ? 'default' : 'secondary'}>{details.status}</Badge>
            ) : (
              <p className="font-medium">—</p>
            )}
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Lead Investigator</p>
            <p className="font-medium">{details.lead_investigator ?? '—'}</p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Created</p>
            <p className="font-medium">{formatTimestamp(details.created_at)}</p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Last Updated</p>
            <p className="font-medium">{formatTimestamp(details.updated_at)}</p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Entities</p>
            <p className="font-medium">{entitiesCount}</p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Evidence Items</p>
            <p className="font-medium">{evidenceCount}</p>
          </div>
        </div>

        {details.description && (
          <div className="rounded-lg border border-border bg-muted/30 p-4">
            <p className="text-sm text-muted-foreground">Description</p>
            <p className="mt-1 text-sm leading-relaxed text-foreground">{details.description}</p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
