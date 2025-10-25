import React from 'react';
import { useTranslation } from 'react-i18next';
import { AlertTriangle } from 'lucide-react';

interface PatternFinding {
  pattern: string;
  score: number;
  explanation: string;
  evidence?: Array<{
    tx_hash: string;
    amount: number;
    timestamp: string;
  }>;
}

interface PatternFindingsProps {
  findings: PatternFinding[];
  onOpenTx: (txHash: string, chain?: string) => void;
}

export const PatternFindings: React.FC<PatternFindingsProps> = ({ findings, onOpenTx }) => {
  const { t } = useTranslation();

  return (
    <div className="bg-white dark:bg-slate-800 p-5 rounded-xl shadow-lg border border-slate-200 dark:border-slate-700">
      <div className="flex items-center justify-between mb-4">
        <h4 className="text-base font-semibold text-slate-900 dark:text-white flex items-center gap-2">
          <AlertTriangle className="h-4 w-4 text-amber-600 dark:text-amber-400" />
          Detected Patterns
        </h4>
        <div className="text-xs text-slate-600 dark:text-slate-400 flex items-center gap-3">
          <span className="inline-flex items-center gap-1.5">
            <span className="inline-block w-3 h-3 rounded-full bg-red-500 dark:bg-red-400" /> Critical
          </span>
          <span className="inline-flex items-center gap-1.5">
            <span className="inline-block w-3 h-3 rounded-full bg-yellow-500 dark:bg-yellow-400" /> Medium
          </span>
          <span className="inline-flex items-center gap-1.5">
            <span className="inline-block w-3 h-3 rounded-full bg-green-500 dark:bg-green-400" /> Low
          </span>
        </div>
      </div>
      <div className="space-y-3">
        {findings.map((f: PatternFinding, i: number) => {
          const scoreValue = f.score * 100;
          const isCritical = scoreValue >= 80;
          const isMedium = scoreValue >= 60 && scoreValue < 80;
          return (
            <div
              key={i}
              className={`border-2 rounded-lg p-4 ${
                isCritical
                  ? 'border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/20'
                  : isMedium
                  ? 'border-yellow-200 dark:border-yellow-800 bg-yellow-50 dark:bg-yellow-900/20'
                  : 'border-green-200 dark:border-green-800 bg-green-50 dark:bg-green-900/20'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <div className="text-sm font-semibold text-slate-900 dark:text-white">{f.pattern}</div>
                <div
                  className={`px-2.5 py-1 rounded-lg text-xs font-semibold ${
                    isCritical
                      ? 'bg-red-100 dark:bg-red-900/40 text-red-700 dark:text-red-400'
                      : isMedium
                      ? 'bg-yellow-100 dark:bg-yellow-900/40 text-yellow-700 dark:text-yellow-400'
                      : 'bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-400'
                  }`}
                >
                  Score: {scoreValue.toFixed(0)}%
                </div>
              </div>
              <div className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed">{f.explanation}</div>
              {Array.isArray(f.evidence) && f.evidence.length > 0 && (
                <div className="mt-3 p-3 bg-slate-50 dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-700">
                  <div className="text-xs font-semibold text-slate-700 dark:text-slate-300 mb-2">
                    Evidence (Top 5):
                  </div>
                  <div className="max-h-48 overflow-y-auto scrollbar-thin scrollbar-thumb-slate-300 dark:scrollbar-thumb-slate-600">
                    <div className="space-y-2">
                      {f.evidence.slice(0, 5).map((e: any, j: number) => (
                        <div
                          key={j}
                          className="p-2 bg-white dark:bg-slate-800 rounded border border-slate-200 dark:border-slate-700"
                        >
                          <div className="grid grid-cols-2 gap-2 text-xs mb-2">
                            <div>
                              <span className="text-slate-500 dark:text-slate-400">Tx:</span>
                              <code className="ml-1 text-slate-900 dark:text-white font-mono">
                                {e.tx_hash?.slice(0, 10)}…
                              </code>
                            </div>
                            <div>
                              <span className="text-slate-500 dark:text-slate-400">Amount:</span>
                              <span className="ml-1 text-slate-900 dark:text-white font-semibold">
                                {Number(e.amount ?? 0).toFixed(4)}
                              </span>
                            </div>
                          </div>
                          <div className="flex items-center justify-between text-xs">
                            <span className="text-slate-500 dark:text-slate-400">{e.timestamp}</span>
                            <button
                              className="px-2 py-1 rounded-lg bg-slate-100 dark:bg-slate-700 hover:bg-slate-200 dark:hover:bg-slate-600 text-slate-700 dark:text-slate-200 font-medium transition-colors"
                              onClick={() => onOpenTx(e.tx_hash)}
                              aria-label={`Open ${e.tx_hash} in explorer`}
                            >
                              Explorer →
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
