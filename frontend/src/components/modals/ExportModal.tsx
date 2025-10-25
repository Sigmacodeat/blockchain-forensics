import { Fragment } from 'react'
import { Dialog, Transition } from '@headlessui/react'
import { X, Download, FileJson, FileSpreadsheet, Share2 } from 'lucide-react'
import type { TraceResult } from '@/lib/types'
import { exportTraceToCSV, exportTraceToJSON, exportNodesToCSV, exportTraceToGraphML } from '@/lib/export'

interface ExportModalProps {
  isOpen: boolean
  onClose: () => void
  trace: TraceResult
}

export default function ExportModal({ isOpen, onClose, trace }: ExportModalProps) {
  const exportOptions = [
    {
      title: 'Full Trace (JSON)',
      description: 'Vollständiger Trace mit allen Daten als JSON',
      icon: FileJson,
      action: () => exportTraceToJSON(trace),
    },
    {
      title: 'Transactions (CSV)',
      description: 'Alle Transaktionen mit Taint-Werten',
      icon: FileSpreadsheet,
      action: () => exportTraceToCSV(trace),
    },
    {
      title: 'Nodes/Addresses (CSV)',
      description: 'Alle Adressen mit Risk-Scores und Labels',
      icon: FileSpreadsheet,
      action: () => exportNodesToCSV(trace),
    },
    {
      title: 'Graph (GraphML)',
      description: 'Für Gephi, Cytoscape und andere Graph-Tools',
      icon: Share2,
      action: () => exportTraceToGraphML(trace),
    },
  ]

  const handleExport = (action: () => void) => {
    action()
    // Optional: Toast-Benachrichtigung
    setTimeout(onClose, 300)
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
                    <Download className="w-5 h-5 text-primary-600" />
                    Export Trace
                  </Dialog.Title>
                  <button
                    onClick={onClose}
                    className="text-gray-400 hover:text-gray-600 transition-colors"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>

                <p className="text-sm text-gray-600 mb-6">
                  Wähle ein Export-Format für Trace <span className="font-mono text-xs">{trace.trace_id}</span>
                </p>

                <div className="space-y-3">
                  {exportOptions.map((option) => (
                    <button
                      key={option.title}
                      onClick={() => handleExport(option.action)}
                      className="w-full flex items-start gap-3 p-4 rounded-lg border border-gray-200 hover:border-primary-500 hover:bg-primary-50 transition-all group"
                    >
                      <option.icon className="w-5 h-5 text-gray-600 group-hover:text-primary-600 mt-0.5" />
                      <div className="flex-1 text-left">
                        <p className="font-medium text-gray-900 group-hover:text-primary-900">
                          {option.title}
                        </p>
                        <p className="text-sm text-gray-600">{option.description}</p>
                      </div>
                    </button>
                  ))}
                </div>

                <div className="mt-6 flex justify-end gap-2">
                  <button onClick={onClose} className="btn-secondary">
                    Abbrechen
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
