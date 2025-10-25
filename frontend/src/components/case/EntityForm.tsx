import { useState } from 'react'
import { useAddEntity } from '@/hooks/useCases'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'

interface EntityFormProps {
  caseId: string
  onSuccess: () => void
  onCancel: () => void
}

export function EntityForm({ caseId, onSuccess, onCancel }: EntityFormProps) {
  const addEntity = useAddEntity()
  const [formData, setFormData] = useState({
    address: '',
    chain: '',
    labels: {} as Record<string, string>,
  })

  const [errors, setErrors] = useState<Record<string, string>>({})
  const [labelInput, setLabelInput] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    const newErrors: Record<string, string> = {}
    if (!formData.address.trim()) newErrors.address = 'Address is required'
    if (!formData.chain.trim()) newErrors.chain = 'Chain is required'

    setErrors(newErrors)

    if (Object.keys(newErrors).length === 0) {
      try {
        await addEntity.mutateAsync({ caseId, entity: formData })
        onSuccess()
      } catch (error) {
        console.error('Failed to add entity:', error)
      }
    }
  }

  const handleChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }))
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }))
    }
  }

  const addLabel = () => {
    if (labelInput.trim()) {
      const [key, value] = labelInput.split(':').map(s => s.trim())
      if (key && value) {
        setFormData(prev => ({
          ...prev,
          labels: { ...prev.labels, [key]: value }
        }))
        setLabelInput('')
      }
    }
  }

  const removeLabel = (key: string) => {
    setFormData(prev => {
      const { [key]: removed, ...rest } = prev.labels
      return { ...prev, labels: rest }
    })
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
      <div className="bg-background rounded-lg shadow-lg w-full max-w-md">
        <div className="p-6">
          <h2 className="text-xl font-semibold mb-4">Add Entity</h2>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Label htmlFor="address">Address *</Label>
              <Input
                id="address"
                value={formData.address}
                onChange={(e) => handleChange('address', e.target.value)}
                placeholder="0x..."
                className={errors.address ? 'border-red-500' : ''}
              />
              {errors.address && (
                <p className="text-sm text-red-500 mt-1">{errors.address}</p>
              )}
            </div>

            <div>
              <Label htmlFor="chain">Chain *</Label>
              <Input
                id="chain"
                value={formData.chain}
                onChange={(e) => handleChange('chain', e.target.value)}
                placeholder="ethereum, polygon, etc."
                className={errors.chain ? 'border-red-500' : ''}
              />
              {errors.chain && (
                <p className="text-sm text-red-500 mt-1">{errors.chain}</p>
              )}
            </div>

            <div>
              <Label>Labels</Label>
              <div className="flex gap-2 mb-2">
                <Input
                  value={labelInput}
                  onChange={(e) => setLabelInput(e.target.value)}
                  placeholder="key: value"
                  onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addLabel())}
                />
                <Button type="button" onClick={addLabel} size="sm">
                  Add
                </Button>
              </div>

              {Object.keys(formData.labels).length > 0 && (
                <div className="space-y-1">
                  {Object.entries(formData.labels).map(([key, value]) => (
                    <div key={key} className="flex items-center justify-between bg-muted p-2 rounded">
                      <span className="text-sm">{key}: {value}</span>
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={() => removeLabel(key)}
                      >
                        ×
                      </Button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="flex gap-3 pt-4">
              <Button type="submit" disabled={addEntity.isPending}>
                {addEntity.isPending ? 'Adding...' : 'Add Entity'}
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
