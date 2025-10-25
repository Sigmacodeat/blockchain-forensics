import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api';
import {
  BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts';
import { 
  Network, Activity, TrendingUp, AlertCircle, 
  GitBranch, Zap, Users, Info
} from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface NetworkStats {
  nodes: number;
  edges: number;
  density: number;
  avg_degree: number;
  active_nodes: number;
}

interface Community {
  id: number;
  size: number;
  avg_taint: number;
  risk_levels: Record<string, number>;
}

interface CentralityAddress {
  address: string;
  score: number;
  taint: number;
  labels?: string[];
}

interface Pattern {
  addresses: string[];
  values: number[];
  total_value?: number;
  risk_score: number;
}

const GraphAnalyticsPage: React.FC = () => {
  const { t } = useTranslation();
  const [selectedTab, setSelectedTab] = useState<'overview' | 'communities' | 'patterns'>('overview');
  const [communityAlgorithm, setCommunityAlgorithm] = useState<'louvain' | 'label_propagation'>('louvain');
  const [centralityAlgorithm, setCentralityAlgorithm] = useState<'pagerank' | 'betweenness' | 'closeness'>('pagerank');
  // Zeitfenster & Layer-Toggle
  const [fromTs, setFromTs] = useState<string>('');
  const [toTs, setToTs] = useState<string>('');
  const [enableBridgeLayer, setEnableBridgeLayer] = useState<boolean>(true);

  // Fetch Network Stats
  const { data: networkStats, isLoading: statsLoading } = useQuery<NetworkStats>({
    queryKey: ['networkStats', fromTs, toTs, enableBridgeLayer],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (fromTs) params.set('from_timestamp', fromTs);
      if (toTs) params.set('to_timestamp', toTs);
      if (enableBridgeLayer) params.set('enable_bridge', 'true');
      const url = `/api/v1/graph-analytics/stats/network${params.toString() ? `?${params.toString()}` : ''}`;
      const response = await api.get(url);
      return response.data;
    }
  });

  // Fetch Degree Distribution
  const { data: degreeData } = useQuery({
    queryKey: ['degreeDistribution', fromTs, toTs],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (fromTs) params.set('from_timestamp', fromTs);
      if (toTs) params.set('to_timestamp', toTs);
      const url = `/api/v1/graph-analytics/stats/degree-distribution${params.toString() ? `?${params.toString()}` : ''}`;
      const response = await api.get(url);
      return response.data;
    }
  });

  // Fetch Communities
  const { data: communitiesData, isLoading: communitiesLoading } = useQuery({
    queryKey: ['communities', communityAlgorithm, fromTs, toTs, enableBridgeLayer],
    queryFn: async () => {
      const body: any = {
        algorithm: communityAlgorithm,
        limit: 20
      };
      if (fromTs) body.from_timestamp = fromTs;
      if (toTs) body.to_timestamp = toTs;
      body.enable_bridge = enableBridgeLayer;
      const response = await api.post(`/api/v1/graph-analytics/communities/detect`, body);
      return response.data;
    },
    enabled: selectedTab === 'communities'
  });

  // Fetch Centrality
  const { data: centralityData } = useQuery({
    queryKey: ['centrality', centralityAlgorithm, fromTs, toTs],
    queryFn: async () => {
      const body: any = { algorithm: centralityAlgorithm, top_n: 20 };
      if (fromTs) body.from_timestamp = fromTs;
      if (toTs) body.to_timestamp = toTs;
      const response = await api.post(`/api/v1/graph-analytics/centrality/calculate`, body);
      return response.data;
    }
  });

  // Fetch Patterns (Circles)
  const { data: circlesData, isLoading: patternsLoading } = useQuery({
    queryKey: ['patterns-circles', fromTs, toTs, enableBridgeLayer],
    queryFn: async () => {
      const body: any = {
        min_length: 3,
        max_length: 8,
        min_total_value: 0
      };
      if (fromTs) body.from_timestamp = fromTs;
      if (toTs) body.to_timestamp = toTs;
      body.enable_bridge = enableBridgeLayer;
      const response = await api.post(`/api/v1/graph-analytics/patterns/circles`, body);
      return response.data;
    },
    enabled: selectedTab === 'patterns'
  });

  // Fetch Hub Analysis
  const { data: hubsData } = useQuery({
    queryKey: ['hubs'],
    queryFn: async () => {
      const response = await api.get(`/api/v1/graph-analytics/stats/hubs`, { params: { min_degree: 10, top_n: 20 } });
      return response.data;
    }
  });

  const stats = networkStats;

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
            <Network className="h-8 w-8 text-primary-600" />
            {t('graph.header.title', 'Graph Analytics & Network Intelligence')}
          </h1>
          <p className="text-gray-600 mt-1">
            {t('graph.header.subtitle', 'Erweiterte Netzwerk-Analysen und Pattern Detection')}
          </p>
        </div>

        {/* Tab Navigation & Filterleiste */}
        <div className="mb-6 border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            {[
              { key: 'overview', label: t('graph.tabs.overview', 'Network Overview'), icon: Activity },
              { key: 'communities', label: t('graph.tabs.communities', 'Community Detection'), icon: Users },
              { key: 'patterns', label: t('graph.tabs.patterns', 'Pattern Detection'), icon: GitBranch }
            ].map(({ key, label, icon: Icon }) => (
              <button
                key={key}
                onClick={() => setSelectedTab(key as any)}
                className={`
                  flex items-center gap-2 px-1 py-4 border-b-2 font-medium text-sm
                  ${selectedTab === key
                    ? 'border-primary-500 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }
                `}
              >
                <Icon className="h-5 w-5" />
                {label}
              </button>
            ))}
          </nav>
          {/* Filterleiste */}
          <div className="mt-4 grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm text-gray-600 mb-1">{t('graph.filters.from', 'Von (ISO)')}</label>
              <input
                type="text"
                className="px-3 py-2 border border-gray-300 rounded-md w-full"
                placeholder={t('graph.filters.from_ph', '2021-01-01T00:00:00Z')}
                value={fromTs}
                onChange={(e) => setFromTs(e.target.value)}
              />
            </div>
            <div>
              <label className="block text-sm text-gray-600 mb-1">{t('graph.filters.to', 'Bis (ISO)')}</label>
              <input
                type="text"
                className="px-3 py-2 border border-gray-300 rounded-md w-full"
                placeholder={t('graph.filters.to_ph', '2023-12-31T23:59:59Z')}
                value={toTs}
                onChange={(e) => setToTs(e.target.value)}
              />
            </div>
            <div className="flex items-end">
              <label className="inline-flex items-center gap-2 text-sm">
                <input type="checkbox" className="checkbox" checked={enableBridgeLayer} onChange={(e) => setEnableBridgeLayer(e.target.checked)} />
                {t('graph.filters.cross_chain', 'Cross-Chain (Bridge-Layer)')}
              </label>
            </div>
          </div>
        </div>

        {/* Overview Tab */}
        {selectedTab === 'overview' && (
          <div className="space-y-6">
            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
              {statsLoading ? (
                <div className="col-span-5 text-center py-8">{t('graph.loading.stats', 'Loading stats...')}</div>
              ) : (
                <>
                  <StatsCard
                    title={t('graph.cards.total_nodes', 'Total Nodes')}
                    value={stats?.nodes || 0}
                    icon={Network}
                    color="blue"
                  />
                  <StatsCard
                    title={t('graph.cards.total_edges', 'Total Edges')}
                    value={stats?.edges || 0}
                    icon={GitBranch}
                    color="green"
                  />
                  <StatsCard
                    title={t('graph.cards.density', 'Network Density')}
                    value={(stats?.density || 0).toFixed(4)}
                    icon={Activity}
                    color="purple"
                  />
                  <StatsCard
                    title={t('graph.cards.avg_degree', 'Avg Degree')}
                    value={(stats?.avg_degree || 0).toFixed(2)}
                    icon={TrendingUp}
                    color="orange"
                  />
                  <StatsCard
                    title={t('graph.cards.active_nodes', 'Active Nodes')}
                    value={stats?.active_nodes || 0}
                    icon={Zap}
                    color="red"
                  />
                </>
              )}
            </div>

          {/* Degree Distribution Chart */}
          {degreeData?.distribution && (
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-semibold mb-4">{t('graph.degree.title', 'Degree Distribution')}</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={degreeData.distribution.slice(0, 20)}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="degree" label={{ value: t('graph.degree.x', 'Degree'), position: 'insideBottom', offset: -5 }} />
                  <YAxis label={{ value: t('graph.degree.y', 'Count'), angle: -90, position: 'insideLeft' }} />
                  <Tooltip />
                  <Bar dataKey="count" fill="#0284c7" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
          {/* Hub Analysis */}
          {hubsData?.hubs && (
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-semibold mb-4">{t('graph.hubs.title', 'Network Hubs (High Degree Nodes)')}</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {hubsData.hubs.slice(0, 6).map((hub: any, idx: number) => (
                  <div key={idx} className="p-4 border border-gray-200 rounded-lg">
                    <code className="text-sm font-mono text-gray-700 block mb-2">
                      {hub.address.slice(0, 16)}...
                    </code>
                    <div className="grid grid-cols-3 gap-2 text-sm">
                      <div>
                        <div className="text-gray-500">{t('graph.hubs.in', 'In')}</div>
                        <div className="font-semibold">{hub.in_degree}</div>
                      </div>
                      <div>
                        <div className="text-gray-500">{t('graph.hubs.out', 'Out')}</div>
                        <div className="font-semibold">{hub.out_degree}</div>
                      </div>
                      <div>
                        <div className="text-gray-500">{t('graph.hubs.total', 'Total')}</div>
                        <div className="font-semibold">{hub.total_degree}</div>
                      </div>
                    </div>
                    <div className="mt-2">
                      <span className={`text-xs px-2 py-1 rounded ${
                        hub.risk_level === 'HIGH' || hub.risk_level === 'CRITICAL'
                          ? 'bg-red-100 text-red-700'
                          : hub.risk_level === 'MEDIUM'
                          ? 'bg-yellow-100 text-yellow-700'
                          : 'bg-green-100 text-green-700'
                      }`}>
                        {hub.risk_level}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
          {/* Centrality Analysis */}
          {centralityData?.top_addresses && (
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-semibold mb-4">{t('graph.centrality.title', 'Centrality Analysis')}</h3>
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {centralityData.top_addresses.slice(0, 10).map((addr: any, idx: number) => (
                    <div key={idx} className="flex items-center justify-between p-3 bg-gray-50 rounded">
                      <div className="flex-1">
                        <code className="text-sm font-mono text-gray-700">
                          {addr.address.slice(0, 10)}...{addr.address.slice(-8)}
                        </code>
                        {addr.labels && addr.labels.length > 0 && (
                          <div className="flex gap-1 mt-1">
                            {addr.labels.slice(0, 2).map((label: string, i: number) => (
                              <span key={i} className="text-xs px-2 py-0.5 bg-primary-100 text-primary-700 rounded">
                                {label}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                      <div className="text-right">
                        <div className="text-sm font-semibold text-gray-900">
                          {addr.score.toFixed(6)}
                        </div>
                        <div className="text-xs text-gray-500">
                          {t('graph.centrality.taint', 'Taint')}: {(addr.taint * 100).toFixed(1)}%
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
        )}
        {/* Communities Tab */}
        {selectedTab === 'communities' && (
          <div className="space-y-6">
            <div className="bg-white p-6 rounded-lg shadow">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold">{t('graph.communities.title', 'Community Detection')}</h3>
                <select
                  value={communityAlgorithm}
                  onChange={(e) => setCommunityAlgorithm(e.target.value as any)}
                  className="px-3 py-2 border border-gray-300 rounded-md"
                >
                  <option value="louvain">{t('graph.communities.louvain', 'Louvain (Modularity)')}</option>
                  <option value="label_propagation">{t('graph.communities.label_propagation', 'Label Propagation')}</option>
                </select>
              </div>

              {communitiesLoading ? (
                <div className="text-center py-8">{t('graph.communities.loading', 'Detecting communities...')}</div>
              ) : communitiesData?.communities ? (
                <div className="space-y-4">
                  {/* Statistics */}
                  <div className="grid grid-cols-3 gap-4 p-4 bg-gray-50 rounded">
                    <div>
                      <div className="text-gray-500 text-sm">{t('graph.communities.total', 'Total Communities')}</div>
                      <div className="text-2xl font-bold">{communitiesData.communities.length}</div>
                    </div>
                    <div>
                      <div className="text-gray-500 text-sm">{t('graph.communities.avg_size', 'Avg Size')}</div>
                      <div className="text-2xl font-bold">
                        {communitiesData.statistics?.avg_community_size?.toFixed(1) || 0}
                      </div>
                    </div>
                    <div>
                      <div className="text-gray-500 text-sm">{t('graph.communities.algorithm', 'Algorithm')}</div>
                      <div className="text-lg font-semibold capitalize">{communityAlgorithm}</div>
                    </div>
                  </div>

                  {/* Communities List */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {communitiesData.communities.slice(0, 10).map((comm: Community) => (
                      <div key={comm.id} className="p-4 border border-gray-200 rounded-lg">
                        <div className="flex justify-between items-start mb-3">
                          <div>
                            <div className="text-sm text-gray-500">Community #{comm.id}</div>
                            <div className="text-2xl font-bold">{comm.size} members</div>
                          </div>
                          <div className="text-right">
                            <div className="text-sm text-gray-500">{t('graph.communities.avg_taint', 'Avg Taint')}</div>
                            <div className={`text-lg font-semibold ${
                              comm.avg_taint > 0.7 ? 'text-red-600' :
                              comm.avg_taint > 0.3 ? 'text-yellow-600' : 'text-green-600'
                            }`}>
                              {(comm.avg_taint * 100).toFixed(1)}%
                            </div>
                          </div>
                        </div>
                        {comm.risk_levels && (
                          <div className="flex gap-2 flex-wrap">
                            {Object.entries(comm.risk_levels).map(([level, count]) => (
                              <span key={level} className="text-xs px-2 py-1 bg-gray-100 rounded">
                                {level}: {count}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  {t('graph.communities.empty', 'Click "Detect Communities" to analyze network structure')}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Patterns Tab */}
        {selectedTab === 'patterns' && (
          <div className="space-y-6">
            {/* Circle Detection */}
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <AlertCircle className="h-5 w-5 text-orange-600" />
                {t('graph.patterns.title', 'Circular Patterns (Potential Money Laundering)')}
              </h3>
              
              {patternsLoading ? (
                <div className="text-center py-8">{t('graph.patterns.loading', 'Detecting patterns...')}</div>
              ) : circlesData?.detected && circlesData.detected.length > 0 ? (
                <div className="space-y-4">
                  {/* Stats */}
                  <div className="grid grid-cols-3 gap-4 p-4 bg-orange-50 rounded">
                    <div>
                      <div className="text-gray-600 text-sm">{t('graph.patterns.detected', 'Detected Circles')}</div>
                      <div className="text-2xl font-bold text-orange-600">{circlesData.count}</div>
                    </div>
                    <div>
                      <div className="text-gray-600 text-sm">{t('graph.patterns.high_risk', 'High Risk')}</div>
                      <div className="text-2xl font-bold text-red-600">
                        {circlesData.statistics?.high_risk_count || 0}
                      </div>
                    </div>
                    <div>
                      <div className="text-gray-600 text-sm">{t('graph.patterns.total_value', 'Total Value')}</div>
                      <div className="text-lg font-semibold">
                        {circlesData.statistics?.total_value_circulated?.toFixed(2) || 0} ETH
                      </div>
                    </div>
                  </div>

                  {/* Circles */}
                  {circlesData.detected.slice(0, 10).map((circle: Pattern, idx: number) => (
                    <div key={idx} className={`p-4 border-2 rounded-lg ${
                      circle.risk_score >= 70 ? 'border-red-300 bg-red-50' :
                      circle.risk_score >= 40 ? 'border-yellow-300 bg-yellow-50' :
                      'border-gray-200 bg-white'
                    }`}>
                      <div className="flex justify-between items-start mb-2">
                        <div>
                          <div className="text-sm text-gray-600">
                            {t('graph.patterns.circle_length', 'Circle Length')}: {circle.addresses.length} {t('graph.patterns.hops', 'hops')}
                          </div>
                          {circle.total_value && (
                            <div className="text-lg font-semibold">
                              {t('graph.patterns.total', 'Total')}: {circle.total_value.toFixed(4)} ETH
                            </div>
                          )}
                        </div>
                        <div className="text-right">
                          <div className="text-sm text-gray-600">{t('graph.patterns.risk_score', 'Risk Score')}</div>
                          <div className={`text-2xl font-bold ${
                            circle.risk_score >= 70 ? 'text-red-600' :
                            circle.risk_score >= 40 ? 'text-yellow-600' : 'text-green-600'
                          }`}>
                            {circle.risk_score}
                          </div>
                        </div>
                      </div>
                      <div className="mt-3">
                        <div className="text-xs text-gray-500 mb-1">{t('graph.patterns.tx_path', 'Transaction Path:')}</div>
                        <div className="space-y-1">
                          {circle.addresses.slice(0, 5).map((addr, i) => (
                            <div key={i} className="flex items-center gap-2 text-xs">
                              <code className="font-mono text-gray-700">
                                {addr.slice(0, 10)}...{addr.slice(-8)}
                              </code>
                              {i < circle.values.length && (
                                <span className="text-gray-500">
                                  → {circle.values[i].toFixed(4)} ETH
                                </span>
                              )}
                            </div>
                          ))}
                          {circle.addresses.length > 5 && (
                            <div className="text-gray-400 text-xs">
                              ... +{circle.addresses.length - 5} {t('graph.patterns.more_addresses', 'more addresses')}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500 flex flex-col items-center gap-2">
                  <Info className="h-12 w-12 text-gray-400" />
                  <p>{t('graph.patterns.empty_title', 'No circular patterns detected')}</p>
                  <p className="text-sm">{t('graph.patterns.empty_desc', 'This is a good sign - no obvious money laundering circles found')}</p>
                </div>
              )}
            </div>
          </div>
        )}
    </div>
  );
};

// Stats Card Component
interface StatsCardProps {
  title: string;
  value: string | number;
  icon: React.ElementType;
  color: 'blue' | 'green' | 'purple' | 'orange' | 'red';
}

const StatsCard: React.FC<StatsCardProps> = ({ title, value, icon: Icon, color }) => {
  const colorClasses = {
    blue: 'bg-primary-50 text-primary-600',
    green: 'bg-green-50 text-green-600',
    purple: 'bg-purple-50 text-purple-600',
    orange: 'bg-orange-50 text-orange-600',
    red: 'bg-red-50 text-red-600'
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-600">{title}</p>
          <p className="text-2xl font-bold text-gray-900 mt-1">{value}</p>
        </div>
        <div className={`p-3 rounded-lg ${colorClasses[color]}`}>
          <Icon className="h-6 w-6" />
        </div>
      </div>
    </div>
  );
};

export default GraphAnalyticsPage;
