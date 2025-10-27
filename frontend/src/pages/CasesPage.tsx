import { useState, useCallback, useMemo, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { motion, AnimatePresence } from 'framer-motion'
import { Plus, Search, Filter, Download, FileText, Shield, X, Calendar, User, TrendingUp, Clock, CheckCircle, AlertCircle, Folder } from 'lucide-react'
import { useCases, useCreateCase } from '@/hooks/useCases'
import { ToastProvider } from '@/components/ui/toast'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { CaseForm } from '@/components/case/CaseForm'
import { CaseCard } from '@/components/case/CaseCard'
import { BatchScreeningModal } from '@/components/BatchScreeningModal'
import type { Case } from '@/types/case'
import { useToastSuccess, useToastError } from '@/components/ui/toast'

// Modern DatePicker Component
const DatePicker = ({ date, onDateChange, placeholder }: { date?: Date; onDateChange?: (date: Date) => void; placeholder: string }) => {
  return (
    <Input
      type="date"
      value={date?.toISOString().split('T')[0] || ''}
      onChange={(e) => onDateChange?.(new Date(e.target.value))}
      placeholder={placeholder}
      className="bg-white/50 dark:bg-slate-800/50 backdrop-blur-sm border-slate-200 dark:border-slate-700 focus:border-primary-500 dark:focus:border-primary-600 transition-all"
    />
  )
}

// Stats Card Component
type ColorType = 'blue' | 'green' | 'purple' | 'orange'

interface StatsCardProps {
  icon: React.ComponentType<{ className?: string }>
  label: string
  value: number
  trend?: string
  color: ColorType
}

const StatsCard = ({ icon: Icon, label, value, trend, color }: StatsCardProps) => {
  const colorClasses: Record<ColorType, string> = {
    blue: 'from-blue-500 to-cyan-500',
    green: 'from-emerald-500 to-teal-500',
    purple: 'from-purple-500 to-pink-500',
    orange: 'from-orange-500 to-red-500'
  }
  const iconColorClasses: Record<ColorType, string> = {
    blue: 'text-blue-600 dark:text-blue-400',
    green: 'text-emerald-600 dark:text-emerald-400',
    purple: 'text-purple-600 dark:text-purple-400',
    orange: 'text-orange-600 dark:text-orange-400'
  }

  return (
    <motion.div
      whileHover={{ y: -4, scale: 1.02 }}
      transition={{ type: 'spring', stiffness: 300 }}
    >
      <Card className="relative overflow-hidden border-slate-200 dark:border-slate-700 bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm hover:shadow-xl transition-all duration-300">
        <div className={`absolute inset-0 bg-gradient-to-br ${colorClasses[color]} opacity-5`} />
        <CardContent className="p-6 relative">
          <div className="flex items-center justify-between mb-4">
            <div className={`p-3 rounded-xl bg-gradient-to-br ${colorClasses[color]} bg-opacity-10`}>
              <Icon className={`h-6 w-6 ${iconColorClasses[color]}`} />
            </div>
            {trend && (
              <Badge variant="secondary" className="flex items-center gap-1 bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400 border-0">
                <TrendingUp className="h-3 w-3" />
                {trend}
              </Badge>
            )}
          </div>
          <div className="space-y-1">
            <p className="text-2xl font-bold text-slate-900 dark:text-white">{value}</p>
            <p className="text-sm text-slate-600 dark:text-slate-400">{label}</p>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  )
}

export default function CasesPage() {
  const { t } = useTranslation()
  const { data: casesResponse, isLoading, error } = useCases()
  const createCase = useCreateCase()
  const showSuccess = useToastSuccess()
  const showError = useToastError()

  // State Management
  const [searchTerm, setSearchTerm] = useState('')
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [showFilters, setShowFilters] = useState(false)
  const [showBatchScreening, setShowBatchScreening] = useState(false)
  const [selectedStatus, setSelectedStatus] = useState<string>('all')
  const [selectedInvestigator, setSelectedInvestigator] = useState<string>('all')
  const [dateFrom, setDateFrom] = useState<Date | undefined>()
  const [dateTo, setDateTo] = useState<Date | undefined>()

  const cases: Case[] = (casesResponse?.cases || []) as Case[]

  // Calculate Statistics
  const stats = useMemo(() => {
    const total = cases.length
    const active = cases.filter(c => c.status === 'active').length
    const closed = cases.filter(c => c.status === 'closed').length
    const pending = cases.filter(c => c.status === 'pending').length
    
    return { total, active, closed, pending }
  }, [cases])

  // Debounced search handler
  const handleSearchChange = useCallback((value: string) => {
    setSearchTerm(value)
  }, [])

  // Filter cases
  const filteredCases = useMemo(() => {
    return cases.filter((case_: Case) => {
      const matchesSearch = !searchTerm ||
        case_.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        case_.case_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
        case_.lead_investigator.toLowerCase().includes(searchTerm.toLowerCase())

      const matchesStatus = selectedStatus === 'all' || case_.status === selectedStatus
      const matchesInvestigator = selectedInvestigator === 'all' || case_.lead_investigator === selectedInvestigator

      const caseDate = new Date(case_.created_at)
      const matchesDate = (!dateFrom || caseDate >= dateFrom) && (!dateTo || caseDate <= dateTo)

      return matchesSearch && matchesStatus && matchesInvestigator && matchesDate
    })
  }, [cases, searchTerm, selectedStatus, selectedInvestigator, dateFrom, dateTo])

  // Get unique investigators
  const investigators = useMemo(() => {
    return Array.from(new Set(cases.map((c: Case) => c.lead_investigator))).sort()
  }, [cases])

  const handleCreateCase = async (data: any) => {
    try {
      await createCase.mutateAsync(data)
      setShowCreateForm(false)
      showSuccess(t('cases.success.created', 'Case Created'), t('cases.success.created_message', 'Your new case has been created successfully.'))
    } catch (error) {
      showError(t('common.error', 'Error'), t('cases.error.create', 'Failed to create case. Please try again.'))
    }
  }

  // Keyboard shortcuts
  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    if (e.key === 'Escape') {
      setShowCreateForm(false)
      setShowFilters(false)
    }
    if (e.ctrlKey || e.metaKey) {
      if (e.key === 'k') {
        e.preventDefault()
        document.querySelector<HTMLInputElement>('[data-search-input]')?.focus()
      }
    }
  }, [])

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [handleKeyDown])

  // Loading State
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-purple-50 dark:from-slate-900 dark:via-slate-900 dark:to-slate-800" role="main" aria-live="polite">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* Ensure heading exists for accessibility/tests */}
          <h1 className="sr-only">{t('cases.title', 'Cases')}</h1>
          <div className="flex items-center justify-center min-h-[400px]">
            <div className="text-center">
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                className="w-16 h-16 border-4 border-primary-500 border-t-transparent rounded-full mx-auto mb-4"
              />
              <p className="text-slate-600 dark:text-slate-400 font-medium">
                {t('cases.loading', 'Lade Fälle...')}
              </p>
            </div>
          </div>
        </div>
      </div>
    )
  }

  // Error State
  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-purple-50 dark:from-slate-900 dark:via-slate-900 dark:to-slate-800" role="main">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center"
          >
            {/* Ensure heading exists for accessibility/tests */}
            <h1 className="sr-only">{t('cases.title', 'Cases')}</h1>
            <AlertCircle className="h-16 w-16 text-red-500 mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">
              {t('cases.error.load', 'Failed to load cases')}
            </h2>
            <p className="text-slate-600 dark:text-slate-400 mb-6">
              {t('cases.error.load_message', 'Beim Laden der Fälle ist ein Problem aufgetreten. Bitte versuche es erneut.')}
            </p>
            <Button onClick={() => window.location.reload()} size="lg">
              {t('common.retry', 'Retry')}
            </Button>
          </motion.div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-purple-50 dark:from-slate-900 dark:via-slate-900 dark:to-slate-800" role="main">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        
        {/* Header Section */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
            <div className="space-y-2">
              <h1 className="text-4xl font-bold bg-gradient-to-r from-slate-900 via-primary-700 to-purple-700 dark:from-white dark:via-primary-400 dark:to-purple-400 bg-clip-text text-transparent">
                {t('cases.title', 'Cases')}
              </h1>
              <p className="text-lg text-slate-600 dark:text-slate-400">
                {t('cases.subtitle', 'Verwalte Ermittlungsfälle und Beweisketten')}
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <motion.div tabIndex={-1} whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                <Button
                  onClick={() => setShowCreateForm(true)}
                  size="lg"
                  className="bg-gradient-to-r from-primary-600 to-purple-600 hover:from-primary-700 hover:to-purple-700 text-white shadow-lg shadow-primary-500/30 dark:shadow-primary-500/20"
                >
                  <Plus className="h-5 w-5 mr-2" />
                  {t('cases.new_case', 'New Case')}
                </Button>
              </motion.div>
              
              <motion.div tabIndex={-1} whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                <Button
                  variant="outline"
                  onClick={() => setShowBatchScreening(true)}
                  size="lg"
                  className="border-2 border-emerald-500 text-emerald-700 dark:text-emerald-400 hover:bg-emerald-50 dark:hover:bg-emerald-900/20"
                >
                  <Shield className="h-5 w-5 mr-2" />
                  {t('cases.batch_screen', 'Batch Screen')}
                </Button>
              </motion.div>
            </div>
          </div>
        </motion.div>

        {/* Statistics Cards */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8"
        >
          <StatsCard
            icon={Folder}
            label={t('cases.stats.total', 'Gesamtfälle')}
            value={stats.total}
            color="blue"
          />
          <StatsCard
            icon={Clock}
            label={t('cases.stats.active', 'Active')}
            value={stats.active}
            trend="+12%"
            color="green"
          />
          <StatsCard
            icon={CheckCircle}
            label={t('cases.stats.closed', 'Closed')}
            value={stats.closed}
            color="purple"
          />
          <StatsCard
            icon={AlertCircle}
            label={t('cases.stats.pending', 'Pending')}
            value={stats.pending}
            color="orange"
          />
        </motion.div>

        {/* Search and Filters */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="mb-6"
        >
          <Card className="border-slate-200 dark:border-slate-700 bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm shadow-lg">
            <CardContent className="p-6">
              <div className="flex flex-col lg:flex-row items-start lg:items-center gap-4">
                <div className="relative flex-1 w-full">
                  <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 h-5 w-5 text-slate-400 dark:text-slate-500" />
                  <Input
                    data-search-input
                    aria-label={t('cases.search_aria', 'Search cases')}
                    placeholder={t('cases.search_placeholder', 'Search cases by title, ID, or investigator...')}
                    value={searchTerm}
                    onChange={(e) => handleSearchChange(e.target.value)}
                    className="pl-12 pr-20 py-6 text-base bg-white/50 dark:bg-slate-900/50 backdrop-blur-sm border-slate-200 dark:border-slate-700 focus:border-primary-500 dark:focus:border-primary-600 rounded-xl transition-all"
                  />
                  <kbd className="absolute right-4 top-1/2 transform -translate-y-1/2 px-3 py-1 text-xs font-semibold text-slate-500 dark:text-slate-400 bg-slate-100 dark:bg-slate-800 border border-slate-300 dark:border-slate-600 rounded-lg">
                    ⌘K
                  </kbd>
                </div>
                
                <Button
                  variant="outline"
                  size="lg"
                  onClick={() => setShowFilters(!showFilters)}
                  className="border-2 border-slate-300 dark:border-slate-600 hover:bg-slate-100 dark:hover:bg-slate-700"
                >
                  <Filter className="h-5 w-5 mr-2" />
                  {t('cases.filters', 'Filters')}
                  {(selectedStatus !== 'all' || selectedInvestigator !== 'all' || dateFrom || dateTo) && (
                    <Badge className="ml-2 bg-primary-500 text-white">
                      {[selectedStatus !== 'all', selectedInvestigator !== 'all', dateFrom, dateTo].filter(Boolean).length}
                    </Badge>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Filters Panel */}
        <AnimatePresence>
          {showFilters && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.3 }}
              className="mb-6"
            >
              <Card className="border-slate-200 dark:border-slate-700 bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm shadow-lg">
                <CardHeader className="pb-4 border-b border-slate-200 dark:border-slate-700">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-xl font-bold text-slate-900 dark:text-white">
                      {t('cases.filters_title', 'Advanced Filters')}
                    </CardTitle>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setShowFilters(false)}
                      className="hover:bg-slate-100 dark:hover:bg-slate-700"
                    >
                      <X className="h-5 w-5" />
                    </Button>
                  </div>
                </CardHeader>
                <CardContent className="pt-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                    <div>
                      <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-3">
                        {t('cases.filter.status', 'Status')}
                      </label>
                      <Select value={selectedStatus} onValueChange={setSelectedStatus}>
                        <SelectTrigger data-testid="status-select-trigger" className="bg-white/50 dark:bg-slate-900/50 backdrop-blur-sm border-slate-200 dark:border-slate-700">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="all">{t('cases.filter.all_statuses', 'All Statuses')}</SelectItem>
                          <SelectItem value="active">{t('cases.status.active', 'Active')}</SelectItem>
                          <SelectItem value="closed">{t('cases.status.closed', 'Closed')}</SelectItem>
                          <SelectItem value="pending">{t('cases.status.pending', 'Pending')}</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    <div>
                      <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-3">
                        {t('cases.filter.investigator', 'Investigator')}
                      </label>
                      <Select value={selectedInvestigator} onValueChange={setSelectedInvestigator}>
                        <SelectTrigger className="bg-white/50 dark:bg-slate-900/50 backdrop-blur-sm border-slate-200 dark:border-slate-700">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="all">{t('cases.filter.all_investigators', 'All Investigators')}</SelectItem>
                          {investigators.map((inv) => (
                            <SelectItem key={inv} value={inv}>{inv}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>

                    <div>
                      <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-3">
                        {t('cases.filter.from_date', 'From Date')}
                      </label>
                      <DatePicker
                        date={dateFrom}
                        onDateChange={setDateFrom}
                        placeholder={t('cases.filter.select_start_date', 'Select start date')}
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-3">
                        {t('cases.filter.to_date', 'To Date')}
                      </label>
                      <DatePicker
                        date={dateTo}
                        onDateChange={setDateTo}
                        placeholder={t('cases.filter.select_end_date', 'Select end date')}
                      />
                    </div>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Cases Grid or Empty State */}
        {filteredCases.length === 0 ? (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="text-center py-20"
          >
            <Card className="border-slate-200 dark:border-slate-700 bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm shadow-xl max-w-2xl mx-auto">
              <CardContent className="p-12">
                <FileText className="h-20 w-20 text-slate-300 dark:text-slate-600 mx-auto mb-6" />
                <h3 aria-hidden="true" className="text-2xl font-bold text-slate-900 dark:text-white mb-3">
                  {t('cases.empty.title', 'Keine Fälle gefunden')}
                </h3>
                <p className="text-slate-600 dark:text-slate-400 mb-8 text-lg">
                  {searchTerm || selectedStatus !== 'all' || selectedInvestigator !== 'all' || dateFrom || dateTo
                    ? t('cases.empty.adjust_filters', 'Try adjusting your filters or search terms')
                    : t('cases.empty.create_first', 'Create your first case to get started')}
                </p>
                {(!searchTerm && selectedStatus === 'all' && selectedInvestigator === 'all' && !dateFrom && !dateTo) && (
                  <motion.div tabIndex={-1} whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                    <Button onClick={() => setShowCreateForm(true)} size="lg" className="bg-gradient-to-r from-primary-600 to-purple-600 hover:from-primary-700 hover:to-purple-700 text-white shadow-lg">
                      <Plus className="h-5 w-5 mr-2" />
                      {t('cases.create_case', 'Create Case')}
                    </Button>
                  </motion.div>
                )}
              </CardContent>
            </Card>
          </motion.div>
        ) : (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex items-center justify-between mb-6"
            >
              <p className="text-sm font-medium text-slate-600 dark:text-slate-400">
                {t('cases.showing', 'Anzeigen')} <span className="font-bold text-slate-900 dark:text-white">{filteredCases.length}</span> {t('cases.of', 'von')} <span className="font-bold text-slate-900 dark:text-white">{cases.length}</span> {t('cases.cases', 'Fälle')}
              </p>
            </motion.div>
            
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.3 }}
              className="grid gap-6 md:grid-cols-2 lg:grid-cols-3"
            >
              <AnimatePresence mode="popLayout">
                {filteredCases.map((case_: Case, index) => (
                  <motion.div
                    key={case_.case_id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, scale: 0.9 }}
                    transition={{ delay: index * 0.05 }}
                    layout
                  >
                    <CaseCard case_={case_} />
                  </motion.div>
                ))}
              </AnimatePresence>
            </motion.div>
          </>
        )}

        {/* Create Case Modal */}
        <AnimatePresence>
          {showCreateForm && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 z-50"
              onClick={() => setShowCreateForm(false)}
            >
              <motion.div
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.9, opacity: 0 }}
                transition={{ type: 'spring', damping: 20 }}
                className="bg-white dark:bg-slate-800 rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto"
                onClick={(e) => e.stopPropagation()}
              >
                <div className="sticky top-0 bg-gradient-to-r from-primary-600 to-purple-600 p-6 rounded-t-2xl">
                  <div className="flex items-center justify-between">
                    <h2 className="text-2xl font-bold text-white">
                      {t('cases.create_new', 'Create New Case')}
                    </h2>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setShowCreateForm(false)}
                      className="text-white hover:bg-white/20"
                    >
                      <X className="h-6 w-6" />
                    </Button>
                  </div>
                </div>
                <div className="p-6">
                  <CaseForm
                    onSubmit={handleCreateCase}
                    onCancel={() => setShowCreateForm(false)}
                    isLoading={createCase.isPending}
                  />
                </div>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Batch Screening Modal */}
        <BatchScreeningModal
          cases={cases}
          isOpen={showBatchScreening}
          onClose={() => setShowBatchScreening(false)}
        />
      </div>
    </div>
  )
}
