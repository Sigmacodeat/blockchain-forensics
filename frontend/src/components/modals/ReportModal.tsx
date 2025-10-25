import { Fragment, useState } from 'react'
import { Dialog, Transition } from '@headlessui/react'
import { X, FileText, Mail, Loader2 } from 'lucide-react'
import api from '@/lib/api'
import type { TraceResult } from '@/lib/types'

interface ReportModalProps {
  isOpen: boolean
  onClose: () => void
  trace: TraceResult
}

export default function ReportModal({ isOpen, onClose, trace }: ReportModalProps) {
  const [isGenerating, setIsGenerating] = useState(false)
  const [email, setEmail] = useState('')
  const [includeGraphs, setIncludeGraphs] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const handleGenerateReport = async () => {
    setIsGenerating(true)
    setError(null)

    try {
      const response = await api.post(
        `/api/v1/reports/trace/${trace.trace_id}`,
        {
          format: 'pdf',
          include_graphs: includeGraphs,
          recipient_email: email || undefined,
        },
        { responseType: 'blob' }
      )

      // Download PDF
      const blob = new Blob([response.data], { type: 'application/pdf' })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `trace_report_${trace.trace_id}.pdf`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)

      // Success feedback
      setTimeout(() => {
        onClose()
        setEmail('')
        setIncludeGraphs(true)
      }, 500)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Fehler beim Generieren des Reports')
    } finally {
      setIsGenerating(false)
    }
  }

  return (
    <Transition appear show={isOpen} as={Fragment}>
      <Dialog as="div" className="relative z-50" onClose={onClose}>
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-black bg-opacity-25" />
        </Transition.Child>

        <div className="fixed inset-0 overflow-y-auto">
          <div className="flex min-h-full items-center justify-center p-4 text-center">
            <Transition.Child
              as={Fragment}
              enter="ease-out duration-300"
              enterFrom="opacity-0 scale-95"
              enterTo="opacity-100 scale-100"
              leave="ease-in duration-200"
              leaveFrom="opacity-100 scale-100"
              leaveTo="opacity-0 scale-95"
            >
              <Dialog.Panel className="w-full max-w-md transform overflow-hidden rounded-2xl bg-white p-6 text-left align-middle shadow-xl transition-all">
                <div className="flex items-center justify-between mb-4">
                  <Dialog.Title
                    as="h3"
                    className="text-lg font-semibold leading-6 text-gray-900 flex items-center gap-2"
                  >
                    <FileText className="w-5 h-5 text-primary-600" />
                    Generate Report
                  </Dialog.Title>
                  <button
                    onClick={onClose}
                    className="text-gray-400 hover:text-gray-600 transition-colors"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>

                <p className="text-sm text-gray-600 mb-6">
                  Generiere einen gerichtsverwertbaren PDF-Report für Trace{' '}
                  <span className="font-mono text-xs">{trace.trace_id}</span>
                </p>

                {error && (
                  <div className="mb-4 p-3 bg-danger-50 border border-danger-200 rounded-lg text-sm text-danger-800">
                    {error}
                  </div>
                )}

                <div className="space-y-4">
                  {/* Include Graphs */}
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={includeGraphs}
                      onChange={(e) => setIncludeGraphs(e.target.checked)}
                      className="w-4 h-4 text-primary-600 rounded focus:ring-primary-500"
                    />
                    <span className="text-sm text-gray-700">Graph-Visualisierungen einbinden</span>
                  </label>

                  {/* Email (optional) */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1 flex items-center gap-2">
                      <Mail className="w-4 h-4" />
                      E-Mail-Versand (optional)
                    </label>
                    <input
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="report@example.com"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      Falls angegeben, wird der Report auch per E-Mail versendet
                    </p>
                  </div>

                  {/* Report Preview Info */}
                  <div className="bg-gray-50 p-3 rounded-lg text-sm space-y-1">
                    <p className="font-medium text-gray-700">Report enthält:</p>
                    <ul className="text-gray-600 space-y-0.5 ml-4 list-disc">
                      <li>Executive Summary</li>
                      <li>Trace-Metadaten & Statistiken</li>
                      <li>High-Risk & Sanctioned Addresses</li>
                      <li>Transaktionsfluss-Analyse</li>
                      {includeGraphs && <li>Graph-Visualisierungen</li>}
                      <li>Digitale Signatur & Timestamps</li>
                    </ul>
                  </div>
                </div>

                <div className="mt-6 flex justify-end gap-2">
                  <button onClick={onClose} className="btn-secondary" disabled={isGenerating}>
                    Abbrechen
                  </button>
                  <button
                    onClick={handleGenerateReport}
                    disabled={isGenerating}
                    className="btn-primary flex items-center gap-2"
                  >
                    {isGenerating ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        Generiere...
                      </>
                    ) : (
                      <>
                        <FileText className="w-4 h-4" />
                        Generieren
                      </>
                    )}
                  </button>
                </div>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition>
  )
}
