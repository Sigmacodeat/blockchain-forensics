/**
 * Institutional Discount Verification Page
 * User kann hier den Status seiner Verification prüfen und Dokumente hochladen
 */

import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  Shield,
  Upload,
  CheckCircle,
  Clock,
  XCircle,
  FileText,
  AlertCircle,
  ArrowLeft,
  Loader2,
} from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'
import toast from 'react-hot-toast'
import clsx from 'clsx'

type VerificationStatus = 'none' | 'pending' | 'approved' | 'rejected'

interface VerificationResponse {
  success: boolean
  has_verification: boolean
  status: VerificationStatus
  can_request: boolean
  verification?: {
    id: number
    status: VerificationStatus
    organization_type: string | null
    organization_name: string | null
    admin_notes: string | null
    rejection_reason: string | null
    document?: {
      type: string | null
      url: string | null
      filename: string | null
      metadata?: Record<string, unknown>
    }
  }
}

const ORGANIZATION_TYPES: { value: string; label: string; description: string }[] = [
  { value: 'police', label: 'Polizei / Law Enforcement', description: 'Offizielle Strafverfolgungsbehörden' },
  { value: 'detective', label: 'Privatdetektiv', description: 'Lizensierte Ermittler/Forensiker' },
  { value: 'lawyer', label: 'Anwalt / Kanzlei', description: 'Juristen mit Blockchain-Schwerpunkt' },
  { value: 'government', label: 'Regierungsbehörde', description: 'Staatliche Ermittlungsbehörden' },
  { value: 'exchange', label: 'Exchange / VASP', description: 'Lizenzierte Kryptobörsen' },
  { value: 'other', label: 'Andere Institution', description: 'Enterprise Compliance / Audit Teams' },
]

const FILE_SIZE_LIMIT_MB = 10
const FILE_SIZE_LIMIT_BYTES = FILE_SIZE_LIMIT_MB * 1024 * 1024

const ALLOWED_MIME_TYPES = new Set([
  'application/pdf',
  'image/jpeg',
  'image/png',
  'application/msword',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
])

const ALLOWED_EXTENSIONS = ['.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx']

const STATUS_CONFIG: Record<VerificationStatus, {
  icon: typeof Shield
  gradient: string
  title: string
  description: string
}> = {
  none: {
    icon: Shield,
    gradient: 'from-slate-500 to-slate-600',
    title: '📄 Verifizierung starten',
    description: 'Beantragen Sie Ihren 10% Institutionen-Rabatt und laden Sie Nachweise hoch.',
  },
  pending: {
    icon: Clock,
    gradient: 'from-blue-500 to-purple-500',
    title: '⏳ Verifizierung läuft',
    description: 'Unser Team prüft Ihre Unterlagen. Antwort innerhalb von 24–48 Stunden.',
  },
  approved: {
    icon: CheckCircle,
    gradient: 'from-green-500 to-emerald-500',
    title: '🎉 Verifizierung bestätigt',
    description: 'Ihr institutioneller Rabatt ist aktiv. Vielen Dank für das Vertrauen!',
  },
  rejected: {
    icon: XCircle,
    gradient: 'from-red-500 to-orange-500',
    title: '❌ Verifizierung abgelehnt',
    description: 'Bitte korrigieren Sie Ihre Unterlagen oder kontaktieren Sie unser Team.',
  },
}

interface UploadState {
  file: File
  progress: number
  state: 'uploading' | 'success' | 'error'
  error?: string
}

export default function VerificationPage() {
  const navigate = useNavigate()
  const { user } = useAuth()

  const queryClient = useQueryClient()
  const [organizationType, setOrganizationType] = useState('')
  const [organizationName, setOrganizationName] = useState('')
  const [pendingUploads, setPendingUploads] = useState<UploadState[]>([])
  const [documentType, setDocumentType] = useState('official_id')
  const [ariaLiveMessage, setAriaLiveMessage] = useState('')

  const {
    data: verification,
    isLoading: isStatusLoading,
    isRefetching,
    refetch: refetchStatus,
  } = useQuery<VerificationResponse>({
    queryKey: ['institutional-verification', user?.id],
    queryFn: async () => {
      const response = await api.get('/api/v1/verification/status')
      return response.data
    },
    enabled: Boolean(user?.id),
    staleTime: 30_000,
    retry: 1,
  })

  const requestVerificationMutation = useMutation({
    mutationFn: async (payload: { organization_type: string; organization_name?: string }) => {
      const response = await api.post('/api/v1/verification/request', payload)
      return response.data
    },
    onSuccess: () => {
      toast.success('Verifizierungsanfrage erfolgreich eingereicht.')
      setAriaLiveMessage('Verifizierungsanfrage erfolgreich eingereicht.')
      queryClient.invalidateQueries({ queryKey: ['institutional-verification'] })
      setOrganizationName('')
      setOrganizationType('')
    },
    onError: (error: any) => {
      const message = error?.response?.data?.detail ?? 'Verifizierungsanfrage fehlgeschlagen.'
      toast.error(message)
      setAriaLiveMessage(`Fehler: ${message}`)
    },
  })

  const uploadDocumentMutation = useMutation({
    mutationFn: async (payload: { verificationId: number; documentType: string; file: File }) => {
      const formData = new FormData()
      formData.append('document_type', payload.documentType)
      formData.append('file', payload.file)

      const response = await api.post(`/api/v1/verification/${payload.verificationId}/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      return response.data
    },
    onSuccess: () => {
      toast.success('Dokument erfolgreich hochgeladen.')
      setAriaLiveMessage('Dokument erfolgreich hochgeladen.')
      refetchStatus()
    },
    onError: (error: any) => {
      const message = error?.response?.data?.detail ?? 'Upload fehlgeschlagen.'
      toast.error(message)
      setAriaLiveMessage(`Upload fehlgeschlagen: ${message}`)
    },
  })

  const reviewStatus = verification?.status ?? 'none'
  const statusConfig = STATUS_CONFIG[reviewStatus]
  const StatusIcon = statusConfig.icon

  const canRequest = verification?.can_request ?? reviewStatus === 'none'
  const currentVerification = verification?.verification

  const handleSubmitRequest = () => {
    if (!organizationType) {
      toast.error('Bitte wählen Sie Ihren Organisationstyp aus.')
      return
    }

    requestVerificationMutation.mutate({
      organization_type: organizationType,
      organization_name: organizationName.trim() || undefined,
    })
  }

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    if (!currentVerification || !event.target.files?.length) {
      return
    }

    const file = event.target.files[0]
    event.target.value = ''

    if (!ALLOWED_MIME_TYPES.has(file.type)) {
      const message = `Dateityp nicht erlaubt. Erlaubt: ${ALLOWED_EXTENSIONS.join(', ')}`
      toast.error(message)
      setAriaLiveMessage(message)
      return
    }

    if (file.size > FILE_SIZE_LIMIT_BYTES) {
      const message = `Datei zu groß. Maximal ${FILE_SIZE_LIMIT_MB}MB`
      toast.error(message)
      setAriaLiveMessage(message)
      return
    }

    const uploadState: UploadState = {
      file,
      progress: 0,
      state: 'uploading',
    }
    setPendingUploads((prev) => [...prev, uploadState])

    try {
      await uploadDocumentMutation.mutateAsync({
        verificationId: currentVerification.id,
        documentType,
        file,
      })

      setPendingUploads((prev) =>
        prev.map((item) =>
          item.file === file
            ? { ...item, state: 'success', progress: 100 }
            : item
        )
      )
    } catch (error: any) {
      const detail = error?.response?.data?.detail ?? 'Upload fehlgeschlagen.'
      setPendingUploads((prev) =>
        prev.map((item) =>
          item.file === file
            ? { ...item, state: 'error', error: detail }
            : item
        )
      )
    }
  }

  const currentUploads = useMemo(() => {
    const document = currentVerification?.document
    const hasSuccessfulUpload = Boolean(document?.filename && document?.url)

    if (hasSuccessfulUpload && document?.filename && document?.url) {
      return [
        {
          label: document.filename,
          state: 'success' as const,
          url: document.url,
          date: document.metadata?.uploaded_at as string | undefined,
        },
        ...pendingUploads.map((upload) => ({
          label: upload.file.name,
          state: upload.state,
          error: upload.error,
        })),
      ]
    }

    return pendingUploads.map((upload) => ({
      label: upload.file.name,
      state: upload.state,
      error: upload.error,
    }))
  }, [currentVerification, pendingUploads])

  const isLoading = isStatusLoading || requestVerificationMutation.isPending
  const noVerificationYet = reviewStatus === 'none' && !verification?.has_verification

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 via-white to-primary-50 dark:from-gray-950 dark:via-gray-900 dark:to-gray-950 py-12 px-4" aria-live="polite">
      <div className="max-w-3xl mx-auto">
        <span className="sr-only" role="status" aria-live="polite">
          {ariaLiveMessage}
        </span>
        {/* Back Button */}
        <button
          onClick={() => navigate(-1)}
          className="mb-6 inline-flex items-center gap-2 rounded-lg px-2 py-1 text-gray-600 outline-offset-2 transition hover:text-primary-600 focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary-500 dark:text-gray-400 dark:hover:text-primary-400"
          aria-label="Zurück"
        >
          <ArrowLeft className="w-4 h-4" />
          Zurück
        </button>

        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-8"
        >
          <div className={`inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br ${statusConfig.gradient} rounded-2xl mb-4 shadow-lg`} role="img" aria-label={statusConfig.title}>
            <StatusIcon className="w-12 h-12 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
            {statusConfig.title}
          </h1>
          <p className="text-gray-600 dark:text-gray-300">
            {statusConfig.description}
          </p>
        </motion.div>

        {/* Status Card */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="card p-8 rounded-2xl border border-gray-200/60 dark:border-gray-700/60 bg-white/80 dark:bg-gray-900/60 backdrop-blur shadow-2xl mb-6"
        >
          {/* Status Informationen */}
          <div className="mb-6">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="bg-primary-50 dark:bg-primary-500/10 rounded-xl p-4 border border-primary-100 dark:border-primary-500/30">
                <h3 className="font-semibold text-primary-900 dark:text-primary-100 mb-2">
                  Rabatt für Institutionen
                </h3>
                <p className="text-sm text-primary-800 dark:text-primary-100/80">
                  <strong>10% zusätzlicher Rabatt</strong> auf alle Pläne für Ermittler, Behörden und Compliance-Teams.
                </p>
              </div>

              <div className="bg-slate-50 dark:bg-slate-800/60 rounded-xl p-4 border border-slate-200 dark:border-slate-700">
                <h3 className="font-semibold text-slate-900 dark:text-slate-100 mb-2">Bearbeitungszeit</h3>
                <p className="text-sm text-slate-600 dark:text-slate-300">
                  Prüfungen erfolgen in der Regel innerhalb von <strong>24–48 Stunden</strong>. Bei dringenden Anfragen kontaktieren Sie uns bitte direkt.
                </p>
              </div>
            </div>
          </div>

          {/* Savings Info */}
          {reviewStatus !== 'approved' && (
            <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4 mb-6">
              <h3 className="font-semibold text-blue-900 dark:text-blue-100 mb-2">
                💰 Ihre potenzielle Ersparnis:
              </h3>
              <div className="grid grid-cols-3 gap-4 text-sm">
                <div>
                  <div className="text-blue-700 dark:text-blue-300">Jahresrabatt</div>
                  <div className="text-xl font-bold text-blue-900 dark:text-blue-100">20%</div>
                </div>
                <div>
                  <div className="text-blue-700 dark:text-blue-300">Institutionell</div>
                  <div className="text-xl font-bold text-blue-900 dark:text-blue-100">+10%</div>
                </div>
                <div>
                  <div className="text-blue-700 dark:text-blue-300">Gesamt</div>
                  <div className="text-xl font-bold text-blue-900 dark:text-blue-100">30%</div>
                </div>
              </div>
              <p className="text-xs text-blue-700 dark:text-blue-300 mt-2">
                Pro Plan: $855/Jahr (statt $1,188) → Sie sparen $333!
              </p>
            </div>
          )}

          {/* Request Section */}
          {canRequest && (
            <div className="mb-10">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Antrag einreichen
              </h3>
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    Organisationstyp
                  </label>
                  <select
                    value={organizationType}
                    onChange={(event) => setOrganizationType(event.target.value)}
                    className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 shadow-sm focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500/40 dark:border-gray-700 dark:bg-gray-900 dark:text-white"
                    aria-label="Organisationstyp auswählen"
                  >
                    <option value="">Wählen Sie eine Option…</option>
                    {ORGANIZATION_TYPES.map((type) => (
                      <option key={type.value} value={type.value}>
                        {type.label}
                      </option>
                    ))}
                  </select>
                  {organizationType && (
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      {ORGANIZATION_TYPES.find((type) => type.value === organizationType)?.description}
                    </p>
                  )}
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    Organisation (optional)
                  </label>
                  <input
                    type="text"
                    value={organizationName}
                    onChange={(event) => setOrganizationName(event.target.value)}
                    placeholder="z. B. Bundeskriminalamt, ChainSecurity GmbH"
                    className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 shadow-sm focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500/40 dark:border-gray-700 dark:bg-gray-900 dark:text-white"
                    aria-label="Name der Organisation"
                  />
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    Optional, hilft uns beim schnelleren Abgleich Ihrer Anfrage.
                  </p>
                </div>
              </div>

              <button
                onClick={handleSubmitRequest}
                disabled={requestVerificationMutation.isPending}
                className="mt-6 inline-flex items-center justify-center gap-2 rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white shadow transition hover:bg-primary-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary-500 disabled:cursor-not-allowed disabled:bg-gray-400"
                aria-live="polite"
              >
                {requestVerificationMutation.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
                Antrag abschicken
              </button>
            </div>
          )}

          {/* Upload Section */}
          {(reviewStatus === 'pending' || reviewStatus === 'none' || currentVerification) && (
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                📤 Dokumente hochladen
              </h3>
              <div className="mb-4 grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <label htmlFor="document-type" className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    Dokumententyp
                  </label>
                  <select
                    id="document-type"
                    value={documentType}
                    onChange={(event) => setDocumentType(event.target.value)}
                    className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 shadow-sm focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500/40 dark:border-gray-700 dark:bg-gray-900 dark:text-white"
                    aria-label="Dokumententyp auswählen"
                  >
                    <option value="official_id">Offizieller Dienstausweis</option>
                    <option value="employment_letter">Beschäftigungsnachweis</option>
                    <option value="license">Lizenz / Zulassung</option>
                    <option value="other">Sonstiger Nachweis</option>
                  </select>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    Dokumente werden verschlüsselt gespeichert und nur für Verifikationszwecke genutzt.
                  </p>
                </div>

                {currentVerification?.document?.url && (
                  <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-900 dark:border-emerald-800/50 dark:bg-emerald-900/20 dark:text-emerald-100">
                    <p className="font-semibold">Aktuell hinterlegte Datei</p>
                    <p className="mt-1 truncate" title={currentVerification.document.filename ?? undefined}>
                      {currentVerification.document.filename}
                    </p>
                    <a
                      href={currentVerification.document.url ?? undefined}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="mt-2 inline-flex items-center gap-2 text-sm font-medium text-emerald-700 underline transition hover:text-emerald-900 dark:text-emerald-200 dark:hover:text-emerald-100"
                    >
                      Dokument anzeigen / herunterladen
                    </a>
                  </div>
                )}
              </div>

              <div className="border-2 border-dashed border-gray-300 dark:border-gray-700 rounded-lg p-8 text-center hover:border-primary-500 transition">
                <input
                  type="file"
                  id="document-upload"
                  accept={ALLOWED_EXTENSIONS.join(',')}
                  onChange={handleFileUpload}
                  className="hidden"
                  disabled={uploadDocumentMutation.isPending || !currentVerification}
                />
                <label
                  htmlFor="document-upload"
                  className={clsx('block cursor-pointer', {
                    'opacity-50 cursor-not-allowed': uploadDocumentMutation.isPending || !currentVerification,
                  })}
                  tabIndex={uploadDocumentMutation.isPending || !currentVerification ? -1 : 0}
                  onKeyDown={(event) => {
                    if (event.key === 'Enter' || event.key === ' ') {
                      event.preventDefault()
                      if (!uploadDocumentMutation.isPending && currentVerification) {
                        document.getElementById('document-upload')?.click()
                      }
                    }
                  }}
                >
                  <Upload className="w-12 h-12 text-gray-400 dark:text-gray-500 mx-auto mb-4" />
                  <p className="text-gray-700 dark:text-gray-300 font-medium mb-2">
                    Datei auswählen (PDF, JPG, PNG, DOC)
                  </p>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    Maximal {FILE_SIZE_LIMIT_MB}MB pro Upload
                  </p>
                  {!currentVerification && (
                    <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">
                      Reichen Sie zunächst einen Antrag ein, um Dokumente hochladen zu können.
                    </p>
                  )}
                </label>
              </div>

              {currentUploads.length > 0 && (
                <div className="mt-4 space-y-2">
                  {currentUploads.map((item, index) => (
                    <div
                      key={`${item.label}-${index}`}
                      className="flex items-center gap-3 rounded-lg bg-gray-50 p-3 dark:bg-gray-800"
                      role="status"
                    >
                      <FileText className="h-5 w-5 text-primary-600" />
                      <span className="flex-1 text-sm text-gray-700 dark:text-gray-300">
                        {item.label}
                      </span>
                      {item.state === 'uploading' && (
                        <Loader2 className="h-5 w-5 animate-spin text-primary-600" />
                      )}
                      {item.state === 'success' && <CheckCircle className="h-5 w-5 text-green-600" />}
                      {item.state === 'error' && (
                        <div className="flex items-center gap-2 text-sm text-red-600 dark:text-red-400">
                          <AlertCircle className="h-4 w-4" />
                          <span>{item.error ?? 'Upload fehlgeschlagen'}</span>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Accepted Documents */}
          <div className="bg-gray-50 dark:bg-gray-800/50 rounded-lg p-4">
            <h4 className="font-semibold text-gray-900 dark:text-white mb-3">
              ✅ Akzeptierte Dokumente:
            </h4>
            <ul className="text-sm text-gray-700 dark:text-gray-300 space-y-2">
              <li className="flex items-start gap-2">
                <CheckCircle className="w-4 h-4 text-green-600 mt-0.5 flex-shrink-0" />
                <span><strong>Polizei:</strong> Dienstausweis, Badge, Behörden-Email</span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle className="w-4 h-4 text-green-600 mt-0.5 flex-shrink-0" />
                <span><strong>Detektive:</strong> Gewerbelizenz, IHK-Nachweis, Zulassung</span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle className="w-4 h-4 text-green-600 mt-0.5 flex-shrink-0" />
                <span><strong>Anwälte:</strong> Anwaltszulassung, BAR Association</span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle className="w-4 h-4 text-green-600 mt-0.5 flex-shrink-0" />
                <span><strong>Regierungen:</strong> Dienstausweis, Behörden-ID</span>
              </li>
            </ul>
          </div>

          {/* Error Message */}
          {(verification?.verification?.admin_notes || verification?.verification?.rejection_reason) && (
            <div className="mt-6 space-y-3">
              {verification.verification.admin_notes && (
                <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 dark:border-amber-800/60 dark:bg-amber-900/20">
                  <h4 className="mb-2 flex items-center gap-2 text-sm font-semibold text-amber-900 dark:text-amber-200">
                    <AlertCircle className="h-4 w-4" /> Hinweise vom Review-Team
                  </h4>
                  <p className="text-sm text-amber-700 dark:text-amber-100/80">
                    {verification.verification.admin_notes}
                  </p>
                </div>
              )}
              {verification.verification.rejection_reason && (
                <div className="rounded-lg border border-red-200 bg-red-50 p-4 dark:border-red-800/60 dark:bg-red-900/20">
                  <h4 className="mb-2 flex items-center gap-2 text-sm font-semibold text-red-900 dark:text-red-100">
                    <AlertCircle className="h-4 w-4" /> Grund für Ablehnung
                  </h4>
                  <p className="text-sm text-red-700 dark:text-red-100/80">
                    {verification.verification.rejection_reason}
                  </p>
                </div>
              )}
            </div>
          )}
        </motion.div>

        {/* Help Section */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
          className="text-center text-sm text-gray-600 dark:text-gray-400"
        >
          <p className="mb-2">
            Fragen? Kontaktieren Sie uns:
          </p>
          <div className="flex justify-center gap-4">
            <a
              href="mailto:verify@sigmacode.io"
              className="text-primary-600 dark:text-primary-400 hover:underline"
            >
              verify@sigmacode.io
            </a>
            <span>•</span>
            <button
              onClick={() => toast('Chat Support in Vorbereitung – wir melden uns in Kürze!')}
              className="text-primary-600 dark:text-primary-400 hover:underline"
            >
              Chat Support
            </button>
          </div>
        </motion.div>
      </div>
    </div>
  )
}
