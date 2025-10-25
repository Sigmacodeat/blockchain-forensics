import React from 'react';
import { useTranslation } from 'react-i18next';
import { RiskCopilot } from '@/components/RiskCopilot';
import { GraphNode, GraphControls } from './types';

interface NodeDetailsPanelProps {
  selectedAddress: string;
  node: GraphNode;
  graphControls: GraphControls | null;
  onPatternDetect: () => void;
  onAiTracePath: () => void;
  onAiMonitor: () => void;
  onFindPath: (targetAddress: string) => void;
  patternsPending: boolean;
}

export const NodeDetailsPanel: React.FC<NodeDetailsPanelProps> = ({
  selectedAddress,
  node,
  graphControls,
  onPatternDetect,
  onAiTracePath,
  onAiMonitor,
  onFindPath,
  patternsPending,
}) => {
  const { t } = useTranslation();

  return (
    <div className="bg-white dark:bg-slate-800 p-6 rounded-xl shadow-lg border border-slate-200 dark:border-slate-700">
      <div className="mb-4">
        <h3 className="text-base font-semibold text-slate-900 dark:text-white mb-2">Node Details</h3>
        <div className="p-3 bg-slate-50 dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-700">
          <code className="block text-xs font-mono text-slate-700 dark:text-slate-300 break-all">
            {selectedAddress}
          </code>
        </div>
      </div>

      <div className="flex flex-wrap gap-2 mb-4">
        <button
          className="px-3 py-1.5 text-xs rounded-lg bg-slate-100 dark:bg-slate-700 hover:bg-slate-200 dark:hover:bg-slate-600 text-slate-700 dark:text-slate-200 font-medium transition-colors"
          onClick={() => navigator.clipboard?.writeText(selectedAddress)}
        >
          Copy
        </button>
        <button
          className="px-3 py-1.5 text-xs rounded-lg bg-slate-100 dark:bg-slate-700 hover:bg-slate-200 dark:hover:bg-slate-600 text-slate-700 dark:text-slate-200 font-medium transition-colors"
          onClick={() => graphControls?.centerOn(selectedAddress)}
        >
          Center
        </button>
        <button
          className="px-3 py-1.5 text-xs rounded-lg bg-blue-600 dark:bg-blue-500 text-white hover:bg-blue-700 dark:hover:bg-blue-600 disabled:opacity-50 font-medium transition-colors shadow-sm"
          onClick={onPatternDetect}
          disabled={patternsPending}
          title="Detect patterns for this address"
        >
          {patternsPending ? 'Detecting…' : 'Patterns'}
        </button>
        <button
          className="px-3 py-1.5 text-xs rounded-lg bg-purple-600 dark:bg-purple-500 text-white hover:bg-purple-700 dark:hover:bg-purple-600 font-medium transition-colors shadow-sm"
          onClick={onAiTracePath}
          title="AI Trace Path"
        >
          AI Trace
        </button>
        <button
          className="px-3 py-1.5 text-xs rounded-lg bg-amber-600 dark:bg-amber-500 text-white hover:bg-amber-700 dark:hover:bg-amber-600 font-medium transition-colors shadow-sm"
          onClick={onAiMonitor}
          title="AI Monitor & Alerts"
        >
          Monitor
        </button>
      </div>

      <div className="grid grid-cols-1 gap-3 text-sm">
        <div className="p-3 bg-slate-50 dark:bg-slate-900 rounded-lg">
          <div className="text-slate-500 dark:text-slate-400 text-xs mb-1">Chain</div>
          <div className="font-semibold text-slate-900 dark:text-white">{node.chain || '—'}</div>
        </div>
        <div className="p-3 bg-slate-50 dark:bg-slate-900 rounded-lg">
          <div className="text-slate-500 dark:text-slate-400 text-xs mb-1">Risk Level</div>
          <div className="flex items-center gap-2">
            <span
              className={`px-2 py-0.5 rounded text-xs font-semibold ${
                node.risk_level === 'CRITICAL'
                  ? 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400'
                  : node.risk_level === 'HIGH'
                  ? 'bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-400'
                  : node.risk_level === 'MEDIUM'
                  ? 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400'
                  : 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400'
              }`}
            >
              {node.risk_level}
            </span>
            <span className="text-slate-600 dark:text-slate-400 text-xs">
              ({(node.taint_score * 100).toFixed(1)}%)
            </span>
          </div>
        </div>
        <div className="p-3 bg-slate-50 dark:bg-slate-900 rounded-lg">
          <div className="text-slate-500 dark:text-slate-400 text-xs mb-1">Transactions</div>
          <div className="font-semibold text-slate-900 dark:text-white">
            {node.tx_count.toLocaleString()}
          </div>
        </div>
      </div>

      {Array.isArray(node.labels) && node.labels.length > 0 && (
        <div className="mt-4">
          <div className="text-slate-500 dark:text-slate-400 text-xs mb-2">Labels</div>
          <div className="flex flex-wrap gap-2">
            {node.labels.slice(0, 6).map((label: string, i: number) => (
              <span
                key={i}
                className="text-xs px-2.5 py-1 rounded-md bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 font-medium border border-primary-200 dark:border-primary-800"
              >
                {label}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Risk Copilot Integration */}
      <div className="mt-4">
        <div className="text-slate-500 dark:text-slate-400 text-xs mb-2 font-medium">
          Live Risk Analysis
        </div>
        <RiskCopilot chain={node.chain || 'ethereum'} address={selectedAddress} variant="compact" className="w-full" />
      </div>

      {/* Find Path to target */}
      <div className="mt-4 flex items-center gap-2">
        <input
          type="text"
          placeholder="Target address (0x... or bc1...)"
          className="flex-1 px-3 py-2 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white text-sm focus:ring-2 focus:ring-primary-500 dark:focus:ring-primary-600 focus:border-transparent"
          onKeyDown={(e) => {
            const el = e.currentTarget as HTMLInputElement;
            if (e.key === 'Enter' && el.value.trim()) {
              onFindPath(el.value.trim());
            }
          }}
        />
        <button
          className="px-3 py-2 rounded-lg bg-primary-600 dark:bg-primary-500 text-white hover:bg-primary-700 dark:hover:bg-primary-600 text-sm font-medium transition-colors shadow-sm"
          onClick={(e) => {
            const container = e.currentTarget.parentElement?.querySelector('input') as HTMLInputElement | null;
            const val = container?.value?.trim();
            if (val) onFindPath(val);
          }}
        >
          Find Path
        </button>
      </div>
    </div>
  );
};
