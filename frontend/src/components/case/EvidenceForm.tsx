import { useState } from 'react'
import { useLinkEvidence } from '@/hooks/useCases'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'

interface EvidenceFormProps {
  caseId: string
  onSuccess: () => void
  onCancel: () => void
}

export function EvidenceForm({ caseId, onSuccess, onCancel }: EvidenceFormProps) {
  const linkEvidence = useLinkEvidence()
  const [formData, setFormData] = useState({
    resource_id: '',
    resource_type: '',
    record_hash: '',
    notes: '',
  })

  const [errors, setErrors] = useState<Record<string, string>>({})

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    const newErrors: Record<string, string> = {}
    if (!formData.resource_id.trim()) newErrors.resource_id = 'Resource ID is required'
    if (!formData.resource_type.trim()) newErrors.resource_type = 'Resource type is required'

    setErrors(newErrors)

    if (Object.keys(newErrors).length === 0) {
      try {
        await linkEvidence.mutateAsync({ caseId, evidence: formData })
        onSuccess()
      } catch (error) {
        console.error('Failed to link evidence:', error)
      }
    }
  }

  const handleChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }))
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }))
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
      <div className="bg-background rounded-lg shadow-lg w-full max-w-md">
        <div className="p-6">
          <h2 className="text-xl font-semibold mb-4">Link Evidence</h2>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Label htmlFor="resource_id">Resource ID *</Label>
              <Input
                id="resource_id"
                value={formData.resource_id}
                onChange={(e) => handleChange('resource_id', e.target.value)}
                placeholder="Transaction hash, address, or identifier"
                className={errors.resource_id ? 'border-red-500' : ''}
              />
              {errors.resource_id && (
                <p className="text-sm text-red-500 mt-1">{errors.resource_id}</p>
              )}
            </div>

            <div>
              <Label htmlFor="resource_type">Resource Type *</Label>
              <Input
                id="resource_type"
                value={formData.resource_type}
                onChange={(e) => handleChange('resource_type', e.target.value)}
                placeholder="transaction, address, bridge_log, etc."
                className={errors.resource_type ? 'border-red-500' : ''}
              />
              {errors.resource_type && (
                <p className="text-sm text-red-500 mt-1">{errors.resource_type}</p>
              )}
            </div>

            <div>
              <Label htmlFor="record_hash">Record Hash (optional)</Label>
              <Input
                id="record_hash"
                value={formData.record_hash}
                onChange={(e) => handleChange('record_hash', e.target.value)}
                placeholder="SHA-256 hash for integrity verification"
              />
            </div>

            <div>
              <Label htmlFor="notes">Notes</Label>
              <Textarea
                id="notes"
                value={formData.notes}
                onChange={(e) => handleChange('notes', e.target.value)}
                placeholder="Additional notes or context"
                rows={3}
              />
            </div>

            <div className="flex gap-3 pt-4">
              <Button type="submit" disabled={linkEvidence.isPending}>
                {linkEvidence.isPending ? 'Linking...' : 'Link Evidence'}
              </Button>
              <Button type="button" variant="outline" onClick={onCancel}>
                Cancel
              </Button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}
