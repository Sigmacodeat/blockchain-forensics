import React from 'react';
import { useRiskStream } from '@/hooks/useRiskStream';

export interface RiskCopilotProps {
  chain: string;
  address: string;
  className?: string;
  showDetails?: boolean;
  variant?: 'full' | 'compact' | 'badge';
}

function scoreToColor(score: number | null) {
  if (score === null) return 'bg-slate-400';
  if (score >= 0.8) return 'bg-red-600';
  if (score >= 0.6) return 'bg-orange-500';
  if (score >= 0.4) return 'bg-yellow-500';
  if (score >= 0.2) return 'bg-emerald-500';
  return 'bg-emerald-400';
}

export const RiskCopilot: React.FC<RiskCopilotProps> = ({ 
  chain, 
  address, 
  className, 
  showDetails = true,
  variant = 'full' 
}) => {
  const { connected, loading, error, score, categories, reasons, factors } = useRiskStream(chain, address);

  const roundedScore = score !== null ? Math.round(score * 100) : null;
  const color = scoreToColor(score);

  // Badge variant - ultra compact
  if (variant === 'badge') {
    return (
      <div className={`inline-flex items-center gap-1.5 px-2 py-1 rounded-md bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 ${className ?? ''}`}>
        <div className={`h-2 w-2 rounded-full ${color} ${loading ? 'animate-pulse' : ''}`} />
        <span className="text-xs font-medium text-slate-700 dark:text-slate-300">
          {roundedScore !== null ? roundedScore : '--'}
        </span>
      </div>
    );
  }

  // Compact variant - single line with minimal details
  if (variant === 'compact') {
    return (
      <div className={`flex items-center gap-3 px-3 py-2 rounded-md border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/50 ${className ?? ''}`}>
        <div className="flex items-center gap-2">
          <div className={`h-2.5 w-2.5 rounded-full ${color} ${loading ? 'animate-pulse' : ''}`} />
          <div className="flex items-baseline gap-1">
            <span className="text-lg font-semibold text-slate-900 dark:text-slate-100">
              {roundedScore !== null ? roundedScore : '--'}
            </span>
            <span className="text-xs text-slate-500">/100</span>
          </div>
        </div>
        {categories && categories.length > 0 && (
          <div className="flex gap-1">
            {categories.slice(0, 2).map((c) => (
              <span key={c} className="px-1.5 py-0.5 text-xs rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400">
                {c}
              </span>
            ))}
            {categories.length > 2 && (
              <span className="px-1.5 py-0.5 text-xs rounded bg-slate-100 dark:bg-slate-800 text-slate-500">
                +{categories.length - 2}
              </span>
            )}
          </div>
        )}
        {error && (
          <span className="text-xs text-red-600">⚠️</span>
        )}
      </div>
    );
  }

  // Full variant - complete details
  return (
    <div className={`rounded-md border border-slate-200 dark:border-slate-800 p-3 ${className ?? ''}`}>
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <div className={`h-3 w-3 rounded-full ${color} ${loading ? 'animate-pulse' : ''}`} />
          <div className="text-sm font-medium">Risk Copilot</div>
        </div>
        <div className="text-xs text-slate-500">
          {connected ? 'live' : 'init'}{loading ? ' • scoring…' : ''}
        </div>
      </div>

      <div className="mt-2 flex items-baseline gap-2">
        <div className="text-2xl font-semibold">
          {roundedScore !== null ? `${roundedScore}` : (
            <span className="text-slate-400">
              {loading ? <span className="animate-pulse">...</span> : '--'}
            </span>
          )}
          <span className="text-sm text-slate-500"> / 100</span>
        </div>
        {categories && categories.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {categories.map((c) => (
              <span key={c} className="px-2 py-0.5 text-xs rounded bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300">
                {c}
              </span>
            ))}
          </div>
        )}
      </div>

      {error && (
        <div className="mt-2 text-xs text-red-600 flex items-center gap-1">
          <span>⚠️</span>
          {error}
        </div>
      )}

      {showDetails && (
        <div className="mt-3 space-y-2">
          {reasons && reasons.length > 0 && (
            <div>
              <div className="text-xs font-medium text-slate-500 mb-1">Reasons</div>
              <ul className="list-disc pl-5 space-y-1">
                {reasons.map((r, idx) => (
                  <li key={idx} className="text-sm text-slate-700 dark:text-slate-200">{r}</li>
                ))}
              </ul>
            </div>
          )}
          {factors && Object.keys(factors).length > 0 && (
            <div>
              <div className="text-xs font-medium text-slate-500 mb-1">Factors</div>
              <div className="grid grid-cols-2 gap-2">
                {Object.entries(factors).map(([k, v]) => (
                  <div key={k} className="text-xs flex items-center justify-between rounded bg-slate-50 dark:bg-slate-900 px-2 py-1">
                    <span className="text-slate-600 dark:text-slate-400">{k}</span>
                    <span className="font-mono text-slate-800 dark:text-slate-200">{v.toFixed(2)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default RiskCopilot;
