import React from 'react';
import { useTranslation } from 'react-i18next';
import { Route } from 'lucide-react';

interface PathSummary {
  source: string;
  target: string;
  hops: number;
  totalAmount: number;
  maxRiskPercent: number;
  bridges: string[];
  executionTimeMs?: number;
  totalPathsFound?: number;
  algorithm?: string;
}

type RawPathStep = {
  from_address: string;
  to_address: string;
  amount?: number;
  risk_score?: number;
  tx_hash?: string;
  timestamp?: string;
  from_chain?: string;
  to_chain?: string;
};

type RawPath = {
  path?: RawPathStep[];
  total_cost?: number;
  hops?: number;
  meeting_point?: string;
};

interface PathResultsProps {
  summary: PathSummary;
  rawPaths?: RawPath[];
  isLoading: boolean;
}

export const PathResults: React.FC<PathResultsProps> = ({ summary, rawPaths, isLoading }) => {
  const { t } = useTranslation();

  return (
    <div className="bg-white dark:bg-slate-800 p-6 rounded-xl shadow-lg border border-slate-200 dark:border-slate-700">
      <h3 className="text-base font-semibold mb-4 flex items-center gap-2 text-slate-900 dark:text-white">
        <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
          <Route className="h-4 w-4 text-blue-600 dark:text-blue-400" />
        </div>
        {t('investigator.path.title', 'Path Results')}
      </h3>
      <div className="space-y-3">
        <div className="grid grid-cols-2 gap-3">
          <div className="p-3 bg-slate-50 dark:bg-slate-900 rounded-lg">
            <div className="text-xs text-slate-500 dark:text-slate-400 mb-1">
              {t('investigator.path.source', 'Source')}
            </div>
            <div className="text-xs font-medium break-all text-slate-900 dark:text-white">{summary.source}</div>
          </div>
          <div className="p-3 bg-slate-50 dark:bg-slate-900 rounded-lg">
            <div className="text-xs text-slate-500 dark:text-slate-400 mb-1">
              {t('investigator.path.target', 'Target')}
            </div>
            <div className="text-xs font-medium break-all text-slate-900 dark:text-white">{summary.target}</div>
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          <div className="p-3 bg-slate-50 dark:bg-slate-900 rounded-lg">
            <div className="text-xs text-slate-500 dark:text-slate-400 mb-1">
              {t('investigator.path.hops', 'Hops')}
            </div>
            <div className="text-sm font-semibold text-slate-900 dark:text-white">{summary.hops}</div>
          </div>
          <div className="p-3 bg-slate-50 dark:bg-slate-900 rounded-lg">
            <div className="text-xs text-slate-500 dark:text-slate-400 mb-1">
              {t('investigator.path.total_value', 'Total Value')}
            </div>
            <div className="text-sm font-semibold text-slate-900 dark:text-white">
              {summary.totalAmount.toLocaleString(undefined, { maximumFractionDigits: 4 })}
            </div>
          </div>
          <div className="p-3 bg-slate-50 dark:bg-slate-900 rounded-lg">
            <div className="text-xs text-slate-500 dark:text-slate-400 mb-1">
              {t('investigator.path.risk_score', 'Risk Score (max)')}
            </div>
            <div className="flex items-center gap-2">
              <span
                className={`px-2 py-0.5 rounded text-xs font-semibold ${
                  summary.maxRiskPercent >= 70
                    ? 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400'
                    : summary.maxRiskPercent >= 40
                    ? 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400'
                    : 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400'
                }`}
              >
                {summary.maxRiskPercent}%
              </span>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          <div className="p-3 bg-slate-50 dark:bg-slate-900 rounded-lg">
            <div className="text-xs text-slate-500 dark:text-slate-400 mb-1">
              {t('investigator.path.algorithm', 'Algorithm')}
            </div>
            <div className="text-sm font-semibold text-slate-900 dark:text-white">
              {(summary.algorithm || 'astar').toUpperCase()}
            </div>
          </div>
          <div className="p-3 bg-slate-50 dark:bg-slate-900 rounded-lg">
            <div className="text-xs text-slate-500 dark:text-slate-400 mb-1">
              {t('investigator.path.execution_time', 'Execution Time')}
            </div>
            <div className="text-sm font-semibold text-slate-900 dark:text-white">
              {summary.executionTimeMs ? `${summary.executionTimeMs.toFixed(0)} ms` : '—'}
            </div>
          </div>
          <div className="p-3 bg-slate-50 dark:bg-slate-900 rounded-lg">
            <div className="text-xs text-slate-500 dark:text-slate-400 mb-1">
              {t('investigator.path.paths_found', 'Paths Found')}
            </div>
            <div className="text-sm font-semibold text-slate-900 dark:text-white">
              {summary.totalPathsFound ?? 0}
            </div>
          </div>
        </div>

        {summary.bridges.length > 0 && (
          <div className="p-3 bg-slate-50 dark:bg-slate-900 rounded-lg">
            <div className="text-xs text-slate-500 dark:text-slate-400 mb-1">
              {t('investigator.path.bridges', 'Cross-Chain Bridges')}
            </div>
            <div className="text-sm font-semibold text-slate-900 dark:text-white">
              {summary.bridges.join(', ')}
            </div>
          </div>
        )}

        <div className="p-3 bg-slate-50 dark:bg-slate-900 rounded-lg">
          <div className="text-xs text-slate-500 dark:text-slate-400 mb-2 flex items-center justify-between">
            <span>{t('investigator.path.detailed_steps', 'Detailed Steps')}</span>
            {isLoading && (
              <span className="text-[10px] uppercase tracking-wide text-slate-400">
                {t('investigator.path.loading', 'Loading…')}
              </span>
            )}
          </div>

          {rawPaths && rawPaths.length > 0 ? (
            <div className="space-y-3">
              {rawPaths.slice(0, 3).map((path, idx) => (
                <div key={idx} className="rounded-lg border border-slate-200 dark:border-slate-700">
                  <div className="px-3 py-2 bg-slate-100 dark:bg-slate-800/60 text-xs font-semibold text-slate-600 dark:text-slate-300 flex items-center justify-between">
                    <span>
                      {t('investigator.path.variant', 'Variant')} #{idx + 1}{' '}
                      {path.hops ? `• ${path.hops} ${t('investigator.path.hops', 'Hops')}` : ''}
                    </span>
                    {path.total_cost !== undefined && (
                      <span>{t('investigator.path.total_cost', 'Total Cost')}: {path.total_cost.toFixed(2)}</span>
                    )}
                  </div>
                  <div className="px-3 py-2 text-xs text-slate-600 dark:text-slate-300 space-y-2">
                    {path.path?.map((step, stepIdx) => (
                      <div key={stepIdx} className="flex flex-col md:flex-row md:items-center md:justify-between gap-1">
                        <div className="font-medium break-all">
                          {step.from_address} → {step.to_address}
                        </div>
                        <div className="flex flex-wrap gap-2 text-[11px] uppercase tracking-wide">
                          <span className="px-2 py-0.5 rounded bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-200">
                            {step.from_chain?.toUpperCase()} → {step.to_chain?.toUpperCase()}
                          </span>
                          {step.amount !== undefined && (
                            <span className="px-2 py-0.5 rounded bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300">
                              {t('investigator.path.amount', 'Amount')}: {step.amount.toLocaleString(undefined, { maximumFractionDigits: 4 })}
                            </span>
                          )}
                          {step.risk_score !== undefined && (
                            <span className="px-2 py-0.5 rounded bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300">
                              {t('investigator.path.risk', 'Risk')}: {(step.risk_score * 100).toFixed(0)}%
                            </span>
                          )}
                          {step.tx_hash && (
                            <a
                              className="px-2 py-0.5 rounded bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 hover:underline"
                              href={`https://etherscan.io/tx/${step.tx_hash}`}
                              target="_blank"
                              rel="noreferrer"
                            >
                              TX
                            </a>
                          )}
                          {step.timestamp && (
                            <span className="px-2 py-0.5 rounded bg-slate-200 dark:bg-slate-700 text-slate-600 dark:text-slate-200">
                              {new Date(step.timestamp).toLocaleString()}
                            </span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-xs text-slate-500 dark:text-slate-400">
              {t('investigator.path.no_results', 'No detailed path data available.')}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
