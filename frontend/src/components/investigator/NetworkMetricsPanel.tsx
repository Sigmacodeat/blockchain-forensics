import React from 'react';
import { TrendingUp } from 'lucide-react';
import { GraphControls } from './types';

interface NetworkMetricsProps {
  density: number;
  nodeCount: number;
  linkCount: number;
  highRiskNodes: Array<{ address: string; risk: string; taint: number }>;
  onSelectAddress: (address: string) => void;
  graphControls: GraphControls | null;
}

export const NetworkMetricsPanel: React.FC<NetworkMetricsProps> = ({
  density,
  nodeCount,
  linkCount,
  highRiskNodes,
  onSelectAddress,
  graphControls,
}) => {
  return (
    <div className="bg-white dark:bg-slate-800 p-6 rounded-xl shadow-lg border border-slate-200 dark:border-slate-700">
      <h3 className="text-base font-semibold mb-4 flex items-center gap-2 text-slate-900 dark:text-white">
        <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
          <TrendingUp className="h-4 w-4 text-blue-600 dark:text-blue-400" />
        </div>
        Network Metrics
      </h3>
      <div className="space-y-3">
        <div className="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-900 rounded-lg">
          <span className="text-xs text-slate-600 dark:text-slate-400">Density</span>
          <span className="text-sm font-semibold text-slate-900 dark:text-white">{density.toFixed(2)}%</span>
        </div>
        {highRiskNodes.length > 0 && (
          <div>
            <div className="text-xs text-slate-500 dark:text-slate-400 mb-2 font-medium">
              Top High-Risk Nodes:
            </div>
            <div className="space-y-1.5">
              {highRiskNodes.map((node, idx) => (
                <button
                  key={idx}
                  className="w-full text-left p-2 bg-red-50 dark:bg-red-900/20 hover:bg-red-100 dark:hover:bg-red-900/30 border border-red-200 dark:border-red-800 rounded-lg transition-colors"
                  onClick={() => {
                    onSelectAddress(node.address);
                    graphControls?.centerOn(node.address);
                  }}
                >
                  <div className="flex items-center justify-between">
                    <code className="text-xs font-mono text-slate-900 dark:text-white">
                      {node.address.slice(0, 10)}...
                    </code>
                    <span className="text-xs font-semibold text-red-600 dark:text-red-400">
                      {(node.taint * 100).toFixed(0)}%
                    </span>
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
