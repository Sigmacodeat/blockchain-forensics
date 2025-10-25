/**
 * ForensicResultDisplay - Zeigt Forensik-Ergebnisse mit Download-Buttons
 * 
 * Ähnlich zu CryptoPaymentDisplay.tsx, aber für Trace/Risk/Case-Results
 */

import React, { useState } from 'react';
import { DownloadButton } from './DownloadButton';
import { Download, ExternalLink, FolderPlus, FileText, CheckCircle } from 'lucide-react'
import { motion } from 'framer-motion'

interface ForensicResultProps {
  type: 'trace' | 'risk' | 'case' | 'report'
  resultId: string
  summary?: Record<string, any>
  downloadUrl?: string
  openLink?: string
  format?: string
}

export default function ForensicResultDisplay({ 
  type, 
  resultId, 
  summary, 
  downloadUrl, 
  openLink,
  format 
}: ForensicResultProps) {
  const [downloading, setDownloading] = useState(false)
  const [downloadSuccess, setDownloadSuccess] = useState(false)

  const handleDownload = async (downloadFormat: string) => {
    setDownloading(true)
    setDownloadSuccess(false)
    
    try {
      const url = downloadUrl?.replace('{format}', downloadFormat) || 
                  `/api/v1/reports/${type}/${resultId}/download/${downloadFormat}`
      
      const response = await fetch(url)
      if (!response.ok) throw new Error('Download failed')
      
      const blob = await response.blob()
      const link = document.createElement('a')
      link.href = window.URL.createObjectURL(blob)
      link.download = `forensic_${type}_${resultId}.${downloadFormat}`
      link.click()
      
      setDownloadSuccess(true)
      setTimeout(() => setDownloadSuccess(false), 3000)
    } catch (error) {
      console.error('Download failed:', error)
      alert('Download fehlgeschlagen. Bitte versuche es erneut.')
    } finally {
      setDownloading(false)
    }
  }

  const handleOpen = () => {
    if (openLink) {
      window.location.href = openLink
    }
  }

  // Icon mapping
  const icons = {
    trace: '🔍',
    risk: '⚠️',
    case: '📁',
    report: '📄'
  }

  // Title mapping
  const titles = {
    trace: 'Trace Results',
    risk: 'Risk Analysis',
    case: 'Investigation Case',
    report: 'Forensic Report'
  }

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95, y: 10 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      transition={{ duration: 0.3, type: 'spring' }}
      className="my-4 p-4 bg-gradient-to-br from-primary-50 via-white to-primary-50 dark:from-primary-900/20 dark:via-slate-800 dark:to-primary-900/20 rounded-xl border-2 border-primary-200 dark:border-primary-700 shadow-xl"
    >
      {/* Header */}
      <div className="flex items-center gap-3 mb-4">
        <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary-600 to-primary-700 flex items-center justify-center shadow-lg">
          <span className="text-2xl">{icons[type]}</span>
        </div>
        <div className="flex-1">
          <h4 className="font-bold text-gray-900 dark:text-white text-lg">
            {titles[type]}
          </h4>
          <p className="text-xs text-gray-600 dark:text-gray-400 font-mono">
            ID: {resultId}
          </p>
        </div>
        {downloadSuccess && (
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            className="flex items-center gap-2 text-green-600 dark:text-green-400"
          >
            <CheckCircle className="w-5 h-5" />
            <span className="text-sm font-medium">Downloaded!</span>
          </motion.div>
        )}
      </div>

      {/* Summary */}
      {summary && Object.keys(summary).length > 0 && (
        <div className="mb-4 p-3 bg-white/70 dark:bg-slate-800/70 rounded-lg backdrop-blur-sm border border-gray-200 dark:border-gray-700">
          <div className="grid grid-cols-2 gap-3 text-sm">
            {Object.entries(summary).map(([key, value]) => (
              <div key={key} className="flex justify-between">
                <span className="text-gray-600 dark:text-gray-400 capitalize">
                  {key.replace(/_/g, ' ')}:
                </span>
                <span className="font-semibold text-gray-900 dark:text-white">
                  {typeof value === 'number' ? value.toLocaleString() : String(value)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="flex flex-wrap gap-2">
        {/* Download Buttons */}
        {downloadUrl && (
          <>
            <motion.button
              whileHover={{ scale: 1.03, y: -2 }}
              whileTap={{ scale: 0.97 }}
              onClick={() => handleDownload('pdf')}
              disabled={downloading}
              className="flex items-center gap-2 px-4 py-2.5 bg-gradient-to-r from-red-500 to-red-600 text-white rounded-lg hover:from-red-600 hover:to-red-700 transition-all shadow-md hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed font-medium"
            >
              <Download className="w-4 h-4" />
              <span>PDF</span>
            </motion.button>

            <motion.button
              whileHover={{ scale: 1.03, y: -2 }}
              whileTap={{ scale: 0.97 }}
              onClick={() => handleDownload('csv')}
              disabled={downloading}
              className="flex items-center gap-2 px-4 py-2.5 bg-gradient-to-r from-green-500 to-green-600 text-white rounded-lg hover:from-green-600 hover:to-green-700 transition-all shadow-md hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed font-medium"
            >
              <Download className="w-4 h-4" />
              <span>CSV</span>
            </motion.button>

            <motion.button
              whileHover={{ scale: 1.03, y: -2 }}
              whileTap={{ scale: 0.97 }}
              onClick={() => handleDownload('json')}
              disabled={downloading}
              className="flex items-center gap-2 px-4 py-2.5 bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-lg hover:from-blue-600 hover:to-blue-700 transition-all shadow-md hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed font-medium"
            >
              <Download className="w-4 h-4" />
              <span>JSON</span>
            </motion.button>
          </>
        )}

        {/* Open Link */}
        {openLink && (
          <motion.button
            whileHover={{ scale: 1.03, y: -2 }}
            whileTap={{ scale: 0.97 }}
            onClick={handleOpen}
            className="flex items-center gap-2 px-4 py-2.5 bg-gradient-to-r from-primary-500 to-primary-600 text-white rounded-lg hover:from-primary-600 hover:to-primary-700 transition-all shadow-md hover:shadow-lg font-medium"
          >
            <ExternalLink className="w-4 h-4" />
            <span>Open {type === 'case' ? 'Case' : 'Details'}</span>
          </motion.button>
        )}
      </div>

      {/* Loading State */}
      {downloading && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="mt-3 flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400"
        >
          <div className="w-4 h-4 border-2 border-primary-600 border-t-transparent rounded-full animate-spin"></div>
          <span>Downloading...</span>
        </motion.div>
      )}

      {/* Format Badge */}
      {format && (
        <div className="mt-3 inline-flex items-center px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded text-xs font-medium text-gray-700 dark:text-gray-300">
          Format: {format.toUpperCase()}
        </div>
      )}
    </motion.div>
  )
}
