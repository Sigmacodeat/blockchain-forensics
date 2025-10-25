import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { motion } from 'framer-motion'
import { Calendar, User, FileText, Download, Shield, Eye, ExternalLink, CheckCircle2, Clock, AlertCircle } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Case } from '@/types/case'
import { useCaseExport, useCaseExportCsv, useCaseChecksum } from '@/hooks/useCases'
import { SanctionsBadge } from '@/components/SanctionsBadge'

interface CaseCardProps {
  case_: Case
  onExport?: (caseId: string) => void
}

export function CaseCard({ case_ }: CaseCardProps) {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const { lang } = useParams<{ lang: string }>()
  const [showExportMenu, setShowExportMenu] = useState(false)

  const { data: exportData } = useCaseExport(case_.case_id)
  const { data: csvData } = useCaseExportCsv(case_.case_id)
  const { data: checksumData } = useCaseChecksum(case_.case_id)

  const handleViewDetails = () => {
    navigate(`/${lang || 'en'}/cases/${case_.case_id}`)
  }

  const handleExport = (format: 'json' | 'csv', e: React.MouseEvent) => {
    e.stopPropagation()
    
    if (format === 'json' && exportData) {
      const blob = new Blob([JSON.stringify(exportData.export, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${case_.case_id}_export.json`
      a.click()
      URL.revokeObjectURL(url)
    } else if (format === 'csv' && csvData) {
      const entitiesCsv = csvData.entities_csv
      const evidenceCsv = csvData.evidence_csv

      if (entitiesCsv) {
        const blob = new Blob([entitiesCsv], { type: 'text/csv' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `${case_.case_id}_entities.csv`
        a.click()
        URL.revokeObjectURL(url)
      }

      if (evidenceCsv) {
        const blob = new Blob([evidenceCsv], { type: 'text/csv' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `${case_.case_id}_evidence.csv`
        a.click()
        URL.revokeObjectURL(url)
      }
    }
    setShowExportMenu(false)
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString(lang || 'en', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    })
  }

  const getStatusConfig = (status: string) => {
    const configs = {
      active: {
        icon: Clock,
        color: 'from-emerald-500 to-teal-500',
        badgeClass: 'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400 border-emerald-300 dark:border-emerald-700',
        label: t('cases.status.active', 'Active')
      },
      closed: {
        icon: CheckCircle2,
        color: 'from-purple-500 to-pink-500',
        badgeClass: 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-400 border-purple-300 dark:border-purple-700',
        label: t('cases.status.closed', 'Closed')
      },
      pending: {
        icon: AlertCircle,
        color: 'from-orange-500 to-red-500',
        badgeClass: 'bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-400 border-orange-300 dark:border-orange-700',
        label: t('cases.status.pending', 'Pending')
      }
    }
    return configs[status as keyof typeof configs] || configs.pending
  }

  const statusConfig = getStatusConfig(case_.status)
  const StatusIcon = statusConfig.icon

  return (
    <motion.div
      whileHover={{ y: -4, scale: 1.02 }}
      transition={{ type: 'spring', stiffness: 300, damping: 20 }}
    >
      <Card 
        className="group relative overflow-hidden border-slate-200 dark:border-slate-700 bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm hover:shadow-2xl hover:border-primary-400 dark:hover:border-primary-600 transition-all duration-300 cursor-pointer h-full"
        onClick={handleViewDetails}
      >
        {/* Gradient Overlay */}
        <div className={`absolute inset-0 bg-gradient-to-br ${statusConfig.color} opacity-0 group-hover:opacity-5 transition-opacity duration-300`} />
        
        {/* Status Indicator Line */}
        <div className={`absolute top-0 left-0 right-0 h-1 bg-gradient-to-r ${statusConfig.color}`} />

        <CardHeader className="pb-4 relative">
          <div className="flex items-start justify-between gap-3">
            <div className="flex-1 min-w-0">
              <CardTitle className="text-lg font-bold text-slate-900 dark:text-white truncate mb-1 group-hover:text-primary-600 dark:group-hover:text-primary-400 transition-colors">
                {case_.title}
              </CardTitle>
              <CardDescription className="text-sm font-mono text-slate-500 dark:text-slate-400 flex items-center gap-2">
                <FileText className="h-3.5 w-3.5 flex-shrink-0" />
                {case_.case_id}
              </CardDescription>
            </div>
            <Badge className={`${statusConfig.badgeClass} border flex items-center gap-1.5 px-3 py-1 font-semibold flex-shrink-0`}>
              <StatusIcon className="h-3.5 w-3.5" />
              {statusConfig.label}
            </Badge>
          </div>
        </CardHeader>

        <CardContent className="pt-0 space-y-4 relative">
          {/* Description */}
          <p className="text-sm text-slate-600 dark:text-slate-400 line-clamp-2 leading-relaxed">
            {case_.description || t('cases.no_description', 'No description provided')}
          </p>

          {/* Metadata */}
          <div className="grid grid-cols-2 gap-3">
            <div className="flex items-center gap-2 p-2.5 bg-slate-50 dark:bg-slate-900/50 rounded-lg">
              <div className="p-1.5 bg-blue-100 dark:bg-blue-900/30 rounded-md">
                <User className="h-3.5 w-3.5 text-blue-600 dark:text-blue-400" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs text-slate-500 dark:text-slate-400 font-medium">
                  {t('cases.investigator', 'Investigator')}
                </p>
                <p className="text-sm text-slate-900 dark:text-white font-semibold truncate">
                  {case_.lead_investigator}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2 p-2.5 bg-slate-50 dark:bg-slate-900/50 rounded-lg">
              <div className="p-1.5 bg-purple-100 dark:bg-purple-900/30 rounded-md">
                <Calendar className="h-3.5 w-3.5 text-purple-600 dark:text-purple-400" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs text-slate-500 dark:text-slate-400 font-medium">
                  {t('cases.created', 'Created')}
                </p>
                <p className="text-sm text-slate-900 dark:text-white font-semibold truncate">
                  {formatDate(case_.created_at)}
                </p>
              </div>
            </div>
          </div>

          {/* Stats */}
          {exportData?.export && (
            <div className="flex items-center justify-between p-3 bg-gradient-to-r from-primary-50 to-purple-50 dark:from-primary-900/20 dark:to-purple-900/20 rounded-lg border border-primary-200 dark:border-primary-800">
              <div className="text-center flex-1">
                <p className="text-xl font-bold text-primary-700 dark:text-primary-400">
                  {exportData.export.entities?.length || 0}
                </p>
                <p className="text-xs text-slate-600 dark:text-slate-400 font-medium">
                  {t('cases.entities', 'Entities')}
                </p>
              </div>
              <div className="w-px h-8 bg-primary-300 dark:bg-primary-700" />
              <div className="text-center flex-1">
                <p className="text-xl font-bold text-purple-700 dark:text-purple-400">
                  {exportData.export.evidence?.length || 0}
                </p>
                <p className="text-xs text-slate-600 dark:text-slate-400 font-medium">
                  {t('cases.evidence', 'Evidence')}
                </p>
              </div>
            </div>
          )}

          {/* Sanctions Check */}
          <div className="pt-2 border-t border-slate-200 dark:border-slate-700">
            <SanctionsBadge address="0x1234567890abcdef1234567890abcdef12345678" />
          </div>

          {/* Actions */}
          <div className="flex items-center gap-2 pt-2">
            <Button
              variant="outline"
              size="sm"
              onClick={(e) => { e.stopPropagation(); handleViewDetails() }}
              className="flex-1 bg-white dark:bg-slate-900 border-2 border-slate-300 dark:border-slate-600 hover:bg-primary-50 dark:hover:bg-primary-900/20 hover:border-primary-500 dark:hover:border-primary-600 group/btn transition-all"
            >
              <Eye className="h-4 w-4 mr-2 text-slate-600 dark:text-slate-400 group-hover/btn:text-primary-600 dark:group-hover/btn:text-primary-400" />
              <span className="font-semibold">{t('cases.view', 'View')}</span>
              <ExternalLink className="h-3 w-3 ml-1 opacity-0 group-hover/btn:opacity-100 transition-opacity" />
            </Button>

            <div className="relative">
              <Button
                variant="outline"
                size="sm"
                onClick={(e) => { e.stopPropagation(); setShowExportMenu(!showExportMenu) }}
                className="bg-white dark:bg-slate-900 border-2 border-emerald-300 dark:border-emerald-700 hover:bg-emerald-50 dark:hover:bg-emerald-900/20 hover:border-emerald-500 dark:hover:border-emerald-500 transition-all"
              >
                <Download className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
              </Button>

              {showExportMenu && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="absolute right-0 mt-2 w-40 bg-white dark:bg-slate-800 border-2 border-slate-200 dark:border-slate-700 rounded-xl shadow-2xl z-10 overflow-hidden"
                  onClick={(e) => e.stopPropagation()}
                >
                  <button
                    className="w-full text-left px-4 py-3 text-sm font-medium text-slate-700 dark:text-slate-300 hover:bg-primary-50 dark:hover:bg-primary-900/20 transition-colors flex items-center gap-2"
                    onClick={(e) => handleExport('json', e)}
                  >
                    <FileText className="h-4 w-4 text-primary-600 dark:text-primary-400" />
                    JSON
                  </button>
                  <button
                    className="w-full text-left px-4 py-3 text-sm font-medium text-slate-700 dark:text-slate-300 hover:bg-emerald-50 dark:hover:bg-emerald-900/20 transition-colors flex items-center gap-2 border-t border-slate-200 dark:border-slate-700"
                    onClick={(e) => handleExport('csv', e)}
                  >
                    <FileText className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
                    CSV
                  </button>
                </motion.div>
              )}
            </div>

            {checksumData?.checksum_sha256 && (
              <div className="flex items-center gap-1.5 px-2.5 py-1.5 bg-amber-50 dark:bg-amber-900/20 border border-amber-300 dark:border-amber-700 rounded-lg">
                <Shield className="h-3.5 w-3.5 text-amber-600 dark:text-amber-400" />
                <span className="font-mono text-xs text-amber-700 dark:text-amber-400 font-semibold">
                  {checksumData.checksum_sha256.slice(0, 6)}...
                </span>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </motion.div>
  )
}
