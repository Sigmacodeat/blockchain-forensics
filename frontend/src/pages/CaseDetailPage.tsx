import { useCallback, useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { ArrowLeft, Download, Shield, CheckCircle, FileText, Users, MessageSquare, Plus } from 'lucide-react'
import { useCase, useCaseExport, useCaseExportCsv, useCaseChecksum, useVerifyCase } from '@/hooks/useCases'
import { useCollaborationWorkspace } from '@/hooks/useCollaborationWorkspace'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { useToastSuccess, useToastError } from '@/components/ui/toast'
import { EntityForm, EvidenceForm, AttachmentUpload } from '@/components/case'
import type { Case as CaseType } from '@/types/case'

type TabId = 'overview' | 'entities' | 'evidence' | 'attachments'

const STATUS_LABELS: Record<string, string> = {
  active: 'Active',
  closed: 'Closed',
  archived: 'Archived',
  pending: 'Pending',
}

const formatDate = (value?: string | null) => {
  if (!value) return '—'
  try {
    return new Date(value).toLocaleString()
  } catch (err) {
    return value
  }
}

export default function CaseDetailPage() {
  const { caseId, lang } = useParams<{ caseId: string; lang?: string }>()
  const navigate = useNavigate()

  const [activeTab, setActiveTab] = useState<TabId>('overview')
  const [showEntityForm, setShowEntityForm] = useState(false)
  const [showEvidenceForm, setShowEvidenceForm] = useState(false)
  const [showAttachmentForm, setShowAttachmentForm] = useState(false)
  const [noteDraft, setNoteDraft] = useState('')

  const { data: caseResponse, isLoading, error } = useCase(caseId ?? '')
  const { data: exportData } = useCaseExport(caseId ?? '')
  const { data: csvData } = useCaseExportCsv(caseId ?? '')
  const { data: checksumData } = useCaseChecksum(caseId ?? '')
  const verifyCase = useVerifyCase()
  const showSuccess = useToastSuccess()
  const showError = useToastError()

  const collab = useCollaborationWorkspace({ caseId: caseId ?? null, enabled: Boolean(caseId) })

  const caseRecord: CaseType | undefined = useMemo(() => {
    if (!caseResponse) return undefined
    return (caseResponse.case || caseResponse.case_) as CaseType | undefined
  }, [caseResponse])

  const exportPayload = exportData?.export

  const handleBack = useCallback(() => {
    const locale = lang || 'en'
    navigate(`/${locale}/cases`)
  }, [lang, navigate])

  const handleExport = useCallback(
    (format: 'json' | 'csv') => {
      if (!caseId) return

      if (format === 'json' && exportData?.export) {
        const blob = new Blob([JSON.stringify(exportData.export, null, 2)], { type: 'application/json' })
        const url = URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        link.download = `${caseId}_export.json`
        link.click()
        URL.revokeObjectURL(url)
        showSuccess('Export erstellt', 'Der JSON-Export wurde heruntergeladen.')
        return
      }

      if (format === 'csv' && csvData) {
        const files: Array<{ name: string; content?: string }> = [
          { name: `${caseId}_entities.csv`, content: csvData.entities_csv },
          { name: `${caseId}_evidence.csv`, content: csvData.evidence_csv },
        ]

        let downloaded = false
        files.forEach(({ name, content }) => {
          if (content) {
            const blob = new Blob([content], { type: 'text/csv' })
            const url = URL.createObjectURL(blob)
            const link = document.createElement('a')
            link.href = url
            link.download = name
            link.click()
            URL.revokeObjectURL(url)
            downloaded = true
          }
        })

        if (downloaded) {
          showSuccess('Export erstellt', 'CSV-Export wurde heruntergeladen.')
        } else {
          showError('Keine Daten', 'Es stehen keine CSV-Daten zur Verfügung.')
        }
      }
    },
    [caseId, exportData, csvData, showSuccess, showError]
  )

  const handleVerify = useCallback(async () => {
    if (!caseId || !exportPayload) return

    try {
      await verifyCase.mutateAsync({
        caseId,
        checksum: exportPayload.checksum_sha256,
        signature: exportPayload.signature_hmac_sha256,
      })
      showSuccess('Verifikation erfolgreich', 'Checksumme und Signatur wurden geprüft.')
    } catch (err) {
      console.error(err)
      showError('Verifikation fehlgeschlagen', 'Bitte prüfe die Angaben und versuche es erneut.')
    }
  }, [caseId, exportPayload, verifyCase, showSuccess, showError])

  const handleSubmitNote = useCallback(
    (event: React.FormEvent<HTMLFormElement>) => {
      event.preventDefault()
      const trimmed = noteDraft.trim()
      if (!trimmed) return
      collab.sendNote(trimmed)
      setNoteDraft('')
    },
    [noteDraft, collab]
  )

  if (isLoading) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-br from-slate-50 via-blue-50 to-purple-50 dark:from-slate-900 dark:via-slate-950 dark:to-slate-900">
        <div className="animate-spin h-12 w-12 rounded-full border-b-2 border-primary" aria-label="Ladevorgang" />
        <p className="mt-4 text-sm text-slate-600 dark:text-slate-300">Lade Falldetails ...</p>
      </div>
    )
  }

  if (error || !caseRecord) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-br from-slate-50 via-blue-50 to-purple-50 dark:from-slate-900 dark:via-slate-950 dark:to-slate-900">
        <Card className="max-w-md w-full border-red-200 dark:border-red-800 bg-white/80 dark:bg-slate-900/80 backdrop-blur">
          <CardHeader>
            <CardTitle className="text-red-600 dark:text-red-300">Fall nicht gefunden</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-slate-600 dark:text-slate-300">
              Der angeforderte Fall konnte nicht geladen werden. Bitte überprüfe die URL oder versuche es später erneut.
            </p>
            <Button onClick={handleBack}>
              <ArrowLeft className="mr-2 h-4 w-4" />
              Zurück zur Übersicht
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  const integrityCards = [
    { label: 'SHA-256 Checksum', value: exportPayload?.checksum_sha256 },
    { label: 'Vorherige Checksum', value: exportPayload?.prev_checksum_sha256 },
    { label: 'HMAC Signature', value: exportPayload?.signature_hmac_sha256 },
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-slate-100 dark:from-slate-900 dark:via-slate-950 dark:to-black">
      <div className="mx-auto w-full max-w-6xl px-4 py-8 lg:px-6">
        <div className="mb-6 flex flex-wrap items-center gap-4">
          <Button variant="outline" onClick={handleBack}>
            <ArrowLeft className="mr-2 h-4 w-4" />
            Zurück
          </Button>
          <div>
            <h1 className="text-3xl font-semibold text-slate-900 dark:text-white">{caseRecord.title}</h1>
            <p className="text-sm text-slate-500 dark:text-slate-400">Case-ID: {caseRecord.case_id}</p>
          </div>
          <Badge variant="secondary" className="ml-auto text-xs uppercase tracking-wide">
            {STATUS_LABELS[caseRecord.status] ?? caseRecord.status}
          </Badge>
        </div>

        <div className="grid gap-6 lg:grid-cols-[2fr_1fr]">
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Falldetails</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4 text-sm text-slate-700 dark:text-slate-300">
                <p>{caseRecord.description || 'Keine Beschreibung vorhanden.'}</p>
                <div className="grid gap-3 sm:grid-cols-2">
                  <DetailRow label="Lead Investigator" value={caseRecord.lead_investigator} />
                  <DetailRow label="Erstellt am" value={formatDate(caseRecord.created_at)} />
                  <DetailRow label="Status" value={STATUS_LABELS[caseRecord.status] ?? caseRecord.status} />
                  <DetailRow label="Checksum" value={checksumData?.checksum_sha256} mono />
                </div>
              </CardContent>
            </Card>

            {exportPayload && (
              <Card>
                <CardHeader className="flex flex-row items-center gap-3">
                  <Shield className="h-5 w-5 text-indigo-500" />
                  <CardTitle>Integrität & Export</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid gap-4 md:grid-cols-2">
                    {integrityCards.map(({ label, value }) => (
                      <DetailStack key={label} label={label} value={value} mono />
                    ))}
                  </div>

                  <div className="flex flex-wrap gap-2">
                    <Button onClick={handleVerify} disabled={verifyCase.isPending}>
                      <CheckCircle className="mr-2 h-4 w-4" />
                      {verifyCase.isPending ? 'Prüfe ...' : 'Integrität prüfen'}
                    </Button>
                    <Button variant="outline" onClick={() => handleExport('json')}>
                      <Download className="mr-2 h-4 w-4" />
                      JSON Export
                    </Button>
                    <Button variant="outline" onClick={() => handleExport('csv')}>
                      <Download className="mr-2 h-4 w-4" />
                      CSV Export
                    </Button>
                  </div>

                  {verifyCase.data && (
                    <div className="flex items-center gap-2 rounded-md border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700 dark:border-emerald-900 dark:bg-emerald-900/40 dark:text-emerald-200">
                      <CheckCircle className="h-4 w-4" />
                      Checksumme {verifyCase.data.match ? 'bestätigt' : 'abweichend'} · Signatur {verifyCase.data.signature_match ? 'gültig' : 'ungültig'}
                    </div>
                  )}
                </CardContent>
              </Card>
            )}

            {exportPayload?.entities && exportPayload.entities.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>Verbundene Entitäten</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3 text-sm text-slate-700 dark:text-slate-300">
                  {exportPayload.entities.map((entity: any, idx: number) => (
                    <div key={`${entity.address}-${idx}`} className="rounded-md border border-slate-200 bg-white/80 p-3 dark:border-slate-700 dark:bg-slate-900/70">
                      <div className="font-mono text-xs text-slate-500 dark:text-slate-400">{entity.address}</div>
                      <div className="text-sm font-semibold">{entity.chain}</div>
                      {entity.labels && Object.keys(entity.labels).length > 0 && (
                        <div className="mt-2 flex flex-wrap gap-2">
                          {Object.entries(entity.labels).map(([key, value]) => (
                            <Badge key={key} variant="outline">
                              {key}: {String(value)}
                            </Badge>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </CardContent>
              </Card>
            )}

            {exportPayload?.evidence && exportPayload.evidence.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>Verknüpfte Evidenz</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3 text-sm text-slate-700 dark:text-slate-300">
                  {exportPayload.evidence.map((item: any, idx: number) => (
                    <div key={`${item.resource_id}-${idx}`} className="rounded-md border border-slate-200 bg-white/80 p-3 dark:border-slate-700 dark:bg-slate-900/70">
                      <div className="font-semibold">{item.resource_type}</div>
                      <div className="font-mono text-xs text-slate-500 dark:text-slate-400">{item.resource_id}</div>
                      {item.notes && <p className="mt-1 text-sm">{item.notes}</p>}
                    </div>
                  ))}
                </CardContent>
              </Card>
            )}
          </div>

          <aside className="space-y-6">
            <CollaborationPanel
              connected={collab.state.connected}
              participants={collab.state.participants}
              notes={collab.state.notes}
              error={collab.state.error}
              noteDraft={noteDraft}
              setNoteDraft={setNoteDraft}
              onSubmit={handleSubmitNote}
            />

            <Card>
              <CardHeader>
                <CardTitle>Aktionen</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <Button variant="outline" className="w-full" onClick={() => setShowEntityForm(true)}>
                  <Plus className="mr-2 h-4 w-4" /> Entität hinzufügen
                </Button>
                <Button variant="outline" className="w-full" onClick={() => setShowEvidenceForm(true)}>
                  <Plus className="mr-2 h-4 w-4" /> Evidenz verknüpfen
                </Button>
                <Button variant="outline" className="w-full" onClick={() => setShowAttachmentForm(true)}>
                  <Plus className="mr-2 h-4 w-4" /> Anhang hochladen
                </Button>
              </CardContent>
            </Card>
          </aside>
        </div>

        {showEntityForm && (
          <EntityForm
            caseId={caseId ?? ''}
            onSuccess={() => {
              setShowEntityForm(false)
              showSuccess('Entität erstellt', 'Die Entität wurde erfolgreich hinzugefügt.')
            }}
            onCancel={() => setShowEntityForm(false)}
          />
        )}

        {showEvidenceForm && (
          <EvidenceForm
            caseId={caseId ?? ''}
            onSuccess={() => {
              setShowEvidenceForm(false)
              showSuccess('Evidenz verknüpft', 'Der Beleg wurde erfolgreich verknüpft.')
            }}
            onCancel={() => setShowEvidenceForm(false)}
          />
        )}

        {showAttachmentForm && (
          <AttachmentUpload
            caseId={caseId ?? ''}
            onSuccess={() => setShowAttachmentForm(false)}
            onCancel={() => setShowAttachmentForm(false)}
          />
        )}
      </div>
    </div>
  )
}

interface DetailRowProps {
  label: string
  value?: string | null
  mono?: boolean
}

const DetailRow = ({ label, value, mono }: DetailRowProps) => (
  <div>
    <p className="text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">{label}</p>
    <p className={`${mono ? 'font-mono text-xs' : 'text-sm font-semibold'} text-slate-900 dark:text-white`}>{value ?? '—'}</p>
  </div>
)

interface DetailStackProps extends DetailRowProps {}

const DetailStack = ({ label, value, mono }: DetailStackProps) => (
  <div className="rounded-lg border border-slate-200 bg-white/80 p-3 text-sm dark:border-slate-700 dark:bg-slate-900/70">
    <p className="text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">{label}</p>
    <p className={`${mono ? 'font-mono break-all text-xs' : 'text-sm font-medium'} text-slate-900 dark:text-white mt-1`}>
      {value ?? '—'}
    </p>
  </div>
)

interface CollaborationPanelProps {
  connected: boolean
  participants: Array<{ user_id: string; user_name: string; joined_at: string }>
  notes: Array<{ id: string; user_name: string; text: string; created_at: string }>
  error?: string | null
  noteDraft: string
  setNoteDraft: (value: string) => void
  onSubmit: (event: React.FormEvent<HTMLFormElement>) => void
}

const CollaborationPanel = ({ connected, participants, notes, error, noteDraft, setNoteDraft, onSubmit }: CollaborationPanelProps) => (
  <Card className="border-indigo-100 bg-white/90 shadow-lg dark:border-indigo-900/50 dark:bg-slate-900/80">
    <CardHeader className="flex flex-row items-center justify-between">
      <div className="flex items-center gap-2">
        <Users className="h-5 w-5 text-indigo-500" />
        <CardTitle className="text-base">Collaboration Workspace</CardTitle>
      </div>
      <Badge variant={connected ? 'outline' : 'secondary'} className="flex items-center gap-1">
        <span className={`h-2 w-2 rounded-full ${connected ? 'bg-emerald-500 animate-pulse' : 'bg-slate-400'}`} />
        {connected ? 'Live' : 'Offline'}
      </Badge>
    </CardHeader>
    <CardContent className="space-y-4">
      <section>
        <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-indigo-500">Aktive Analyst:innen</h3>
        {participants.length === 0 ? (
          <p className="text-xs text-slate-500 dark:text-slate-400">Noch niemand verbunden.</p>
        ) : (
          <div className="flex flex-wrap gap-2">
            {participants.map((participant) => (
              <Badge key={participant.user_id} variant="outline" className="bg-indigo-50 text-indigo-700 dark:bg-indigo-900/40 dark:text-indigo-200">
                {participant.user_name}
              </Badge>
            ))}
          </div>
        )}
      </section>

      <section className="space-y-2">
        <h3 className="text-xs font-semibold uppercase tracking-wide text-indigo-500">Live-Notizen</h3>
        <div className="max-h-56 space-y-2 overflow-y-auto rounded-lg border border-indigo-100 bg-white/80 p-3 text-sm dark:border-indigo-900/40 dark:bg-indigo-950/30">
          {notes.length === 0 ? (
            <p className="text-xs text-slate-500 dark:text-slate-400">Noch keine Notizen vorhanden.</p>
          ) : (
            notes.map((note) => (
              <div key={note.id} className="rounded-md border border-indigo-100 bg-indigo-50/70 p-2 dark:border-indigo-900/40 dark:bg-indigo-950/50">
                <div className="flex items-center justify-between text-[11px] text-indigo-600 dark:text-indigo-200">
                  <span className="font-semibold">{note.user_name}</span>
                  <span>{new Date(note.created_at).toLocaleTimeString()}</span>
                </div>
                <p className="mt-1 text-sm text-slate-700 dark:text-slate-100">{note.text}</p>
              </div>
            ))
          )}
        </div>
      </section>

      <form className="space-y-2" onSubmit={onSubmit}>
        <label className="text-xs font-semibold uppercase tracking-wide text-indigo-500" htmlFor="collab-note">
          Schnelle Notiz
        </label>
        <div className="flex gap-2">
          <textarea
            id="collab-note"
            value={noteDraft}
            onChange={(event) => setNoteDraft(event.target.value)}
            placeholder="Wichtige Erkenntnisse teilen ..."
            className="flex-1 resize-none rounded-md border border-indigo-200 bg-white/80 px-3 py-2 text-sm text-slate-800 shadow-sm outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 dark:border-indigo-900/50 dark:bg-indigo-950/40 dark:text-indigo-50"
            rows={3}
          />
          <Button type="submit" className="self-start bg-indigo-600 hover:bg-indigo-700">
            <MessageSquare className="mr-2 h-4 w-4" />
            Senden
          </Button>
        </div>
      </form>

      {error && (
        <div className="rounded-md border border-amber-300 bg-amber-100/70 px-3 py-2 text-xs text-amber-800 dark:border-amber-900/60 dark:bg-amber-900/40 dark:text-amber-200">
          {error}
        </div>
      )}
    </CardContent>
  </Card>
)
