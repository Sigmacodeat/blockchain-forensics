import { useQuery, useMutation } from '@tanstack/react-query'
import { Database, Settings, Upload, Activity, Users as UsersIcon } from 'lucide-react'
import api from '@/lib/api'
import LoadingSpinner from '@/components/ui/LoadingSpinner'
import ErrorMessage from '@/components/ui/error-message'
import UserManagement from '@/components/admin/UserManagement'
import { useState } from 'react'
import { useTranslation } from 'react-i18next'

type TabType = 'overview' | 'users' | 'ingestion' | 'config'

export default function AdminPage() {
  const { t } = useTranslation()
  const [activeTab, setActiveTab] = useState<TabType>('overview')
  const [ingestAddress, setIngestAddress] = useState('')
  const [blockNumber, setBlockNumber] = useState('')

  // Health Check
  const { data: health, isPending: healthLoading } = useQuery({
    queryKey: ['health'],
    queryFn: async () => {
      const response = await api.get('/api/v1/admin/health/db')
      return response.data
    },
    refetchInterval: 10000, // Refresh every 10s
  })

  // System Stats
  const { data: stats } = useQuery({
    queryKey: ['stats'],
    queryFn: async () => {
      const response = await api.get('/api/v1/admin/stats')
      return response.data
    },
  })

  // Config
  const { data: config } = useQuery({
    queryKey: ['config'],
    queryFn: async () => {
      const response = await api.get('/api/v1/admin/config')
      return response.data
    },
  })

  // Ingest Address Mutation
  const ingestMutation = useMutation({
    mutationFn: async (address: string) => {
      const response = await api.post('/api/v1/admin/ingest/address', {
        address,
        limit: 100,
      })
      return response.data
    },
  })

  // Ingest Block Mutation
  const blockMutation = useMutation({
    mutationFn: async (block: number) => {
      const response = await api.post('/api/v1/admin/ingest/block', {
        block_number: block,
      })
      return response.data
    },
  })

  const handleIngestAddress = (e: React.FormEvent) => {
    e.preventDefault()
    if (ingestAddress) {
      ingestMutation.mutate(ingestAddress)
      setIngestAddress('')
    }
  }

  const handleIngestBlock = (e: React.FormEvent) => {
    e.preventDefault()
    if (blockNumber) {
      blockMutation.mutate(parseInt(blockNumber))
      setBlockNumber('')
    }
  }

  const tabs = [
    { id: 'overview' as TabType, label: t('admin.tabs.overview', 'Overview'), icon: Database },
    { id: 'users' as TabType, label: t('admin.tabs.users', 'User Management'), icon: UsersIcon },
    { id: 'ingestion' as TabType, label: t('admin.tabs.ingestion', 'Data Ingestion'), icon: Upload },
    { id: 'config' as TabType, label: t('admin.tabs.config', 'Configuration'), icon: Settings },
  ]

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <Settings className="w-8 h-8 text-primary-600" />
          <h1 className="text-3xl font-bold text-gray-900">{t('admin.title', 'System Administration')}</h1>
        </div>
        <p className="text-gray-600">{t('admin.subtitle', 'Monitoring, Configuration & Data Management')}</p>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="-mb-px flex space-x-8">
          {tabs.map((tab) => {
            const Icon = tab.icon
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`
                  flex items-center gap-2 py-4 px-1 border-b-2 font-medium text-sm transition-colors
                  ${
                    activeTab === tab.id
                      ? 'border-primary-500 text-primary-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }
                `}
              >
                <Icon className="w-5 h-5" />
                {tab.label}
              </button>
            )
          })}
        </nav>
      </div>

      {/* User Management Tab */}
      {activeTab === 'users' && <UserManagement />}

      {/* Overview Tab */}
      {activeTab === 'overview' && (
        <>
          {/* Health Status */}
          <div className="card p-6 mb-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <Database className="w-5 h-5" />
          {t('admin.health.title', 'Database Health')}
        </h2>
        {healthLoading ? (
          <LoadingSpinner />
        ) : health ? (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {Object.entries(health.databases || {}).map(([db, status]) => (
              <div key={db} className="p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-700 capitalize">{db}</span>
                  <div
                    className={`w-3 h-3 rounded-full ${
                      status ? 'bg-green-500' : 'bg-red-500'
                    }`}
                  />
                </div>
                <p className="text-xs text-gray-600">
                  {status ? t('admin.health.connected', '✓ Connected') : t('admin.health.disconnected', '✗ Disconnected')}
                </p>
              </div>
            ))}
          </div>
        ) : (
          <ErrorMessage message={t('admin.health.error', 'Failed to load health status')} />
        )}
      </div>

      {/* System Stats */}
      {stats && (
        <div className="card p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">{t('admin.stats.title', 'System Statistics')}</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="p-4 bg-primary-50 rounded-lg">
              <p className="text-sm text-primary-600 mb-1">{t('admin.stats.total_transactions', 'Total Transactions')}</p>
              <p className="text-2xl font-bold text-primary-900">{stats.total_transactions || 0}</p>
            </div>
            <div className="p-4 bg-green-50 rounded-lg">
              <p className="text-sm text-green-600 mb-1">{t('admin.stats.total_addresses', 'Total Addresses')}</p>
              <p className="text-2xl font-bold text-green-900">{stats.total_addresses || 0}</p>
            </div>
            <div className="p-4 bg-purple-50 rounded-lg">
              <p className="text-sm text-purple-600 mb-1">{t('admin.stats.total_traces', 'Total Traces')}</p>
              <p className="text-2xl font-bold text-purple-900">{stats.total_traces || 0}</p>
            </div>
            <div className="p-4 bg-orange-50 rounded-lg">
              <p className="text-sm text-orange-600 mb-1">{t('admin.stats.db_size', 'DB Size')}</p>
              <p className="text-2xl font-bold text-orange-900">
                {stats.database_size_mb?.toFixed(1) || 0} MB
              </p>
            </div>
          </div>
        </div>
      )}
        </>
      )}

      {/* Data Ingestion Tab */}
      {activeTab === 'ingestion' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Ingest Address */}
        <div className="card p-6">
          <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Upload className="w-5 h-5" />
            {t('admin.ingestion.address.title', 'Ingest Address Data')}
          </h3>
          <form onSubmit={handleIngestAddress} className="space-y-4">
            <div>
              <input
                type="text"
                className="input"
                placeholder={t('admin.ingestion.address.placeholder', '0x...')}
                value={ingestAddress}
                onChange={(e) => setIngestAddress(e.target.value)}
              />
              <p className="mt-1 text-xs text-gray-500">
                {t('admin.ingestion.address.help', 'Fetches transactions from Ethereum RPC')}
              </p>
            </div>
            <button
              type="submit"
              disabled={ingestMutation.isPending}
              className="btn-primary w-full disabled:opacity-50"
            >
              {ingestMutation.isPending ? t('admin.ingestion.address.ingesting', 'Ingesting...') : t('admin.ingestion.address.start', 'Start Ingestion')}
            </button>
            {ingestMutation.isSuccess && (
              <p className="text-sm text-green-600">{t('admin.ingestion.address.success', '✓ Ingestion started in background')}</p>
            )}
            {ingestMutation.isError && (
              <p className="text-sm text-red-600">
                {t('admin.error', 'Error')}: {(ingestMutation.error as any)?.response?.data?.detail}
              </p>
            )}
          </form>
        </div>

        {/* Ingest Block */}
        <div className="card p-6">
          <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Activity className="w-5 h-5" />
            {t('admin.ingestion.block.title', 'Ingest Block Data')}
          </h3>
          <form onSubmit={handleIngestBlock} className="space-y-4">
            <div>
              <input
                type="number"
                className="input"
                placeholder={t('admin.ingestion.block.placeholder', 'Block number')}
                value={blockNumber}
                onChange={(e) => setBlockNumber(e.target.value)}
              />
              <p className="mt-1 text-xs text-gray-500">
                {t('admin.ingestion.block.help', 'Imports all transactions from a block')}
              </p>
            </div>
            <button
              type="submit"
              disabled={blockMutation.isPending}
              className="btn-primary w-full disabled:opacity-50"
            >
              {blockMutation.isPending ? t('admin.ingestion.block.ingesting', 'Ingesting...') : t('admin.ingestion.block.start', 'Start Block Import')}
            </button>
            {blockMutation.isSuccess && (
              <p className="text-sm text-green-600">{t('admin.ingestion.block.success', '✓ Block ingestion started')}</p>
            )}
            {blockMutation.isError && (
              <p className="text-sm text-red-600">
                {t('admin.error', 'Error')}: {(blockMutation.error as any)?.response?.data?.detail}
              </p>
            )}
          </form>
        </div>
        </div>
      )}

      {/* Configuration Tab */}
      {activeTab === 'config' && config && (
        <div className="card p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">{t('admin.config.title', 'Configuration')}</h2>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
            <div>
              <p className="text-gray-600">{t('admin.config.app_name', 'App Name')}</p>
              <p className="font-medium text-gray-900">{config.app_name}</p>
            </div>
            <div>
              <p className="text-gray-600">{t('admin.config.version', 'Version')}</p>
              <p className="font-medium text-gray-900">{config.version}</p>
            </div>
            <div>
              <p className="text-gray-600">{t('admin.config.max_trace_depth', 'Max Trace Depth')}</p>
              <p className="font-medium text-gray-900">{config.max_trace_depth}</p>
            </div>
            <div>
              <p className="text-gray-600">{t('admin.config.ml_clustering', 'ML Clustering')}</p>
              <p className="font-medium text-gray-900">
                {config.features?.ml_clustering ? t('admin.enabled', '✓ Enabled') : t('admin.disabled', '✗ Disabled')}
              </p>
            </div>
            <div>
              <p className="text-gray-600">{t('admin.config.ai_agents', 'AI Agents')}</p>
              <p className="font-medium text-gray-900">
                {config.features?.ai_agents ? t('admin.enabled', '✓ Enabled') : t('admin.disabled', '✗ Disabled')}
              </p>
            </div>
            <div>
              <p className="text-gray-600">{t('admin.config.cross_chain', 'Cross-Chain')}</p>
              <p className="font-medium text-gray-900">
                {config.features?.cross_chain ? t('admin.enabled', '✓ Enabled') : t('admin.disabled', '✗ Disabled')}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
