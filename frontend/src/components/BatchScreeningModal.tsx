import { useState } from 'react'
import { useSanctionsBatchScreen } from '@/hooks/useSanctions'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { AlertTriangle, CheckCircle, X } from 'lucide-react'
import { Case } from '@/types/case'

interface BatchScreeningModalProps {
  cases: Case[]
  isOpen: boolean
  onClose: () => void
}

export function BatchScreeningModal({ cases, isOpen, onClose }: BatchScreeningModalProps) {
  const [selectedCases, setSelectedCases] = useState<Set<string>>(new Set())

  // Extract addresses from cases (assuming case has 'primary_address' or similar)
  const screeningItems = cases.map(case_ => ({
    address: case_.case_id, // Placeholder: use actual address field if available
    name: case_.title,
  })).filter((_, index) => selectedCases.has(cases[index].case_id))

  const { data: results, isLoading, error } = useSanctionsBatchScreen(screeningItems)

  const toggleCase = (caseId: string) => {
    const newSelected = new Set(selectedCases)
    if (newSelected.has(caseId)) {
      newSelected.delete(caseId)
    } else {
      newSelected.add(caseId)
    }
    setSelectedCases(newSelected)
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50" role="dialog" aria-modal="true">
      <Card className="w-full max-w-2xl max-h-[90vh] overflow-auto">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Batch Sanctions Screening</CardTitle>
              <CardDescription>Select cases to screen for sanctions</CardDescription>
            </div>
            <Button variant="ghost" size="sm" onClick={onClose}>
              <X className="h-4 w-4" />
            </Button>
          </div>
        </CardHeader>

        <CardContent className="space-y-4">
          {/* Case Selection */}
          <div>
            <h3 className="font-semibold mb-2">Select Cases</h3>
            <div className="space-y-2 max-h-40 overflow-y-auto">
              {cases.map(case_ => (
                <div key={case_.case_id} className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id={case_.case_id}
                    checked={selectedCases.has(case_.case_id)}
                    onChange={() => toggleCase(case_.case_id)}
                  />
                  <label htmlFor={case_.case_id} className="text-sm">
                    {case_.title} ({case_.case_id})
                  </label>
                </div>
              ))}
            </div>
          </div>

          {/* Screening Results */}
          {selectedCases.size > 0 && (
            <div>
              <h3 className="font-semibold mb-2">Screening Results</h3>
              {isLoading ? (
                <p className="text-sm text-muted-foreground">Screening in progress...</p>
              ) : error ? (
                <p className="text-sm text-red-600">Error: {error.message}</p>
              ) : results ? (
                <div className="space-y-2">
                  {results.map((result, index) => {
                    const case_ = cases.find(c => c.case_id === Array.from(selectedCases)[index])
                    return (
                      <div key={index} className="flex items-center justify-between p-2 border rounded">
                        <span className="text-sm">{case_?.title}</span>
                        {result.matched ? (
                          <Badge variant="destructive" className="flex items-center gap-1">
                            <AlertTriangle className="w-3 h-3" />
                            Sanctioned
                          </Badge>
                        ) : (
                          <Badge variant="outline" className="flex items-center gap-1 text-green-600">
                            <CheckCircle className="w-3 h-3" />
                            Clean
                          </Badge>
                        )}
                      </div>
                    )
                  })}
                </div>
              ) : null}
            </div>
          )}

          {/* Actions */}
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={onClose}>
              Close
            </Button>
            {selectedCases.size > 0 && (
              <Button onClick={() => setSelectedCases(new Set())}>
                Clear Selection
              </Button>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
