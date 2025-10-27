import React, { useMemo, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { useMutation } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { Search, Brain, Link as LinkIcon, ExternalLink, Clipboard, TrendingUp, AlertTriangle, Activity } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { motion, AnimatePresence } from 'framer-motion';

interface EvidenceEdge {
  tx_hash: string;
  from_address: string;
  to_address: string;
  amount: number;
  timestamp: string;
}

interface PatternFinding {
  pattern: string;
  score: number;
  explanation: string;
  evidence: EvidenceEdge[];
}

interface PatternResponse {
  address: string;
  findings: PatternFinding[];
}

export default function PatternsPage({ debounceMs = 300 }: { debounceMs?: number }) {
  const { t } = useTranslation();
  const [address, setAddress] = useState('');
  const [addrInput, setAddrInput] = useState('');
  const [patterns, setPatterns] = useState<string>(''); // e.g. "peel_chain,rapid_movement"
  const [minScore, setMinScore] = useState<number>(0);
  const [limit, setLimit] = useState<number>(50);

  function exportFindingsCSV() {
    const data = detectMutation.data;
    if (!data || !Array.isArray(data.findings)) return;
    const headers = ['pattern','score','explanation','tx_hash','from_address','to_address','amount','timestamp'];
    const rows: string[][] = [];
    for (const f of data.findings) {
      if (Array.isArray(f.evidence) && f.evidence.length > 0) {
        for (const e of f.evidence) {
          rows.push([
            f.pattern,
            String(f.score),
            f.explanation || '',
            e.tx_hash || '',
            e.from_address || '',
            e.to_address || '',
            String(e.amount ?? ''),
            e.timestamp || '',
          ]);
        }
      } else {
        rows.push([f.pattern, String(f.score), f.explanation || '', '', '', '', '', '']);
      }
    }
    const csv = [headers, ...rows]
      .map(r => r.map(v => String(v).replace(/"/g,'""')).join(','))
      .join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `patterns_${data.address || 'address'}_${Date.now()}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }

  function exportFindingsJSON() {
    const data = detectMutation.data;
    if (!data) return;
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `patterns_${data.address || 'address'}_${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }

  function openInInvestigator(addr: string) {
    try {
      const m = window.location.pathname.match(/^\/([a-zA-Z]{2}(?:-[A-Z]{2})?)/)
      const lang = m ? m[1] : 'en'
      window.open(`/${lang}/investigator?address=${encodeURIComponent(addr)}`, '_self')
    } catch {
      window.open(`/investigator?address=${encodeURIComponent(addr)}`, '_self')
    }
  }

  function openTxExplorer(tx: string, chain: string = 'ethereum') {
    const explorers: Record<string, string> = {
      ethereum: `https://etherscan.io/tx/${tx}`,
      polygon: `https://polygonscan.com/tx/${tx}`,
      arbitrum: `https://arbiscan.io/tx/${tx}`,
      optimism: `https://optimistic.etherscan.io/tx/${tx}`,
      base: `https://basescan.org/tx/${tx}`,
    };
    window.open(explorers[chain] || explorers.ethereum, '_blank', 'noopener,noreferrer');
  }

  // Debounce: spiegelt addrInput -> address nach debounceMs
  React.useEffect(() => {
    const h = setTimeout(() => setAddress(addrInput.trim()), debounceMs)
    return () => clearTimeout(h)
  }, [addrInput, debounceMs])

  const addrValid = useMemo(() => /^(0x[a-fA-F0-9]{6,}|bc1[a-z0-9]{6,})$/i.test(address.trim()), [address])

  const detectMutation = useMutation({
    mutationFn: async () => {
      const norm = address.trim()
      if (!norm) throw new Error('address_required');
      const params: Record<string, any> = { address: norm };
      if (patterns.trim()) params.patterns = patterns.trim();
      if (minScore > 0) params.min_score = Math.min(1, Math.max(0, minScore));
      if (limit) params.limit = Math.max(10, Math.min(500, limit));
      const res = await api.get<PatternResponse>('/api/v1/patterns', { params });
      return res.data;
    },
  });

  const findings = useMemo(() => detectMutation.data?.findings || [], [detectMutation.data]);
  const findingsEvidence = useMemo(() => findings.map((f: PatternFinding) => (Array.isArray(f.evidence) ? f.evidence.slice(0, 10) : [])), [findings])

  const getPatternIcon = (pattern: string) => {
    const icons: Record<string, React.ReactNode> = {
      peel_chain: <TrendingUp className="w-4 h-4" />,
      rapid_movement: <Activity className="w-4 h-4" />,
      layering: <Brain className="w-4 h-4" />,
      structuring: <AlertTriangle className="w-4 h-4" />,
    };
    return icons[pattern] || <Brain className="w-4 h-4" />;
  };

  const getScoreBadgeVariant = (score: number): "default" | "secondary" | "destructive" => {
    if (score >= 0.8) return 'destructive';
    if (score >= 0.6) return 'secondary';
    return 'default';
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-blue-50 dark:from-slate-950 dark:via-slate-900 dark:to-slate-950 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header with Gradient */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-primary-600 via-purple-600 to-blue-600 dark:from-primary-700 dark:via-purple-700 dark:to-blue-700 p-8 shadow-2xl"
        >
          <div className="absolute inset-0 bg-grid-white/10 [mask-image:linear-gradient(0deg,white,rgba(255,255,255,0.6))]" />
          <div className="relative z-10">
            <div className="flex items-center gap-3 mb-2">
              <div className="p-3 bg-white/20 dark:bg-white/10 rounded-xl backdrop-blur-sm">
                <Brain className="w-8 h-8 text-white" />
              </div>
              <h1 className="text-4xl font-bold text-white">{t('patterns.title')}</h1>
            </div>
            <p className="text-blue-100 dark:text-blue-200 text-lg max-w-2xl">
              {t('patterns.subtitle')}
            </p>
          </div>
        </motion.div>

        {/* Analysis Form Card */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <Card className="border border-border shadow-lg hover:shadow-xl transition-shadow duration-300">
            <CardHeader className="bg-gradient-to-r from-slate-50 to-blue-50 dark:from-slate-900 dark:to-slate-800 border-b border-border">
              <CardTitle className="text-xl flex items-center gap-2 text-slate-900 dark:text-slate-100">
                <Search className="w-5 h-5 text-primary-600 dark:text-primary-400" />
                {t('patterns.analysis.title')}
              </CardTitle>
              <CardDescription className="text-slate-600 dark:text-slate-400">
                {t('patterns.analysis.description')}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4 pt-6">
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="md:col-span-2">
                  <label htmlFor="addr" className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-2 block">
                    {t('patterns.form.address', 'Adresse')}
                  </label>
                  <Input
                    id="addr"
                    value={addrInput}
                    onChange={(e) => setAddrInput(e.target.value)}
                    placeholder={t('patterns.form.addressPlaceholder', 'Adresse oder bc1…')}
                    className="border-slate-300 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
                    aria-label={t('patterns.form.address', 'Adresse')}
                  />
                </div>
                <div>
                  <label htmlFor="pats" className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-2 block">
                    {t('patterns.form.patterns')}
                  </label>
                  <Input
                    id="pats"
                    value={patterns}
                    onChange={(e) => setPatterns(e.target.value)}
                    placeholder={t('patterns.form.patternsPlaceholder')}
                    className="border-slate-300 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
                    aria-label={t('patterns.form.patterns')}
                  />
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label htmlFor="minscore" className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-2 block">
                      {t('patterns.form.minScore')}
                    </label>
                    <Input
                      id="minscore"
                      type="number"
                      step="0.01"
                      min={0}
                      max={1}
                      value={minScore}
                      onChange={(e) => setMinScore(parseFloat(e.target.value || '0'))}
                      className="border-slate-300 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
                      aria-label={t('patterns.form.minScore')}
                    />
                  </div>
                  <div>
                    <label htmlFor="limit" className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-2 block">
                      {t('patterns.form.limit')}
                    </label>
                    <Input
                      id="limit"
                      type="number"
                      min={10}
                      max={500}
                      value={limit}
                      onChange={(e) => setLimit(parseInt(e.target.value || '50'))}
                      className="border-slate-300 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
                      aria-label={t('patterns.form.limit')}
                    />
                  </div>
                </div>
              </div>
              <div className="flex flex-wrap items-center gap-3">
                <Button
                  onClick={() => detectMutation.mutate()}
                  disabled={detectMutation.isPending || !addrValid}
                  className="bg-gradient-to-r from-primary-600 to-purple-600 hover:from-primary-700 hover:to-purple-700 text-white shadow-lg"
                >
                  <Search className="w-4 h-4 mr-2" />
                  {detectMutation.isPending ? t('patterns.form.analyzing', 'Analysieren') : t('patterns.form.analyze', 'Analysieren')}
                </Button>
                <Button
                  variant="outline"
                  onClick={() => window.dispatchEvent(new CustomEvent('assistant.ask', { detail: { text: `/patterns ${address}` } }))}
                  disabled={!addrValid}
                  className="hover:bg-primary-50 dark:hover:bg-primary-900/20"
                >
                  <Brain className="w-4 h-4 mr-2" />
                  {t('patterns.form.askAssistant')}
                </Button>
              </div>
              <div role="status" aria-live="polite" className="sr-only">
                {detectMutation.isPending ? t('patterns.status.analyzing') : detectMutation.data ? t('patterns.status.complete') : ''}
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Validation Messages */}
        <AnimatePresence>
          {(!addrValid && address.trim().length > 0) && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg p-4 flex items-center gap-3"
            >
              <AlertTriangle className="w-5 h-5 text-amber-600 dark:text-amber-400 flex-shrink-0" />
              <span className="text-sm text-amber-700 dark:text-amber-300">{t('patterns.validation.invalidAddress')}</span>
            </motion.div>
          )}
          {detectMutation.isError && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 flex items-center gap-3"
            >
              <AlertTriangle className="w-5 h-5 text-red-600 dark:text-red-400 flex-shrink-0" />
              <span className="text-sm text-red-700 dark:text-red-300">{t('patterns.error')}</span>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Loading State */}
        <AnimatePresence>
          {detectMutation.isPending && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="space-y-4"
            >
              <Card className="border-2 border-primary-200 dark:border-primary-800 shadow-lg">
                <CardHeader className="bg-gradient-to-r from-primary-50 to-purple-50 dark:from-primary-900/20 dark:to-purple-900/20 border-b dark:border-slate-700">
                  <div className="flex items-center gap-3">
                    <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary-600 dark:border-primary-400" />
                    <CardTitle className="text-slate-900 dark:text-slate-100">{t('patterns.status.analyzing')}</CardTitle>
                  </div>
                  <CardDescription className="text-slate-600 dark:text-slate-400">{t('patterns.status.waiting')}</CardDescription>
                </CardHeader>
              </Card>
              {[0, 1, 2].map((i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.1 }}
                >
                  <Card className="dark:border-slate-800">
                    <CardHeader>
                      <div className="animate-pulse flex items-center justify-between">
                        <div className="h-5 bg-slate-200 dark:bg-slate-700 rounded w-40" />
                        <div className="h-5 bg-slate-200 dark:bg-slate-700 rounded w-24" />
                      </div>
                      <div className="animate-pulse mt-2 h-3 bg-slate-100 dark:bg-slate-800 rounded w-3/4" />
                    </CardHeader>
                    <CardContent>
                      <div className="animate-pulse space-y-2">
                        <div className="h-3 bg-slate-100 dark:bg-slate-800 rounded w-full" />
                        <div className="h-3 bg-slate-100 dark:bg-slate-800 rounded w-5/6" />
                        <div className="h-3 bg-slate-100 dark:bg-slate-800 rounded w-2/3" />
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              ))}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Results Section */}
        <AnimatePresence>
          {detectMutation.data && !detectMutation.isPending && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
            >
              <Card className="border border-border shadow-xl">
                <CardHeader className="bg-gradient-to-r from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20 border-b dark:border-slate-700">
                  <CardTitle className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 text-slate-900 dark:text-slate-100">
                    <div className="flex items-center gap-2">
                      <Activity className="w-5 h-5 text-green-600 dark:text-green-400" />
                      <span>
                        {t('patterns.results.title')} <code className="font-mono bg-slate-100 dark:bg-slate-800 px-2 py-1 rounded text-sm">{detectMutation.data.address}</code>
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={exportFindingsCSV}
                        className="border-green-200 dark:border-green-800 hover:bg-green-50 dark:hover:bg-green-900/20"
                        aria-label={t('patterns.results.export.csv')}
                      >
                        <ExternalLink className="w-4 h-4 mr-2" />
                        {t('patterns.results.export.csv')}
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={exportFindingsJSON}
                        className="border-green-200 dark:border-green-800 hover:bg-green-50 dark:hover:bg-green-900/20"
                        aria-label={t('patterns.results.export.json')}
                      >
                        <ExternalLink className="w-4 h-4 mr-2" />
                        {t('patterns.results.export.json')}
                      </Button>
                    </div>
                  </CardTitle>
                  <CardDescription className="text-slate-600 dark:text-slate-400">
                    {t('patterns.results.patternsFound', { count: findings.length })}
                  </CardDescription>
                </CardHeader>
                <CardContent className="pt-6">
                  {findings.length === 0 ? (
                    <div className="text-center py-12">
                      <Brain className="w-16 h-16 text-slate-300 dark:text-slate-700 mx-auto mb-4" />
                      <p className="text-slate-600 dark:text-slate-400">{t('patterns.results.noPatterns')}</p>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      {findings.map((f, idx) => (
                        <motion.div
                          key={idx}
                          initial={{ opacity: 0, x: -20 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: idx * 0.05 }}
                        >
                          <Card className="border border-border hover:shadow-lg transition-shadow duration-300">
                            <CardHeader className="bg-muted">
                              <div className="flex items-center justify-between">
                                <CardTitle className="text-base capitalize flex items-center gap-2 text-slate-900 dark:text-slate-100">
                                  {getPatternIcon(f.pattern)}
                                  {t(`patterns.patterns.${f.pattern}`, f.pattern.replace('_', ' '))}
                                </CardTitle>
                                <Badge variant={getScoreBadgeVariant(f.score)} className="shadow-sm">
                                  {t('patterns.pattern.score', { score: (f.score * 100).toFixed(0) })}
                                </Badge>
                              </div>
                              <CardDescription className="text-sm mt-2 text-slate-600 dark:text-slate-400">
                                {f.explanation}
                              </CardDescription>
                            </CardHeader>
                            <CardContent className="pt-4">
                              {Array.isArray(f.evidence) && f.evidence.length > 0 ? (
                                <div className="overflow-x-auto">
                                  <Table>
                                    <caption className="sr-only">{t('patterns.pattern.evidence')}</caption>
                                    <TableHeader>
                                      <TableRow className="bg-muted">
                                        <TableHead scope="col" className="text-slate-700 dark:text-slate-300">{t('patterns.table.tx')}</TableHead>
                                        <TableHead scope="col" className="text-slate-700 dark:text-slate-300">{t('patterns.table.from')}</TableHead>
                                        <TableHead scope="col" className="text-slate-700 dark:text-slate-300">{t('patterns.table.to')}</TableHead>
                                        <TableHead scope="col" className="text-slate-700 dark:text-slate-300">{t('patterns.table.amount')}</TableHead>
                                        <TableHead scope="col" className="text-slate-700 dark:text-slate-300">{t('patterns.table.time')}</TableHead>
                                        <TableHead scope="col" className="text-right text-slate-700 dark:text-slate-300">{t('patterns.table.actions')}</TableHead>
                                      </TableRow>
                                    </TableHeader>
                                    <TableBody>
                                      {findingsEvidence[idx].map((e, i) => (
                                        <TableRow key={i} className="hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors">
                                          <TableCell className="font-mono text-slate-900 dark:text-slate-100">
                                            <button
                                              className="inline-flex items-center gap-1 text-primary-600 dark:text-primary-400 hover:underline"
                                              onClick={() => openTxExplorer(e.tx_hash)}
                                            >
                                              {e.tx_hash.slice(0, 10)}… <ExternalLink className="w-3 h-3" />
                                            </button>
                                          </TableCell>
                                          <TableCell className="font-mono text-slate-700 dark:text-slate-300">{e.from_address.slice(0, 10)}…</TableCell>
                                          <TableCell className="font-mono text-slate-700 dark:text-slate-300">{e.to_address.slice(0, 10)}…</TableCell>
                                          <TableCell className="text-slate-700 dark:text-slate-300">{e.amount}</TableCell>
                                          <TableCell className="text-xs text-slate-600 dark:text-slate-400">{e.timestamp}</TableCell>
                                          <TableCell className="text-right">
                                            <div className="flex items-center gap-2 justify-end">
                                              <Button
                                                size="sm"
                                                variant="outline"
                                                onClick={() => openInInvestigator(e.tx_hash)}
                                                className="border border-border hover:bg-muted"
                                              >
                                                <LinkIcon className="w-3 h-3 mr-1" />
                                                {t('patterns.table.investigator')}
                                              </Button>
                                              <Button
                                                size="sm"
                                                variant="outline"
                                                onClick={() => { try { const m = window.location.pathname.match(/^\/([a-zA-Z]{2}(?:-[A-Z]{2})?)/); const lang = m ? m[1] : 'en'; const params = new URLSearchParams({ address: e.to_address, action: 'expand' }); window.open(`/${lang}/investigator?${params.toString()}`, '_self'); } catch { window.open(`/investigator?address=${encodeURIComponent(e.to_address)}&action=expand`, '_self'); } }}
                                                className="border border-border hover:bg-muted"
                                              >
                                                {t('patterns.table.expand')}
                                              </Button>
                                              <Button
                                                size="sm"
                                                variant="outline"
                                                onClick={() => { try { const m = window.location.pathname.match(/^\/([a-zA-Z]{2}(?:-[A-Z]{2})?)/); const lang = m ? m[1] : 'en'; const params = new URLSearchParams({ address: e.from_address, action: 'path', target: e.to_address }); window.open(`/${lang}/investigator?${params.toString()}`, '_self'); } catch { window.open(`/investigator?address=${encodeURIComponent(e.from_address)}&action=path&target=${encodeURIComponent(e.to_address)}`, '_self'); } }}
                                                className="border border-border hover:bg-muted"
                                              >
                                                {t('patterns.table.path')}
                                              </Button>
                                              <Button
                                                size="sm"
                                                variant="outline"
                                                onClick={() => navigator.clipboard?.writeText(JSON.stringify(e))}
                                                className="border border-border hover:bg-muted"
                                              >
                                                <Clipboard className="w-3 h-3 mr-1" />
                                                {t('patterns.table.copy')}
                                              </Button>
                                            </div>
                                          </TableCell>
                                        </TableRow>
                                      ))}
                                    </TableBody>
                                  </Table>
                                </div>
                              ) : (
                                <div className="text-sm text-slate-600 dark:text-slate-400 text-center py-8">
                                  {t('patterns.pattern.noEvidence')}
                                </div>
                              )}
                            </CardContent>
                          </Card>
                        </motion.div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
