import { useMemo, useState, useEffect, useRef } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { X, ChevronLeft, ChevronRight, CheckCircle2, Shield, Search, FolderPlus } from 'lucide-react'
import { useI18n } from '@/contexts/I18nContext'

export type ForensicWizardAction = 'trace' | 'case' | 'sanctions'

interface ForensicWizardProps {
  open: boolean
  onClose: () => void
  onSubmit: (prompt: string) => void
}

export default function ForensicWizard({ open, onClose, onSubmit }: ForensicWizardProps) {
  const { t } = useI18n()
  const [step, setStep] = useState(0)
  const [action, setAction] = useState<ForensicWizardAction>('trace')
  const dialogRef = useRef<HTMLDivElement>(null)
  const closeBtnRef = useRef<HTMLButtonElement>(null)

  // Shared fields
  const [address, setAddress] = useState('')
  const [txHash, setTxHash] = useState('')
  const [timeRange, setTimeRange] = useState<'24h'|'7d'|'30d'|'all'>('7d')
  const [priority, setPriority] = useState<'low'|'medium'|'high'|'critical'>('high')
  const [caseTitle, setCaseTitle] = useState('')
  const [notes, setNotes] = useState('')
  const [errors, setErrors] = useState<{address?: string; txHash?: string; caseTitle?: string}>({})

  const canNext = useMemo(() => {
    if (step === 0) return true
    if (step === 1) {
      switch (action) {
        case 'trace':
          return (address || txHash) && !errors.address && !errors.txHash ? true : false
        case 'case':
          return !!caseTitle && !errors.caseTitle
        case 'sanctions':
          return !!address && !errors.address
        default:
          return false
      }
    }
    return true
  }, [step, action, address, txHash, caseTitle, errors])

  // Basic validators (non-exhaustive, but helpful)
  const isLikelyEVMAddress = (v: string) => /^0x[a-fA-F0-9]{40}$/.test(v)
  const isLikelyBTCBech32 = (v: string) => /^bc1[a-z0-9]{25,87}$/i.test(v)
  const isLikelyTxHash = (v: string) => /^0x[a-fA-F0-9]{64}$/.test(v)

  const validateAddress = (v: string) => {
    if (!v) return undefined
    if (isLikelyEVMAddress(v) || isLikelyBTCBech32(v)) return undefined
    return t('wizard.errors.address_invalid')
  }
  const validateTx = (v: string) => {
    if (!v) return undefined
    if (isLikelyTxHash(v)) return undefined
    return t('wizard.errors.tx_invalid')
  }

  // On change handlers with validation
  const onAddressChange = (v: string) => {
    setAddress(v)
    setErrors(prev => ({ ...prev, address: validateAddress(v) }))
  }
  const onTxChange = (v: string) => {
    setTxHash(v)
    setErrors(prev => ({ ...prev, txHash: validateTx(v) }))
  }
  const onCaseTitleChange = (v: string) => {
    setCaseTitle(v)
    setErrors(prev => ({ ...prev, caseTitle: v ? undefined : t('wizard.errors.case_title_required') }))
  }

  const buildPrompt = (): string => {
    if (action === 'trace') {
      return `Trace Request:\n`+
             `type: ${txHash ? 'transaction' : 'address'}\n`+
             `${txHash ? `tx: ${txHash}` : `address: ${address}`}\n`+
             `time_range: ${timeRange}\n`+
             `requirements: high-risk focus, cross-chain links, mixers, bridges, summary first`;
    }
    if (action === 'case') {
      return `Create Case:\n`+
             `title: ${caseTitle}\n`+
             `priority: ${priority}\n`+
             `context: ${notes || 'n/a'}\n`+
             `auto_attach: latest high-risk findings (7d)`;
    }
    // sanctions
    return `Sanctions Screening:\n`+
           `address: ${address}\n`+
           `lists: OFAC, UN, EU, UK, CA, AU, CH, JP, SG\n`+
           `time_range: ${timeRange}\n`+
           `output: table + risk summary`;
  }

  const resetAndClose = () => {
    setStep(0)
    setAction('trace')
    setAddress('')
    setTxHash('')
    setTimeRange('7d')
    setPriority('high')
    setCaseTitle('')
    setNotes('')
    onClose()
  }

  // Focus management and trap inside dialog
  useEffect(() => {
    if (!open) return
    // Focus the close button on open
    closeBtnRef.current?.focus()

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.preventDefault()
        resetAndClose()
        return
      }
      if (e.key === 'Tab') {
        const container = dialogRef.current
        if (!container) return
        const focusable = container.querySelectorAll<HTMLElement>(
          'a[href], button:not([disabled]), textarea, input, select, [tabindex]:not([tabindex="-1"])'
        )
        const first = focusable[0]
        const last = focusable[focusable.length - 1]
        if (!first || !last) return
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault()
          last.focus()
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault()
          first.focus()
        }
      }
    }
    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [open])

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="absolute inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4"
          role="dialog"
          aria-modal="true"
          aria-labelledby="wizard-title"
          aria-describedby="wizard-desc"
          onClick={resetAndClose}
        >
          <motion.div
            initial={{ y: 24, scale: 0.98 }}
            animate={{ y: 0, scale: 1 }}
            exit={{ y: 24, scale: 0.98 }}
            transition={{ type: 'spring', stiffness: 300, damping: 26 }}
            className="w-full max-w-2xl rounded-xl bg-white dark:bg-slate-900 border border-slate-200/60 dark:border-slate-800 shadow-2xl"
            onClick={(e) => e.stopPropagation()}
            ref={dialogRef}
          >
            <div className="flex items-center justify-between p-4 border-b border-slate-200/60 dark:border-slate-800">
              <div className="flex items-center gap-2">
                <span className="inline-flex h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
                <p id="wizard-title" className="text-sm font-medium text-slate-700 dark:text-slate-200">{t('wizard.title')}</p>
              </div>
              <button ref={closeBtnRef} aria-label={t('common.close')} className="icon-button" onClick={resetAndClose}>
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-4">
              <p id="wizard-desc" className="sr-only">{t('wizard.desc')}</p>
              {step === 0 && (
                <div className="grid gap-3">
                  <p className="text-sm text-slate-600 dark:text-slate-300">{t('wizard.choose_action')}</p>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                    <button
                      onClick={() => setAction('trace')}
                      className={`rounded-lg border p-4 text-left transition ${action==='trace' ? 'border-primary-500 bg-primary-50/50 dark:bg-primary-900/20' : 'border-slate-200 dark:border-slate-700'}`}
                    >
                      <Search className="w-5 h-5 mb-2" />
                      <p className="font-medium">{t('wizard.trace.title')}</p>
                      <p className="text-xs text-slate-500">{t('wizard.trace.desc')}</p>
                    </button>
                    <button
                      onClick={() => setAction('case')}
                      className={`rounded-lg border p-4 text-left transition ${action==='case' ? 'border-primary-500 bg-primary-50/50 dark:bg-primary-900/20' : 'border-slate-200 dark:border-slate-700'}`}
                    >
                      <FolderPlus className="w-5 h-5 mb-2" />
                      <p className="font-medium">{t('wizard.case.title')}</p>
                      <p className="text-xs text-slate-500">{t('wizard.case.desc')}</p>
                    </button>
                    <button
                      onClick={() => setAction('sanctions')}
                      className={`rounded-lg border p-4 text-left transition ${action==='sanctions' ? 'border-primary-500 bg-primary-50/50 dark:bg-primary-900/20' : 'border-slate-200 dark:border-slate-700'}`}
                    >
                      <Shield className="w-5 h-5 mb-2" />
                      <p className="font-medium">{t('wizard.sanctions.title')}</p>
                      <p className="text-xs text-slate-500">{t('wizard.sanctions.desc')}</p>
                    </button>
                  </div>
                </div>
              )}

              {step === 1 && (
                <div className="grid gap-4">
                  {action === 'trace' && (
                    <div className="grid gap-3">
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                        <div className="grid gap-1">
                          <label htmlFor="wiz-address" className="text-xs text-slate-600 dark:text-slate-300">{t('wizard.labels.address_opt')}</label>
                          <input
                            id="wiz-address"
                            value={address}
                            onChange={(e) => onAddressChange(e.target.value)}
                            placeholder={t('wizard.placeholders.address')}
                            className={`input ${errors.address ? 'border-rose-500 focus:border-rose-600 focus:ring-rose-400/20' : ''}`}
                            aria-invalid={!!errors.address}
                            aria-describedby={errors.address ? 'wiz-address-error' : undefined}
                          />
                          {errors.address && (
                            <p id="wiz-address-error" className="text-xs text-rose-600" aria-live="assertive">{errors.address}</p>
                          )}
                        </div>
                        <div className="grid gap-1">
                          <label htmlFor="wiz-tx" className="text-xs text-slate-600 dark:text-slate-300">{t('wizard.labels.tx_opt')}</label>
                          <input
                            id="wiz-tx"
                            value={txHash}
                            onChange={(e) => onTxChange(e.target.value)}
                            placeholder={t('wizard.placeholders.tx')}
                            className={`input ${errors.txHash ? 'border-rose-500 focus:border-rose-600 focus:ring-rose-400/20' : ''}`}
                            aria-invalid={!!errors.txHash}
                            aria-describedby={errors.txHash ? 'wiz-tx-error' : undefined}
                          />
                          {errors.txHash && (
                            <p id="wiz-tx-error" className="text-xs text-rose-600" aria-live="assertive">{errors.txHash}</p>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <label htmlFor="wiz-range" className="text-sm text-slate-600 dark:text-slate-300">{t('wizard.labels.time_range')}</label>
                        <select id="wiz-range" value={timeRange} onChange={(e) => setTimeRange(e.target.value as any)} className="input max-w-[180px]">
                          <option value="24h">24h</option>
                          <option value="7d">7 Tage</option>
                          <option value="30d">30 Tage</option>
                          <option value="all">Alles</option>
                        </select>
                      </div>
                    </div>
                  )}

                  {action === 'case' && (
                    <div className="grid gap-3">
                      <div className="grid gap-1">
                        <label htmlFor="wiz-case-title" className="text-xs text-slate-600 dark:text-slate-300">{t('wizard.labels.case_title')}</label>
                        <input
                          id="wiz-case-title"
                          value={caseTitle}
                          onChange={(e) => onCaseTitleChange(e.target.value)}
                          placeholder={t('wizard.placeholders.case_title')}
                          className={`input ${errors.caseTitle ? 'border-rose-500 focus:border-rose-600 focus:ring-rose-400/20' : ''}`}
                          aria-invalid={!!errors.caseTitle}
                          aria-describedby={errors.caseTitle ? 'wiz-case-title-error' : undefined}
                        />
                        {errors.caseTitle && (
                          <p id="wiz-case-title-error" className="text-xs text-rose-600" aria-live="assertive">{errors.caseTitle}</p>
                        )}
                      </div>
                      <div className="flex items-center gap-2">
                        <label htmlFor="wiz-priority" className="text-sm text-slate-600 dark:text-slate-300">{t('wizard.labels.priority')}</label>
                        <select id="wiz-priority" value={priority} onChange={(e) => setPriority(e.target.value as any)} className="input max-w-[200px]">
                          <option value="low">Low</option>
                          <option value="medium">Medium</option>
                          <option value="high">High</option>
                          <option value="critical">Critical</option>
                        </select>
                      </div>
                      <div className="grid gap-1">
                        <label htmlFor="wiz-notes" className="text-xs text-slate-600 dark:text-slate-300">{t('wizard.labels.notes_opt')}</label>
                        <textarea
                          id="wiz-notes"
                          value={notes}
                          onChange={(e) => setNotes(e.target.value)}
                          placeholder={t('wizard.placeholders.notes')}
                          className="input min-h-[96px]"
                        />
                      </div>
                    </div>
                  )}

                  {action === 'sanctions' && (
                    <div className="grid gap-3">
                      <div className="grid gap-1">
                        <label htmlFor="wiz-sanctions-address" className="text-xs text-slate-600 dark:text-slate-300">{t('wizard.labels.address')}</label>
                        <input
                          id="wiz-sanctions-address"
                          value={address}
                          onChange={(e) => onAddressChange(e.target.value)}
                          placeholder="z.B. 0x... oder bc1..."
                          className={`input ${errors.address ? 'border-rose-500 focus:border-rose-600 focus:ring-rose-400/20' : ''}`}
                          aria-invalid={!!errors.address}
                          aria-describedby={errors.address ? 'wiz-sanctions-address-error' : undefined}
                        />
                        {errors.address && (
                          <p id="wiz-sanctions-address-error" className="text-xs text-rose-600" aria-live="assertive">{errors.address}</p>
                        )}
                      </div>
                      <div className="flex items-center gap-2">
                        <label htmlFor="wiz-sanctions-range" className="text-sm text-slate-600 dark:text-slate-300">{t('wizard.labels.time_range')}</label>
                        <select id="wiz-sanctions-range" value={timeRange} onChange={(e) => setTimeRange(e.target.value as any)} className="input max-w-[180px]">
                          <option value="24h">24h</option>
                          <option value="7d">7 Tage</option>
                          <option value="30d">30 Tage</option>
                          <option value="all">Alles</option>
                        </select>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {step === 2 && (
                <div className="grid gap-3">
                  <div className="rounded-lg border border-slate-200 dark:border-slate-800 p-3 bg-slate-50 dark:bg-slate-800/50">
                    <p className="text-xs uppercase tracking-wide text-slate-500 mb-2">{t('wizard.review.title')}</p>
                    <pre className="text-xs whitespace-pre-wrap leading-relaxed text-slate-700 dark:text-slate-200">{buildPrompt()}</pre>
                  </div>
                  <div className="flex items-center gap-2 text-xs text-slate-500">
                    <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                    <span>{t('wizard.review.hint')}</span>
                  </div>
                </div>
              )}
            </div>

            <div className="flex items-center justify-between p-4 border-t border-slate-200/60 dark:border-slate-800">
              <button
                onClick={() => setStep((s) => Math.max(0, s - 1))}
                disabled={step === 0}
                className="btn-secondary flex items-center gap-1 disabled:opacity-50"
              >
                <ChevronLeft className="w-4 h-4" /> {t('common.back')}
              </button>

              <div className="flex items-center gap-2">
                {step < 2 ? (
                  <button
                    onClick={() => canNext && setStep((s) => Math.min(2, s + 1))}
                    disabled={!canNext}
                    className="btn-primary flex items-center gap-1 disabled:opacity-50"
                  >
                    {t('common.next')} <ChevronRight className="w-4 h-4" />
                  </button>
                ) : (
                  <button
                    onClick={() => { onSubmit(buildPrompt()); resetAndClose() }}
                    className="btn-primary flex items-center gap-1"
                  >
                    {t('wizard.execute')} <CheckCircle2 className="w-4 h-4" />
                  </button>
                )}
              </div>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
