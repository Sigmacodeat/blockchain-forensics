import React, { useMemo, useState } from 'react';
import { Search, AlertTriangle, CheckCircle, XCircle, Loader2, Globe, Shield, TrendingUp, Activity } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { ChainIcon, ChainBadge, getChainName } from '@/components/ui/ChainIcon';
import { exportJSON, exportCSV, exportPrintPDF } from '@/utils/universalScreeningExport';
import UniversalScreeningCharts from '@/components/UniversalScreeningCharts';
import BatchUniversalScreeningModal from '@/components/BatchUniversalScreeningModal';
import MonitorAddressPanel from '@/components/MonitorAddressPanel';
import UniversalScreeningHistoryCharts from '@/components/UniversalScreeningHistoryCharts';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import axios from 'axios';
// dialog components not needed here; BatchUniversalScreeningModal encapsulates its own dialog

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

interface AttributionEvidence {
  source: string;
  confidence: number;
  label: string;
  evidence_type: string;
  timestamp: string;
  verification_method?: string;
}

interface ChainResult {
  chain_id: string;
  address: string;
  risk_score: number;
  risk_level: string;
  is_sanctioned: boolean;
  labels: string[];
  attribution_evidence: AttributionEvidence[];
  transaction_count: number;
  total_value_usd: number;
  counterparties: number;
}

interface UniversalScreeningResult {
  address: string;
  screened_chains: string[];
  total_chains_checked: number;
  aggregate_risk_score: number;
  aggregate_risk_level: string;
  highest_risk_chain?: string;
  is_sanctioned_any_chain: boolean;
  cross_chain_activity: boolean;
  chain_results: Record<string, ChainResult>;
  screening_timestamp: string;
  processing_time_ms: number;
  summary: {
    total_transactions: number;
    total_value_usd: number;
    unique_counterparties: number;
    all_labels: string[];
  };
}

const RiskLevelBadge: React.FC<{ level: string }> = ({ level }) => {
  const colors = {
    critical: 'bg-red-500 text-white',
    high: 'bg-orange-500 text-white',
    medium: 'bg-yellow-500 text-black',
    low: 'bg-blue-500 text-white',
    minimal: 'bg-green-500 text-white',
  };
  
  return (
    <Badge className={colors[level.toLowerCase() as keyof typeof colors] || 'bg-gray-500'}>
      {level.toUpperCase()}
    </Badge>
  );
};

const UniversalScreening: React.FC = () => {
  const { t } = useTranslation();
  const [address, setAddress] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<UniversalScreeningResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [jurisdiction, setJurisdiction] = useState<'all' | 'ofac' | 'eu' | 'uk' | 'un'>('all');
  const [batchInput, setBatchInput] = useState('');
  const [batchRunning, setBatchRunning] = useState(false);
  const [batchSummary, setBatchSummary] = useState<{ success: number; total: number }>({ success: 0, total: 0 });
  const [showBatch, setShowBatch] = useState(false);
  const [showMonitor, setShowMonitor] = useState(false);

  const handleScreen = async () => {
    if (!address.trim()) {
      setError(t('universal_screening.errors.enter_address', 'Please enter a wallet address'));
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `${API_BASE_URL}/api/v1/universal-screening/screen`,
        {
          address: address.trim(),
          chains: null, // null = alle Chains
          max_concurrent: 10,
        },
        {
          headers: {
            Authorization: token ? `Bearer ${token}` : '',
          },
        }
      );

      if (response.data.success) {
        setResult(response.data.data);
      } else {
        setError(response.data.message || t('universal_screening.errors.screening_failed', 'Screening failed'));
      }
    } catch (err: any) {
      console.error('Screening error:', err);
      setError(err.response?.data?.detail || err.message || t('universal_screening.errors.failed_to_screen', 'Failed to screen address'));
    } finally {
      setLoading(false);
    }
  };

  const getRiskColor = (score: number) => {
    if (score >= 0.9) return 'text-red-500';
    if (score >= 0.7) return 'text-orange-500';
    if (score >= 0.4) return 'text-yellow-500';
    if (score >= 0.1) return 'text-blue-500';
    return 'text-green-500';
  };

  const getRiskIcon = (score: number) => {
    if (score >= 0.7) return <AlertTriangle className="h-6 w-6 text-red-500" />;
    if (score >= 0.4) return <Shield className="h-6 w-6 text-yellow-500" />;
    return <CheckCircle className="h-6 w-6 text-green-500" />;
  };

  const isJurisdictionMatch = (chain: any) => {
    if (jurisdiction === 'all') return true;
    if (!chain?.is_sanctioned) return false;
    const evid = (chain?.attribution_evidence || []) as any[];
    const sanc = evid.find(e => e.source === 'sanctions_list');
    const name = (sanc?.metadata?.list_name || '').toString().toUpperCase();
    if (jurisdiction === 'ofac') return name.includes('OFAC') || name.includes('US');
    if (jurisdiction === 'eu') return name.includes('EU');
    if (jurisdiction === 'uk') return name.includes('UK') || name.includes('UNITED KINGDOM');
    if (jurisdiction === 'un') return name.includes('UN');
    return true;
  };

  const filteredChainEntries = useMemo(() => {
    if (!result) return [] as Array<[string, any]>;
    const entries = Object.entries(result.chain_results);
    return entries.filter(([_, chain]) => isJurisdictionMatch(chain));
  }, [result, jurisdiction]);

  const hasExposure = (chain: any) => {
    return !!(chain?.exposure_summary && (Object.keys(chain.exposure_summary.direct_exposure || {}).length > 0 || Object.keys(chain.exposure_summary.indirect_exposure || {}).length > 0));
  };

  const defiKeywords = ['defi','dex','uniswap','aave','curve','lido','maker','compound','staking','lending','pool'];
  const extractDefiLabels = (labels: string[]) => labels.filter(l => defiKeywords.some(k => l.toLowerCase().includes(k)));

  const parseAddresses = (text: string): string[] => {
    const parts = text
      .split(/\r?\n|,|;|\s+/)
      .map(s => s.trim())
      .filter(Boolean);
    // de-duplicate, limit 50
    return Array.from(new Set(parts)).slice(0, 50);
  };

  const handleBatchRun = async () => {
    if (batchRunning) return;
    const items = parseAddresses(batchInput);
    setBatchSummary({ success: 0, total: items.length });
    if (items.length === 0) return;
    setBatchRunning(true);
    try {
      const token = localStorage.getItem('token');
      let success = 0;
      for (const addr of items) {
        try {
          const resp = await axios.post(
            `${API_BASE_URL}/api/v1/universal-screening/screen`,
            { address: addr, chains: null, max_concurrent: 10 },
            { headers: { Authorization: token ? `Bearer ${token}` : '' } }
          );
          if (resp.data?.success) success += 1;
        } catch (_) {
          // continue
        }
        setBatchSummary(prev => ({ ...prev, success }));
      }
    } finally {
      setBatchRunning(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center space-y-2"
      >
        <h1 className="text-4xl font-bold bg-gradient-to-r from-primary via-purple-500 to-blue-500 bg-clip-text text-transparent">
          {t('universal_screening.title', 'Universal Wallet Screening')}
        </h1>
        <p className="text-muted-foreground">
          {t('universal_screening.subtitle', 'Screen any wallet address across 90+ blockchains simultaneously')}
        </p>
      </motion.div>

      {/* Search Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Globe className="h-5 w-5" />
            {t('universal_screening.cross_chain_title', 'Cross-Chain Screening')}
          </CardTitle>
          <CardDescription>
            {t('universal_screening.description', 'Enter a wallet address to screen across all supported chains')}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-2">
            <Input
              type="text"
              placeholder={t('universal_screening.search_placeholder', '0x... or bc1... or any wallet address')}
              value={address}
              onChange={(e) => setAddress(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleScreen()}
              className="flex-1"
              disabled={loading}
            />
            <Button onClick={handleScreen} disabled={loading || !address.trim()}>
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  {t('universal_screening.button_screening', 'Screening...')}
                </>
              ) : (
                <>
                  <Search className="mr-2 h-4 w-4" />
                  {t('universal_screening.button_screen', 'Screen')}
                </>
              )}
            </Button>
          </div>

          {error && (
            <Alert variant="destructive">
              <XCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Results */}
      <AnimatePresence>
        {result && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="space-y-6"
          >
            {/* Toolbar: Export & Jurisdiction Filter */}
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
              <div className="flex items-center gap-2 flex-wrap">
                <Button variant="outline" onClick={() => result && exportJSON(result)}>
                  {t('universal_screening.export.json', 'Export JSON')}
                </Button>
                <Button variant="outline" onClick={() => result && exportCSV(result)}>
                  {t('universal_screening.export.csv', 'Export CSV')}
                </Button>
                <Button variant="outline" onClick={() => result && exportPrintPDF(result)}>
                  {t('universal_screening.export.pdf', 'Export PDF')}
                </Button>
                <Button variant="default" onClick={() => setShowBatch(true)}>
                  {t('universal_screening.toolbar.batch', 'Batch')}
                </Button>
                <Button variant="secondary" onClick={() => setShowMonitor((v) => !v)} disabled={!result || !address.trim()}>
                  {showMonitor ? t('universal_screening.toolbar.hide_monitor', 'Hide Monitor') : t('universal_screening.toolbar.monitor', 'Monitor')}
                </Button>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-sm text-muted-foreground">{t('universal_screening.jurisdiction.title', 'Jurisdiction')}</span>
                <select
                  className="text-sm border rounded px-2 py-1 bg-transparent"
                  value={jurisdiction}
                  onChange={(e) => setJurisdiction(e.target.value as any)}
                >
                  <option value="all">{t('universal_screening.jurisdiction.options.all', 'All')}</option>
                  <option value="ofac">{t('universal_screening.jurisdiction.options.ofac', 'OFAC (US)')}</option>
                  <option value="eu">{t('universal_screening.jurisdiction.options.eu', 'EU')}</option>
                  <option value="uk">{t('universal_screening.jurisdiction.options.uk', 'UK')}</option>
                  <option value="un">{t('universal_screening.jurisdiction.options.un', 'UN')}</option>
                </select>
              </div>
            </div>
            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* Aggregate Risk */}
              <Card className="border-2 border-primary/20">
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-medium flex items-center gap-2">
                    {getRiskIcon(result.aggregate_risk_score)}
                    {t('universal_screening.summary.risk_level', 'Risk Level')}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <div className={`text-3xl font-bold ${getRiskColor(result.aggregate_risk_score)}`}>
                      {(result.aggregate_risk_score * 100).toFixed(1)}%
                    </div>
                    <RiskLevelBadge level={result.aggregate_risk_level} />
                    <Progress 
                      value={result.aggregate_risk_score * 100} 
                      className="h-2"
                    />
                  </div>
                </CardContent>
              </Card>

              {/* Chains Screened */}
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-medium flex items-center gap-2">
                    <Globe className="h-4 w-4" />
                    {t('universal_screening.summary.chains_screened', 'Chains Screened')}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold">{result.total_chains_checked}</div>
                  <p className="text-xs text-muted-foreground">
                    {t('universal_screening.summary.found_on_chains', { count: result.screened_chains.length, defaultValue: 'Found on {{count}} chains' })}
                  </p>
                </CardContent>
              </Card>

              {/* Total Transactions */}
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-medium flex items-center gap-2">
                    <Activity className="h-4 w-4" />
                    {t('universal_screening.summary.total_activity', 'Total Activity')}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold">
                    {result.summary.total_transactions.toLocaleString()}
                  </div>
                  <p className="text-xs text-muted-foreground">
                    {t('universal_screening.summary.counterparties_count', { count: result.summary.unique_counterparties, defaultValue: '{{count}} counterparties' })}
                  </p>
                </CardContent>
              </Card>

              {/* Processing Time */}
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-medium flex items-center gap-2">
                    <TrendingUp className="h-4 w-4" />
                    {t('universal_screening.summary.performance', 'Performance')}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold">
                    {result.processing_time_ms.toFixed(0)}ms
                  </div>
                  <p className="text-xs text-muted-foreground">
                    {result.cross_chain_activity ? t('universal_screening.summary.cross_chain', 'Cross-chain') : t('universal_screening.summary.single_chain', 'Single chain')}
                  </p>
                </CardContent>
              </Card>
            </div>

            {/* Sanctions Alert */}
            {result.is_sanctioned_any_chain && (
              <Alert variant="destructive">
                <AlertTriangle className="h-4 w-4" />
                <AlertDescription className="font-semibold">
                  {t('universal_screening.alert.sanctioned', '⚠️ SANCTIONED ENTITY DETECTED - This address appears on sanctions lists')}
                </AlertDescription>
              </Alert>
            )}

            {/* Charts */}
            {filteredChainEntries.length > 0 && (
              <UniversalScreeningCharts entries={filteredChainEntries as Array<[string, any]>} />
            )}

            {/* Live Monitor */}
            {showMonitor && address.trim() && (
              <MonitorAddressPanel address={address.trim()} />
            )}

            {/* Historical Charts */}
            {address.trim() && (
              <UniversalScreeningHistoryCharts address={address.trim()} />
            )}

            {/* Chain Results */}
            <Card>
              <CardHeader>
                <CardTitle>{t('universal_screening.chain_results.title', 'Chain-Specific Results')}</CardTitle>
                <CardDescription>
                  {t('universal_screening.chain_results.description', 'Detailed breakdown for each blockchain')}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {filteredChainEntries.map(([chainId, chainResult]) => (
                    <motion.div
                      key={chainId}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      className="border rounded-lg p-4 space-y-3"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <ChainIcon chainId={chainResult.chain_id} size="lg" />
                          <div className="font-bold text-lg">
                            {getChainName(chainResult.chain_id)}
                          </div>
                          <RiskLevelBadge level={chainResult.risk_level} />
                          {chainResult.is_sanctioned && (
                            <Badge variant="destructive">{t('universal_screening.chain_results.sanctioned_badge', 'SANCTIONED')}</Badge>
                          )}
                        </div>
                        <div className={`text-2xl font-bold ${getRiskColor(chainResult.risk_score)}`}>
                          {(chainResult.risk_score * 100).toFixed(1)}%
                        </div>
                      </div>

                      <div className="grid grid-cols-3 gap-4 text-sm">
                        <div>
                          <div className="text-muted-foreground">{t('universal_screening.chain_results.transactions', 'Transactions')}</div>
                          <div className="font-semibold">
                            {chainResult.transaction_count.toLocaleString()}
                          </div>
                        </div>
                        <div>
                          <div className="text-muted-foreground">{t('universal_screening.chain_results.value_usd', 'Value (USD)')}</div>
                          <div className="font-semibold">
                            ${chainResult.total_value_usd.toLocaleString()}
                          </div>
                        </div>
                        <div>
                          <div className="text-muted-foreground">{t('universal_screening.chain_results.counterparties', 'Counterparties')}</div>
                          <div className="font-semibold">{chainResult.counterparties}</div>
                        </div>
                      </div>

                      {/* Exposure Insights */}
                      {hasExposure(chainResult) && (
                        <div className="mt-2 text-sm">
                          <div className="text-muted-foreground mb-1">{t('universal_screening.exposure.title', 'Exposure')}</div>
                          <div className="flex flex-wrap gap-2">
                            {Object.entries(chainResult.exposure_summary?.direct_exposure || {}).map(([k, v]: any) => (
                              <Badge key={`direct-${k}`} variant="outline" className="border-orange-300 text-orange-700">
                                {t('universal_screening.exposure.direct', 'Direct')}: {k} {(Number(v) * 100).toFixed(0)}%
                              </Badge>
                            ))}
                            {Object.entries(chainResult.exposure_summary?.indirect_exposure || {}).map(([k, v]: any) => (
                              <Badge key={`indirect-${k}`} variant="outline" className="border-yellow-300 text-yellow-700">
                                {t('universal_screening.exposure.indirect', 'Indirect')}: {k} {(Number(v) * 100).toFixed(0)}%
                              </Badge>
                            ))}
                          </div>
                        </div>
                      )}

                      {chainResult.labels.length > 0 && (
                        <div className="flex flex-wrap gap-2">
                          {chainResult.labels.slice(0, 5).map((label: string, idx: number) => (
                            <Badge key={idx} variant="outline">
                              {label}
                            </Badge>
                          ))}
                          {chainResult.labels.length > 5 && (
                            <Badge variant="outline">
                              {t('universal_screening.chain_results.more_labels', { count: chainResult.labels.length - 5, defaultValue: "+{{count}} more" })}
                            </Badge>
                          )}
                        </div>
                      )}

                      {/* DeFi Insights (derived from labels) */}
                      {extractDefiLabels(chainResult.labels).length > 0 && (
                        <div className="text-sm">
                          <div className="text-muted-foreground mb-1">{t('universal_screening.defi.title', 'DeFi Insights')}</div>
                          <div className="flex flex-wrap gap-2">
                            {extractDefiLabels(chainResult.labels).map((label, idx) => (
                              <Badge key={`defi-${idx}`} variant="secondary">
                                {label}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Attribution Evidence (Glass Box) */}
                      {chainResult.attribution_evidence.length > 0 && (
                        <details className="text-sm">
                          <summary className="cursor-pointer font-medium text-primary hover:underline">
                            {t('universal_screening.attribution_evidence.title', { count: chainResult.attribution_evidence.length, defaultValue: 'View Attribution Evidence ({{count}})' })}
                          </summary>
                          <div className="mt-2 space-y-2 pl-4">
                            {chainResult.attribution_evidence.map((evidence: AttributionEvidence, idx: number) => (
                              <div key={idx} className="border-l-2 border-primary/30 pl-3">
                                <div className="flex items-center gap-2">
                                  <Badge variant="secondary" className="text-xs">
                                    {evidence.source}
                                  </Badge>
                                  <span className="font-semibold">{evidence.label}</span>
                                  <span className="text-muted-foreground">
                                    ({(evidence.confidence * 100).toFixed(0)}% confidence)
                                  </span>
                                </div>
                                <div className="text-xs text-muted-foreground mt-1">
                                  {evidence.evidence_type}
                                  {evidence.verification_method && ` • ${evidence.verification_method}`}
                                </div>
                              </div>
                            ))}
                          </div>
                        </details>
                      )}
                    </motion.div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* All Labels Summary */}
            {result.summary.all_labels.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>{t('universal_screening.all_labels.title', 'All Labels Across Chains')}</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-wrap gap-2">
                    {result.summary.all_labels.map((label, idx) => (
                      <Badge key={idx} variant="secondary">
                        {label}
                      </Badge>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Batch Modal */}
      <BatchUniversalScreeningModal isOpen={showBatch} onClose={() => setShowBatch(false)} />
    </div>
  );
};

export default UniversalScreening;
