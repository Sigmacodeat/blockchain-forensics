import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Slider } from '@/components/ui/slider';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { LabelWithTooltip } from '@/components/ui/tooltip';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { PlayCircle, Save, Settings, Activity, Clock, CheckCircle2, AlertCircle, Loader2, Sparkles } from 'lucide-react';
import { useTranslation } from 'react-i18next';

interface AutomationSettings {
  enabled: boolean;
  risk_threshold: number; // 0..1
  min_amount_usd: number;
  auto_create_case: boolean;
  auto_trace_depth: number; // 0..10
  report_template: string;
}

interface SimulationRequest {
  hours?: number;
  sample_size?: number;
}

interface SimulationResult {
  evaluated: number;
  would_create_cases: number;
  would_trigger_traces: number;
  high_priority: number;
}

export default function AutomationPage() {
  const { t } = useTranslation();
  const qc = useQueryClient();
  const { data: settings, isPending } = useQuery<AutomationSettings>({
    queryKey: ['automationSettings'],
    queryFn: async () => {
      const res = await api.get('/api/v1/automation/settings');
      return res.data;
    },
    refetchOnWindowFocus: false,
  });

  const saveMutation = useMutation({
    mutationFn: async (payload: AutomationSettings) => {
      const res = await api.put('/api/v1/automation/settings', payload);
      return res.data as AutomationSettings;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['automationSettings'] }),
  });

  const simulateMutation = useMutation({
    mutationFn: async (payload: SimulationRequest) => {
      const res = await api.post('/api/v1/automation/simulate', payload);
      return res.data as SimulationResult;
    },
  });

  const [local, setLocal] = useState<AutomationSettings | null>(null);
  const { data: recent } = useQuery<{ items: Array<{ address: string; chain: string; depth: number; status: string; error?: string }>}>({
    queryKey: ['automationRecent'],
    queryFn: async () => {
      const res = await api.get('/api/v1/automation/recent');
      return res.data;
    },
    refetchInterval: 5000,
  });

  useEffect(() => {
    if (settings && !local) setLocal(settings);
  }, [settings]);

  const disabled = isPending || !local || saveMutation.isPending;

  return (
    <div className="min-h-screen space-y-8 p-6" aria-labelledby="automation-title">
      {/* Hero Header with Glassmorphism */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-primary-500/10 via-purple-500/10 to-blue-500/10 dark:from-primary-900/20 dark:via-purple-900/20 dark:to-blue-900/20 backdrop-blur-sm border border-primary-200/20 dark:border-primary-800/30 p-8"
      >
        <div className="relative z-10">
          <div className="flex items-center gap-3 mb-3">
            <div className="p-3 rounded-xl bg-gradient-to-br from-primary-500 to-purple-600 shadow-lg shadow-primary-500/50 dark:shadow-primary-500/30">
              <Settings className="w-7 h-7 text-white" />
            </div>
            <div>
              <h1 id="automation-title" className="text-4xl font-bold bg-gradient-to-r from-primary-600 to-purple-600 dark:from-primary-400 dark:to-purple-400 bg-clip-text text-transparent">
                {t('automation.title')}
              </h1>
            </div>
          </div>
          <p className="text-base text-slate-600 dark:text-slate-300 max-w-3xl">
            {t('automation.subtitle')}
          </p>
        </div>
        {/* Animated Background Pattern */}
        <div className="absolute inset-0 opacity-20 dark:opacity-10">
          <div className="absolute top-0 left-1/4 w-64 h-64 bg-primary-500 rounded-full filter blur-3xl animate-pulse" />
          <div className="absolute bottom-0 right-1/4 w-64 h-64 bg-purple-500 rounded-full filter blur-3xl animate-pulse" style={{ animationDelay: '1s' }} />
        </div>
      </motion.div>

      {/* Settings Card */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
      >
        <Card className="border border-border shadow-xl shadow-slate-200/50 dark:shadow-slate-900/50 hover:shadow-2xl transition-shadow duration-300">
          <CardHeader className="bg-gradient-to-r from-slate-50 to-slate-100 dark:from-slate-900/50 dark:to-slate-800/50 border-b border-border">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-primary-100 dark:bg-primary-900/30">
                <Sparkles className="w-5 h-5 text-primary-600 dark:text-primary-400" />
              </div>
              <div>
                <CardTitle className="text-xl font-bold text-slate-900 dark:text-slate-100">
                  {t('automation.settings.title')}
                </CardTitle>
                <CardDescription className="text-slate-600 dark:text-slate-400">
                  {t('automation.settings.description')}
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-6 p-6">
            {/* Enabled Toggle */}
            <div className="flex items-center justify-between p-4 rounded-xl bg-muted border border-border hover:border-primary-300 dark:hover:border-primary-700 transition-colors">
              <div className="flex-1">
                <Label htmlFor="enabled" className="text-base font-semibold text-slate-900 dark:text-slate-100">
                  {t('automation.settings.enabled')}
                </Label>
                <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
                  {t('automation.settings.enabledDesc')}
                </p>
              </div>
              <Switch
                id="enabled"
                checked={!!local?.enabled}
                onCheckedChange={(v) => setLocal((s) => (s ? { ...s, enabled: v } : s))}
                aria-label={t('automation.settings.enabledDesc')}
                className="data-[state=checked]:bg-primary-600"
              />
            </div>

            {/* Risk Threshold Slider */}
            <div className="p-4 rounded-xl bg-gradient-to-br from-orange-50 to-red-50 dark:from-orange-950/30 dark:to-red-950/30 border border-orange-200 dark:border-orange-900/50">
              <LabelWithTooltip
                label={t('automation.settings.riskThresholdValue', { value: (local?.risk_threshold ?? 0).toFixed(2) })}
                tooltip={t('automation.settings.riskThresholdTooltip')}
                className="mb-3 text-base font-semibold text-slate-900 dark:text-slate-100"
              />
              <span id="risk-label" className="sr-only">{t('automation.settings.riskThreshold')}</span>
              <div className="relative">
                <Slider
                  min={0}
                  max={1}
                  step={0.01}
                  value={[local?.risk_threshold ?? 0]}
                  onValueChange={([v]) => setLocal((s) => (s ? { ...s, risk_threshold: v } : s))}
                  aria-label={t('automation.settings.riskThreshold')}
                  aria-labelledby="risk-label"
                  className="[&_[role=slider]]:bg-gradient-to-r [&_[role=slider]]:from-orange-500 [&_[role=slider]]:to-red-600 [&_[role=slider]]:border-2 [&_[role=slider]]:border-white [&_[role=slider]]:shadow-lg"
                />
                <div className="flex justify-between mt-2 text-xs font-medium">
                  <span className="text-green-600 dark:text-green-400">0.00 (Safe)</span>
                  <span className="text-yellow-600 dark:text-yellow-400">0.50 (Medium)</span>
                  <span className="text-red-600 dark:text-red-400">1.00 (Critical)</span>
                </div>
              </div>
              <p className="text-sm text-slate-600 dark:text-slate-400 mt-3 flex items-start gap-2">
                <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                {t('automation.settings.riskThresholdHelp')}
              </p>
            </div>

            {/* Min Amount & Trace Depth */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-2">
                <LabelWithTooltip
                  label={t('automation.settings.minAmount')}
                  tooltip={t('automation.settings.minAmountTooltip')}
                  htmlFor="min_amount"
                  className="text-sm font-semibold text-slate-900 dark:text-slate-100"
                />
                <div className="relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500 dark:text-slate-400 font-medium">$</span>
                  <Input
                    id="min_amount"
                    type="number"
                    value={local?.min_amount_usd ?? ''}
                    onChange={(e) => setLocal((s) => (s ? { ...s, min_amount_usd: Number(e.target.value) } : s))}
                    inputMode="decimal"
                    className="pl-8 bg-white dark:bg-slate-900 border-slate-300 dark:border-slate-700 focus:border-primary-500 focus:ring-primary-500"
                    aria-label={t('automation.settings.minAmount')}
                    aria-describedby="min-amount-help"
                  />
                </div>
                <p id="min-amount-help" className="text-xs text-slate-600 dark:text-slate-400">
                  {t('automation.settings.minAmountHelp')}
                </p>
              </div>
              <div className="space-y-2">
                <Label htmlFor="depth" className="text-sm font-semibold text-slate-900 dark:text-slate-100">
                  {t('automation.settings.traceDepth')}
                </Label>
                <Input
                  id="depth"
                  type="number"
                  min={0}
                  max={10}
                  value={local?.auto_trace_depth ?? 3}
                  onChange={(e) => setLocal((s) => (s ? { ...s, auto_trace_depth: Number(e.target.value) } : s))}
                  className="bg-white dark:bg-slate-900 border-slate-300 dark:border-slate-700 focus:border-primary-500 focus:ring-primary-500"
                  aria-label={t('automation.settings.traceDepth')}
                  aria-describedby="depth-help"
                />
                <p id="depth-help" className="text-xs text-slate-600 dark:text-slate-400">
                  {t('automation.settings.traceDepthHelp')}
                </p>
              </div>
            </div>

            {/* Auto Create Case & Report Template */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="p-4 rounded-xl bg-muted border border-border">
                <div className="flex items-center gap-3">
                  <Switch
                    id="auto_case"
                    checked={!!local?.auto_create_case}
                    onCheckedChange={(v) => setLocal((s) => (s ? { ...s, auto_create_case: v } : s))}
                    aria-label={t('automation.settings.autoCreateCase')}
                    className="data-[state=checked]:bg-primary-600"
                  />
                  <Label htmlFor="auto_case" className="text-sm font-semibold text-slate-900 dark:text-slate-100 cursor-pointer">
                    {t('automation.settings.autoCreateCase')}
                  </Label>
                </div>
              </div>

              <div className="space-y-2">
                <Label className="text-sm font-semibold text-slate-900 dark:text-slate-100">
                  {t('automation.settings.reportTemplate')}
                </Label>
                <Select
                  value={local?.report_template ?? 'standard'}
                  onValueChange={(v) => setLocal((s) => (s ? { ...s, report_template: v } : s))}
                >
                  <SelectTrigger aria-label={t('automation.settings.reportTemplate')} className="bg-white dark:bg-slate-900 border-slate-300 dark:border-slate-700">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="standard">{t('automation.settings.reportTemplates.standard')}</SelectItem>
                    <SelectItem value="legal">{t('automation.settings.reportTemplates.legal')}</SelectItem>
                    <SelectItem value="summary">{t('automation.settings.reportTemplates.summary')}</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Save Button */}
            <div className="flex justify-end pt-4 border-t border-border">
              <Button
                onClick={() => local && saveMutation.mutate(local)}
                disabled={disabled}
                aria-busy={saveMutation.isPending}
                className="bg-gradient-to-r from-primary-600 to-purple-600 hover:from-primary-700 hover:to-purple-700 text-white shadow-lg shadow-primary-500/50 dark:shadow-primary-500/30 px-6 py-2 font-semibold transition-all hover:scale-105"
              >
                {saveMutation.isPending ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    {t('automation.settings.saving')}
                  </>
                ) : (
                  <>
                    <Save className="w-4 h-4 mr-2" />
                    {t('automation.settings.save')}
                  </>
                )}
              </Button>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Simulation Card */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
      >
        <Card className="border border-border shadow-xl shadow-slate-200/50 dark:shadow-slate-900/50 hover:shadow-2xl transition-shadow duration-300">
          <CardHeader className="bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-950/30 dark:to-purple-950/30 border-b border-border">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-blue-100 dark:bg-blue-900/30">
                <Activity className="w-5 h-5 text-blue-600 dark:text-blue-400" />
              </div>
              <div>
                <CardTitle className="text-xl font-bold text-slate-900 dark:text-slate-100">
                  {t('automation.simulation.title')}
                </CardTitle>
                <CardDescription className="text-slate-600 dark:text-slate-400">
                  {t('automation.simulation.description')}
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-6 p-6">
            <div className="flex flex-wrap gap-4 items-end">
              <div className="flex-1 min-w-[200px] space-y-2">
                <Label htmlFor="hours" className="text-sm font-semibold text-slate-900 dark:text-slate-100">
                  {t('automation.simulation.hours')}
                </Label>
                <Input 
                  id="hours" 
                  type="number" 
                  min={1} 
                  max={168} 
                  defaultValue={24} 
                  className="bg-white dark:bg-slate-900 border-slate-300 dark:border-slate-700 focus:border-primary-500 focus:ring-primary-500"
                  aria-label={t('automation.simulation.hours')} 
                />
              </div>
              <div className="flex-1 min-w-[200px] space-y-2">
                <Label htmlFor="sample" className="text-sm font-semibold text-slate-900 dark:text-slate-100">
                  {t('automation.simulation.sample')}
                </Label>
                <Input 
                  id="sample" 
                  type="number" 
                  min={1} 
                  max={1000} 
                  defaultValue={100} 
                  className="bg-white dark:bg-slate-900 border-slate-300 dark:border-slate-700 focus:border-primary-500 focus:ring-primary-500"
                  aria-label={t('automation.simulation.sample')} 
                />
              </div>
              <Button
                onClick={() => {
                  const hours = Number((document.getElementById('hours') as HTMLInputElement)?.value || 24);
                  const sample_size = Number((document.getElementById('sample') as HTMLInputElement)?.value || 100);
                  simulateMutation.mutate({ hours, sample_size });
                }}
                disabled={simulateMutation.isPending}
                aria-busy={simulateMutation.isPending}
                className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white shadow-lg shadow-blue-500/50 dark:shadow-blue-500/30 px-6 font-semibold transition-all hover:scale-105"
              >
                {simulateMutation.isPending ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    {t('automation.simulation.simulating')}
                  </>
                ) : (
                  <>
                    <PlayCircle className="w-4 h-4 mr-2" />
                    {t('automation.simulation.simulate')}
                  </>
                )}
              </Button>
            </div>

            {simulateMutation.data && (
              <motion.div 
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="grid grid-cols-2 md:grid-cols-4 gap-4" 
                role="status" 
                aria-live="polite"
              >
                <Stat 
                  label={t('automation.simulation.results.evaluated')} 
                  value={simulateMutation.data.evaluated}
                  icon={<Activity className="w-5 h-5 text-blue-600 dark:text-blue-400" />}
                  gradientClass="bg-gradient-to-br from-blue-50 to-cyan-50 dark:from-blue-950/30 dark:to-cyan-950/30"
                />
                <Stat 
                  label={t('automation.simulation.results.createCases')} 
                  value={simulateMutation.data.would_create_cases}
                  icon={<CheckCircle2 className="w-5 h-5 text-green-600 dark:text-green-400" />}
                  gradientClass="bg-gradient-to-br from-green-50 to-emerald-50 dark:from-green-950/30 dark:to-emerald-950/30"
                />
                <Stat 
                  label={t('automation.simulation.results.triggerTraces')} 
                  value={simulateMutation.data.would_trigger_traces}
                  icon={<Sparkles className="w-5 h-5 text-purple-600 dark:text-purple-400" />}
                  gradientClass="bg-gradient-to-br from-purple-50 to-pink-50 dark:from-purple-950/30 dark:to-pink-950/30"
                />
                <Stat 
                  label={t('automation.simulation.results.highPriority')} 
                  value={simulateMutation.data.high_priority}
                  icon={<AlertCircle className="w-5 h-5 text-orange-600 dark:text-orange-400" />}
                  gradientClass="bg-gradient-to-br from-orange-50 to-red-50 dark:from-orange-950/30 dark:to-red-950/30"
                />
              </motion.div>
            )}
          </CardContent>
        </Card>
      </motion.div>

      {/* Recent Jobs Card */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
      >
        <Card className="border border-border shadow-xl shadow-slate-200/50 dark:shadow-slate-900/50 hover:shadow-2xl transition-shadow duration-300">
          <CardHeader className="bg-gradient-to-r from-indigo-50 to-blue-50 dark:from-indigo-950/30 dark:to-blue-950/30 border-b border-border">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-indigo-100 dark:bg-indigo-900/30">
                <Clock className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
              </div>
              <div>
                <CardTitle className="text-xl font-bold text-slate-900 dark:text-slate-100">
                  {t('automation.recent.title')}
                </CardTitle>
                <CardDescription className="text-slate-600 dark:text-slate-400">
                  {t('automation.recent.description')}
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="p-6">
            {recent?.items?.length ? (
              <div role="list" aria-label="Recent Jobs" className="space-y-3">
                {recent.items.map((j, i) => (
                  <motion.div 
                    key={`${j.address}-${i}`}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.05 }}
                    role="listitem" 
                    className="group p-4 rounded-xl bg-muted border border-border hover:border-primary-300 dark:hover:border-primary-700 transition-all hover:shadow-lg"
                  >
                    <div className="flex items-center justify-between gap-4">
                      <div className="flex-1 min-w-0">
                        <div className="font-mono text-sm font-semibold text-slate-900 dark:text-slate-100 truncate">
                          {j.address}
                        </div>
                        <div className="text-xs text-slate-600 dark:text-slate-400 mt-1 flex items-center gap-2">
                          <span className="inline-flex items-center gap-1">
                            <span className="font-semibold">{t('automation.recent.chain')}:</span> {j.chain}
                          </span>
                          <span className="text-slate-400 dark:text-slate-600">·</span>
                          <span className="inline-flex items-center gap-1">
                            <span className="font-semibold">{t('automation.recent.depth')}:</span> {j.depth}
                          </span>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
                          j.status === 'done' 
                            ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' 
                            : j.status === 'queued' 
                            ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400' 
                            : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
                        }`}>
                          {j.status === 'done' ? t('automation.recent.status.done') : j.status === 'queued' ? t('automation.recent.status.queued') : t('automation.recent.status.failed')}
                        </span>
                        {j.error && (
                          <span className="ml-2 text-xs text-red-600 dark:text-red-400 max-w-[200px] truncate" title={j.error}>
                            {j.error}
                          </span>
                        )}
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12">
                <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-slate-100 dark:bg-slate-900 mb-4">
                  <Clock className="w-8 h-8 text-slate-400 dark:text-slate-600" />
                </div>
                <p className="text-sm font-medium text-slate-600 dark:text-slate-400">{t('automation.recent.noJobs')}</p>
              </div>
            )}
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
}

function Stat({ label, value, icon, gradientClass }: { label: string; value: number; icon?: React.ReactNode; gradientClass?: string }) {
  return (
    <motion.div 
      whileHover={{ scale: 1.05, y: -5 }}
      className={`relative overflow-hidden p-6 rounded-xl border border-slate-200 dark:border-slate-800 ${gradientClass || 'bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900/50 dark:to-slate-800/50'} shadow-lg hover:shadow-xl transition-all`}
    >
      {icon && (
        <div className="absolute top-2 right-2 opacity-20">
          {icon}
        </div>
      )}
      <div className="relative z-10">
        <div className="text-xs font-semibold text-slate-600 dark:text-slate-300 uppercase tracking-wide mb-2">{label}</div>
        <div className="text-3xl font-bold bg-gradient-to-br from-slate-900 to-slate-700 dark:from-slate-100 dark:to-slate-300 bg-clip-text text-transparent" aria-label={`${label}: ${value}`}>
          {value}
        </div>
      </div>
      {/* Animated gradient overlay */}
      <div className="absolute inset-0 bg-gradient-to-t from-white/50 to-transparent dark:from-slate-950/50 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none" />
    </motion.div>
  );
}
