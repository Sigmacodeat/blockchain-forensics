import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { motion } from 'framer-motion'
import { Loader2, Save, X as XIcon, FileText, User as UserIcon, Hash } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'

interface CaseFormProps {
  onSubmit: (data: any) => void
  onCancel: () => void
  isLoading?: boolean
  initialData?: any
}

export function CaseForm({ onSubmit, onCancel, isLoading = false, initialData }: CaseFormProps) {
  const { t } = useTranslation()
  const [formData, setFormData] = useState({
    case_id: initialData?.case_id || '',
    title: initialData?.title || '',
    description: initialData?.description || '',
    lead_investigator: initialData?.lead_investigator || '',
  })

  const [errors, setErrors] = useState<Record<string, string>>({})
  const [touched, setTouched] = useState<Record<string, boolean>>({})

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    // Validation
    const newErrors: Record<string, string> = {}
    if (!formData.case_id.trim()) {
      newErrors.case_id = t('cases.form.error.case_id_required', 'Case ID is required')
    }
    if (!formData.title.trim()) {
      newErrors.title = t('cases.form.error.title_required', 'Title is required')
    }
    if (!formData.lead_investigator.trim()) {
      newErrors.lead_investigator = t('cases.form.error.investigator_required', 'Lead investigator is required')
    }

    setErrors(newErrors)
    if (Object.keys(newErrors).length > 0) {
      // Mark invalid fields as touched so error messages are displayed immediately
      setTouched(prev => ({
        ...prev,
        ...Object.fromEntries(Object.keys(newErrors).map((k) => [k, true]))
      }))
    }

    if (Object.keys(newErrors).length === 0) {
      onSubmit(formData)
    }
  }

  const handleChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }))
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }))
    }
  }

  const handleBlur = (field: string) => {
    setTouched(prev => ({ ...prev, [field]: true }))
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Case ID Field */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
      >
        <Label htmlFor="case_id" className="text-base font-semibold text-slate-700 dark:text-slate-300 mb-2 flex items-center gap-2">
          <div className="p-1.5 bg-primary-100 dark:bg-primary-900/30 rounded-md">
            <Hash className="h-4 w-4 text-primary-600 dark:text-primary-400" />
          </div>
          {t('cases.form.case_id', 'Case ID')} <span className="text-red-500">*</span>
        </Label>
        <Input
          id="case_id"
          value={formData.case_id}
          onChange={(e) => handleChange('case_id', e.target.value)}
          onBlur={() => handleBlur('case_id')}
          placeholder={t('cases.form.case_id_placeholder', 'e.g., CASE-2025-001')}
          className={`mt-2 bg-white/50 dark:bg-slate-900/50 backdrop-blur-sm border-2 ${
            errors.case_id && touched.case_id
              ? 'border-red-500 dark:border-red-500 focus:border-red-600 dark:focus:border-red-600'
              : 'border-slate-200 dark:border-slate-700 focus:border-primary-500 dark:focus:border-primary-600'
          } transition-all py-3`}
          disabled={isLoading}
        />
        {errors.case_id && touched.case_id && (
          <motion.p
            initial={{ opacity: 0, y: -5 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-sm text-red-600 dark:text-red-400 mt-2 flex items-center gap-1.5 font-medium"
          >
            <XIcon className="h-3.5 w-3.5" />
            {errors.case_id}
          </motion.p>
        )}
      </motion.div>

      {/* Title Field */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
      >
        <Label htmlFor="title" className="text-base font-semibold text-slate-700 dark:text-slate-300 mb-2 flex items-center gap-2">
          <div className="p-1.5 bg-purple-100 dark:bg-purple-900/30 rounded-md">
            <FileText className="h-4 w-4 text-purple-600 dark:text-purple-400" />
          </div>
          {t('cases.form.title', 'Title')} <span className="text-red-500">*</span>
        </Label>
        <Input
          id="title"
          value={formData.title}
          onChange={(e) => handleChange('title', e.target.value)}
          onBlur={() => handleBlur('title')}
          placeholder={t('cases.form.title_placeholder', 'Brief case title')}
          className={`mt-2 bg-white/50 dark:bg-slate-900/50 backdrop-blur-sm border-2 ${
            errors.title && touched.title
              ? 'border-red-500 dark:border-red-500 focus:border-red-600 dark:focus:border-red-600'
              : 'border-slate-200 dark:border-slate-700 focus:border-primary-500 dark:focus:border-primary-600'
          } transition-all py-3`}
          disabled={isLoading}
        />
        {errors.title && touched.title && (
          <motion.p
            initial={{ opacity: 0, y: -5 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-sm text-red-600 dark:text-red-400 mt-2 flex items-center gap-1.5 font-medium"
          >
            <XIcon className="h-3.5 w-3.5" />
            {errors.title}
          </motion.p>
        )}
      </motion.div>

      {/* Description Field */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
      >
        <Label htmlFor="description" className="text-base font-semibold text-slate-700 dark:text-slate-300 mb-2 flex items-center gap-2">
          <div className="p-1.5 bg-blue-100 dark:bg-blue-900/30 rounded-md">
            <FileText className="h-4 w-4 text-blue-600 dark:text-blue-400" />
          </div>
          {t('cases.form.description', 'Description')}
        </Label>
        <Textarea
          id="description"
          value={formData.description}
          onChange={(e) => handleChange('description', e.target.value)}
          placeholder={t('cases.form.description_placeholder', 'Detailed description of the investigation')}
          rows={4}
          className="mt-2 bg-white/50 dark:bg-slate-900/50 backdrop-blur-sm border-2 border-slate-200 dark:border-slate-700 focus:border-primary-500 dark:focus:border-primary-600 transition-all resize-none"
          disabled={isLoading}
        />
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-2">
          {t('cases.form.description_hint', 'Optional: Provide additional context about this case')}
        </p>
      </motion.div>

      {/* Lead Investigator Field */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
      >
        <Label htmlFor="lead_investigator" className="text-base font-semibold text-slate-700 dark:text-slate-300 mb-2 flex items-center gap-2">
          <div className="p-1.5 bg-emerald-100 dark:bg-emerald-900/30 rounded-md">
            <UserIcon className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
          </div>
          {t('cases.form.lead_investigator', 'Lead Investigator')} <span className="text-red-500">*</span>
        </Label>
        <Input
          id="lead_investigator"
          value={formData.lead_investigator}
          onChange={(e) => handleChange('lead_investigator', e.target.value)}
          onBlur={() => handleBlur('lead_investigator')}
          placeholder={t('cases.form.investigator_placeholder', 'Name or email')}
          className={`mt-2 bg-white/50 dark:bg-slate-900/50 backdrop-blur-sm border-2 ${
            errors.lead_investigator && touched.lead_investigator
              ? 'border-red-500 dark:border-red-500 focus:border-red-600 dark:focus:border-red-600'
              : 'border-slate-200 dark:border-slate-700 focus:border-primary-500 dark:focus:border-primary-600'
          } transition-all py-3`}
          disabled={isLoading}
        />
        {errors.lead_investigator && touched.lead_investigator && (
          <motion.p
            initial={{ opacity: 0, y: -5 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-sm text-red-600 dark:text-red-400 mt-2 flex items-center gap-1.5 font-medium"
          >
            <XIcon className="h-3.5 w-3.5" />
            {errors.lead_investigator}
          </motion.p>
        )}
      </motion.div>

      {/* Action Buttons */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
        className="flex gap-4 pt-4 border-t border-slate-200 dark:border-slate-700"
      >
        <Button
          type="submit"
          disabled={isLoading}
          size="lg"
          className="flex-1 bg-gradient-to-r from-primary-600 to-purple-600 hover:from-primary-700 hover:to-purple-700 text-white shadow-lg shadow-primary-500/30 dark:shadow-primary-500/20 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
        >
          {isLoading ? (
            <>
              <Loader2 className="h-5 w-5 mr-2 animate-spin" />
              {t('cases.form.creating', 'Creating...')}
            </>
          ) : (
            <>
              <Save className="h-5 w-5 mr-2" />
              {t('cases.form.create', 'Create Case')}
            </>
          )}
        </Button>
        
        <Button
          type="button"
          variant="outline"
          onClick={onCancel}
          disabled={isLoading}
          size="lg"
          className="flex-1 border-2 border-slate-300 dark:border-slate-600 hover:bg-slate-100 dark:hover:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
        >
          <XIcon className="h-5 w-5 mr-2" />
          {t('cases.form.cancel', 'Cancel')}
        </Button>
      </motion.div>
    </form>
  )
}
