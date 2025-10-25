import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import {
  AlertCircle,
  CheckCircle,
  Clock,
  FileText,
  Filter,
  Loader2,
  RefreshCw,
  Search,
  ShieldCheck,
  XCircle,
} from 'lucide-react'
import api from '@/lib/api'
import toast from 'react-hot-toast'

type VerificationStatus = 'pending' | 'approved' | 'rejected' | 'cancelled'

interface VerificationRecord {
  id: number
  user_id: string
  organization_type: string
  organization_name?: string | null
  status: VerificationStatus
  admin_notes?: string | null
  rejection_reason?: string | null
  document?: {
    type?: string | null
    url?: string | null
    filename?: string | null
    metadata?: {
      uploaded_at?: string
      original_filename?: string
      file_size?: number
    }
  }
  created_at?: string
  updated_at?: string
  reviewed_at?: string | null
  reviewed_by?: string | null
}

interface VerificationListResponse {
  success: boolean
  verifications: VerificationRecord[]
  total: number
  limit: number
  offset: number
}

const STATUS_FILTERS: { value: VerificationStatus | 'all'; label: string }[] = [
  { value: 'all', label: 'Alle' },
  { value: 'pending', label: 'Ausstehend' },
  { value: 'approved', label: 'Genehmigt' },
  { value: 'rejected', label: 'Abgelehnt' },
  { value: 'cancelled', label: 'Storniert' },
]

const ORGANIZATION_LABELS: Record<string, string> = {
  police: 'Polizei / Law Enforcement',
  detective: 'Privatdetektiv',
  lawyer: 'Anwalt / Kanzlei',
  government: 'Regierungsbehörde',
  exchange: 'Exchange / VASP',
  other: 'Andere Institution',
}

const statusBadge = (status: VerificationStatus) => {
  const config: Record<VerificationStatus, { label: string; className: string; icon: JSX.Element }> = {
    pending: {
      label: 'Ausstehend',
      className: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-200',
      icon: <Clock className="h-4 w-4" />,
    },
    approved: {
      label: 'Genehmigt',
      className: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-200',
      icon: <CheckCircle className="h-4 w-4" />,
    },
    rejected: {
      label: 'Abgelehnt',
      className: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-200',
      icon: <XCircle className="h-4 w-4" />,
    },
    cancelled: {
      label: 'Storniert',
      className: 'bg-gray-100 text-gray-700 dark:bg-slate-800/50 dark:text-gray-200',
      icon: <AlertCircle className="h-4 w-4" />,
    },
  }

  return config[status]
}

const formatDateTime = (value?: string | null) => {
  if (!value) return '–'
  return new Date(value).toLocaleString()
}

const humanFileSize = (value?: number) => {
  if (!value) return '–'
  if (value < 1024) return `${value} B`
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`
  return `${(value / (1024 * 1024)).toFixed(1)} MB`
}

const VerificationReviewDialog = ({
  record,
  onClose,
  onSubmit,
  isSubmitting,
}: {
  record: VerificationRecord
  onClose: () => void
  onSubmit: (payload: { action: 'approve' | 'reject'; admin_notes?: string; rejection_reason?: string }) => void
  isSubmitting: boolean
}) => {
  const [decision, setDecision] = useState<'approve' | 'reject'>('approve')
  const [notes, setNotes] = useState(record.admin_notes ?? '')
  const [rejectionReason, setRejectionReason] = useState(record.rejection_reason ?? '')

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="w-full max-w-xl rounded-2xl bg-white p-6 shadow-2xl dark:bg-slate-900"
      >
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Verifizierung prüfen</h2>
            <p className="text-xs text-gray-500 dark:text-gray-400">Request #{record.id} • {record.user_id}</p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 transition hover:text-gray-600 focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary-500"
            aria-label="Dialog schließen"
          >
            ✕
          </button>
        </div>

        <div className="mt-4 rounded-xl border border-gray-200 bg-gray-50 p-4 text-sm dark:border-slate-700 dark:bg-slate-800">
          <p className="font-medium text-gray-900 dark:text-white">Organisation</p>
          <p className="text-gray-700 dark:text-gray-200">
            {ORGANIZATION_LABELS[record.organization_type] ?? record.organization_type}
          </p>
          {record.organization_name && (
            <p className="text-gray-700 dark:text-gray-200">{record.organization_name}</p>
          )}
          {record.document?.filename && (
            <div className="mt-3">
              <p className="font-medium text-gray-900 dark:text-white">Dokument</p>
              <p className="text-gray-700 dark:text-gray-200">
                {record.document.url ? (
                  <a
                    href={record.document.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-primary-600 underline dark:text-primary-300"
                  >
                    {record.document.metadata?.original_filename ?? record.document.filename}
                  </a>
                ) : (
                  record.document.filename
                )}
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                Upload: {formatDateTime(record.document.metadata?.uploaded_at)} • Größe: {humanFileSize(record.document.metadata?.file_size)}
              </p>
            </div>
          )}
        </div>

        <div className="mt-6 space-y-4">
          <div>
            <p className="mb-2 text-sm font-medium text-gray-700 dark:text-gray-200">Entscheidung</p>
            <div className="grid grid-cols-2 gap-3">
              <button
                onClick={() => setDecision('approve')}
                className={`rounded-lg border px-4 py-2 text-sm font-medium transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary-500 dark:border-slate-700 ${
                  decision === 'approve'
                    ? 'border-emerald-500 bg-emerald-50 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-200'
                    : 'border-gray-200 text-gray-600 hover:border-emerald-200 dark:text-gray-300'
                }`}
              >
                Genehmigen
              </button>
              <button
                onClick={() => setDecision('reject')}
                className={`rounded-lg border px-4 py-2 text-sm font-medium transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary-500 dark:border-slate-700 ${
                  decision === 'reject'
                    ? 'border-red-500 bg-red-50 text-red-600 dark:bg-red-500/10 dark:text-red-200'
                    : 'border-gray-200 text-gray-600 hover:border-red-200 dark:text-gray-300'
                }`}
              >
                Ablehnen
              </button>
            </div>
          </div>

          <div>
            <label htmlFor="notes" className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-200">
              Admin-Notizen (optional)
            </label>
            <textarea
              id="notes"
              value={notes}
              onChange={(event) => setNotes(event.target.value)}
              rows={3}
              className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 shadow-sm focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500/40 dark:border-slate-700 dark:bg-slate-900 dark:text-white"
              placeholder="Interne Hinweise für den Audit Trail"
            />
          </div>

          {decision === 'reject' && (
            <div>
              <label htmlFor="rejection-reason" className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-200">
                Ablehnungsgrund
              </label>
              <textarea
                id="rejection-reason"
                value={rejectionReason}
                onChange={(event) => setRejectionReason(event.target.value)}
                rows={2}
                className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 shadow-sm focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500/40 dark:border-slate-700 dark:bg-slate-900 dark:text-white"
                placeholder="Begründen Sie die Ablehnung – wird dem Antragsteller angezeigt"
              />
              <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">Pflichtfeld bei Ablehnung</p>
            </div>
          )}
        </div>

        <div className="mt-6 flex justify-end gap-3">
          <button
            onClick={onClose}
            className="rounded-lg border border-gray-200 px-4 py-2 text-sm font-medium text-gray-600 transition hover:border-gray-300 focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary-500 dark:border-slate-700 dark:text-gray-300"
          >
            Abbrechen
          </button>
          <button
            onClick={() => {
              if (decision === 'reject' && !rejectionReason.trim()) {
                toast.error('Bitte geben Sie einen Ablehnungsgrund an.')
                return
              }
              onSubmit({
                action: decision,
                admin_notes: notes.trim() || undefined,
                rejection_reason: rejectionReason.trim() || undefined,
              })
            }}
            disabled={isSubmitting}
            className="inline-flex items-center gap-2 rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white shadow transition hover:bg-primary-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary-500 disabled:cursor-not-allowed disabled:bg-gray-400"
          >
            {isSubmitting && <Loader2 className="h-4 w-4 animate-spin" />}
            Entscheidung speichern
          </button>
        </div>
      </motion.div>
    </div>
  )
}

const EmptyState = ({ onRefresh }: { onRefresh: () => void }) => (
  <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-gray-300 bg-white p-12 text-center dark:border-slate-700 dark:bg-slate-900/50">
    <ShieldCheck className="h-12 w-12 text-gray-300" />
    <h3 className="mt-4 text-lg font-semibold text-gray-900 dark:text-white">Keine Anträge gefunden</h3>
    <p className="mt-2 max-w-md text-sm text-gray-500 dark:text-gray-400">
      Sobald Nutzer einen institutionellen Nachweis einreichen, erscheinen die Anträge hier.
    </p>
    <button
      onClick={onRefresh}
      className="mt-6 inline-flex items-center gap-2 rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white shadow transition hover:bg-primary-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary-500"
    >
      <RefreshCw className="h-4 w-4" />
      Jetzt aktualisieren
    </button>
  </div>
)

const TableSkeleton = () => (
  <div className="space-y-3">
    {Array.from({ length: 6 }).map((_, index) => (
      <div key={index} className="h-24 animate-pulse rounded-xl bg-gray-100 dark:bg-slate-800/60" />
    ))}
  </div>
)

export default function InstitutionalVerificationAdminPage() {
  const [statusFilter, setStatusFilter] = useState<VerificationStatus | 'all'>('pending')
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedRecord, setSelectedRecord] = useState<VerificationRecord | null>(null)

  const queryClient = useQueryClient()

  const { data, isLoading, refetch, isRefetching } = useQuery<VerificationListResponse>({
    queryKey: ['admin-institutional-verifications', statusFilter],
    queryFn: async () => {
      const response = await api.get('/api/v1/verification', {
        params: {
          status: statusFilter === 'all' ? undefined : statusFilter,
          limit: 100,
          offset: 0,
        },
      })
      return response.data
    },
  })

  const reviewMutation = useMutation({
    mutationFn: async ({ verificationId, action, admin_notes, rejection_reason }: {
      verificationId: number
      action: 'approve' | 'reject'
      admin_notes?: string
      rejection_reason?: string
    }) => {
      const formData = new FormData()
      formData.append('action', action)
      if (admin_notes) formData.append('admin_notes', admin_notes)
      if (rejection_reason) formData.append('rejection_reason', rejection_reason)

      const response = await api.post(`/api/v1/verification/${verificationId}/review`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })
      return response.data
    },
    onSuccess: (_, variables) => {
      toast.success(
        variables.action === 'approve' ? 'Verifizierung genehmigt.' : 'Verifizierung abgelehnt.'
      )
      queryClient.invalidateQueries({ queryKey: ['admin-institutional-verifications'] })
      setSelectedRecord(null)
    },
    onError: (error: any) => {
      const message = error?.response?.data?.detail ?? 'Aktion fehlgeschlagen.'
      toast.error(message)
    },
  })

  const records = data?.verifications ?? []

  const summary = useMemo(() => {
    const total = data?.total ?? 0
    const pending = records.filter((item) => item.status === 'pending').length
    const approved = records.filter((item) => item.status === 'approved').length
    const rejected = records.filter((item) => item.status === 'rejected').length
    const cancelled = records.filter((item) => item.status === 'cancelled').length
    return { total, pending, approved, rejected, cancelled }
  }, [data, records])

  const filteredRecords = useMemo(() => {
    if (!searchTerm.trim()) return records
    const query = searchTerm.trim().toLowerCase()
    return records.filter((item) => {
      const org = ORGANIZATION_LABELS[item.organization_type] ?? item.organization_type
      return (
        item.user_id.toLowerCase().includes(query) ||
        org.toLowerCase().includes(query) ||
        (item.organization_name?.toLowerCase().includes(query) ?? false)
      )
    })
  }, [records, searchTerm])

  return (
    <div className="min-h-screen bg-gray-50 p-6 dark:bg-slate-950">
      <div className="mx-auto max-w-7xl space-y-6">
        <header className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <h1 className="flex items-center gap-3 text-3xl font-bold text-gray-900 dark:text-white">
              <ShieldCheck className="h-8 w-8 text-primary-600" />
              Institutional Verification Review
            </h1>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Verwaltung aller eingereichten institutionellen Nachweise – inkl. Dokumente, Status und Audit Trail.
            </p>
          </div>
          <button
            onClick={() => refetch()}
            className="inline-flex items-center gap-2 rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white shadow transition hover:bg-primary-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary-500"
          >
            <RefreshCw className={`h-4 w-4 ${isRefetching ? 'animate-spin' : ''}`} />
            Aktualisieren
          </button>
        </header>

        <section className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <div className="rounded-2xl bg-white p-5 shadow dark:bg-slate-900/80">
            <p className="text-xs uppercase text-gray-500 dark:text-gray-400">Anträge gesamt</p>
            <p className="mt-2 text-3xl font-semibold text-gray-900 dark:text-white">{summary.total}</p>
          </div>
          <div className="rounded-2xl bg-white p-5 shadow dark:bg-slate-900/80">
            <p className="text-xs uppercase text-amber-600">Pending</p>
            <p className="mt-2 text-3xl font-semibold text-amber-600">{summary.pending}</p>
          </div>
          <div className="rounded-2xl bg-white p-5 shadow dark:bg-slate-900/80">
            <p className="text-xs uppercase text-emerald-600">Genehmigt</p>
            <p className="mt-2 text-3xl font-semibold text-emerald-600">{summary.approved}</p>
          </div>
          <div className="rounded-2xl bg-white p-5 shadow dark:bg-slate-900/80">
            <p className="text-xs uppercase text-red-600">Abgelehnt / Storniert</p>
            <p className="mt-2 text-3xl font-semibold text-red-600">{summary.rejected + summary.cancelled}</p>
          </div>
        </section>

        <section className="rounded-2xl bg-white p-6 shadow dark:bg-slate-900/80">
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div className="flex flex-wrap items-center gap-2">
              <Filter className="h-5 w-5 text-gray-500" />
              {STATUS_FILTERS.map((filter) => (
                <button
                  key={filter.value}
                  onClick={() => setStatusFilter(filter.value as VerificationStatus | 'all')}
                  className={`rounded-full px-4 py-2 text-sm font-medium transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary-500 ${
                    statusFilter === filter.value
                      ? 'bg-primary-600 text-white shadow'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-slate-800 dark:text-gray-300 dark:hover:bg-slate-700'
                  }`}
                >
                  {filter.label}
                </button>
              ))}
            </div>

            <div className="relative w-full max-w-xs">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                value={searchTerm}
                onChange={(event) => setSearchTerm(event.target.value)}
                placeholder="Suche nach User-ID oder Organisation"
                className="w-full rounded-lg border border-gray-200 bg-white py-2 pl-9 pr-3 text-sm text-gray-700 shadow-sm focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500/40 dark:border-slate-700 dark:bg-slate-900 dark:text-gray-200"
              />
            </div>
          </div>

          <div className="mt-6">
            {isLoading ? (
              <TableSkeleton />
            ) : filteredRecords.length === 0 ? (
              <EmptyState onRefresh={() => refetch()} />
            ) : (
              <div className="space-y-3">
                {filteredRecords.map((record) => {
                  const badge = statusBadge(record.status)
                  return (
                    <motion.div
                      key={record.id}
                      initial={{ opacity: 0, y: 8 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm transition hover:border-primary-200 hover:shadow-lg dark:border-slate-700 dark:bg-slate-800"
                    >
                      <div className="flex flex-col gap-4 md:flex-row md:justify-between">
                        <div className="space-y-2">
                          <div className="flex items-center gap-3">
                            <span className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-semibold ${badge.className}`}>
                              {badge.icon}
                              {badge.label}
                            </span>
                            <span className="text-xs font-mono text-gray-400 dark:text-gray-500">#{record.id}</span>
                          </div>
                          <div>
                            <p className="text-sm font-semibold text-gray-900 dark:text-white">
                              {ORGANIZATION_LABELS[record.organization_type] ?? record.organization_type}
                            </p>
                            {record.organization_name && (
                              <p className="text-sm text-gray-600 dark:text-gray-300">{record.organization_name}</p>
                            )}
                          </div>
                          <div className="flex flex-wrap items-center gap-3 text-xs text-gray-500 dark:text-gray-400">
                            <span>Benutzer: {record.user_id}</span>
                            <span>Eingereicht: {formatDateTime(record.created_at)}</span>
                            {record.reviewed_at && <span>Entscheid: {formatDateTime(record.reviewed_at)}</span>}
                          </div>
                          {(record.admin_notes || record.rejection_reason) && (
                            <div className="rounded-lg bg-gray-50 p-3 text-sm text-gray-600 dark:bg-slate-900 dark:text-gray-300">
                              {record.admin_notes && (
                                <p className="mb-1">
                                  <span className="font-medium text-gray-700 dark:text-gray-200">Admin-Notiz:</span>{' '}
                                  {record.admin_notes}
                                </p>
                              )}
                              {record.rejection_reason && (
                                <p>
                                  <span className="font-medium text-gray-700 dark:text-gray-200">Ablehnungsgrund:</span>{' '}
                                  {record.rejection_reason}
                                </p>
                              )}
                            </div>
                          )}
                        </div>

                        <div className="flex flex-col items-start justify-between gap-2">
                          <div className="flex flex-col items-start gap-2">
                            {record.document?.url && (
                              <a
                                href={record.document.url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="inline-flex items-center gap-2 rounded-lg border border-gray-200 px-3 py-2 text-sm font-medium text-gray-700 transition hover:border-primary-200 hover:text-primary-600 focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary-500 dark:border-slate-600 dark:text-gray-200 dark:hover:border-primary-400 dark:hover:text-primary-200"
                              >
                                <FileText className="h-4 w-4" /> Dokument öffnen
                              </a>
                            )}
                          </div>

                          {record.status === 'pending' && (
                            <button
                              onClick={() => setSelectedRecord(record)}
                              className="inline-flex items-center gap-2 rounded-lg bg-primary-600 px-3 py-2 text-sm font-medium text-white shadow transition hover:bg-primary-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary-500"
                            >
                              Review starten
                            </button>
                          )}
                        </div>
                      </div>
                    </motion.div>
                  )
                })}
              </div>
            )}
          </div>
        </section>
      </div>

      {selectedRecord && (
        <VerificationReviewDialog
          record={selectedRecord}
          onClose={() => setSelectedRecord(null)}
          isSubmitting={reviewMutation.isPending}
          onSubmit={(payload) => reviewMutation.mutate({
            verificationId: selectedRecord.id,
            ...payload,
          })}
        />
      )}
    </div>
  )
}
