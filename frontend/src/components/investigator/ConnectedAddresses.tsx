import React from 'react';
import { useTranslation } from 'react-i18next';
import { Users } from 'lucide-react';
import { LocalGraph, GraphControls } from './types';

interface ConnectedAddressesProps {
  filteredGraph: LocalGraph;
  selectedAddress: string;
  highlightedPath?: string[];
  onSelectAddress: (address: string) => void;
  onFindPath: (address: string) => void;
  onExpandNeighbors: (address: string) => void;
  graphControls: GraphControls | null;
}

export const ConnectedAddresses: React.FC<ConnectedAddressesProps> = ({
  filteredGraph,
  selectedAddress,
  highlightedPath,
  onSelectAddress,
  onFindPath,
  onExpandNeighbors,
  graphControls,
}) => {
  const { t } = useTranslation();

  if (!filteredGraph?.nodes || Object.keys(filteredGraph.nodes).length <= 1) {
    return null;
  }

  return (
    <div className="bg-white dark:bg-slate-800 p-6 rounded-xl shadow-lg border border-slate-200 dark:border-slate-700">
      <h3 className="text-lg font-semibold mb-4 flex items-center gap-2 text-slate-900 dark:text-white">
        <Users className="h-5 w-5 text-primary-600 dark:text-primary-400" />
        {t('investigator.connected.title', 'Connected Addresses')}{' '}
        <span className="text-sm font-normal text-slate-500 dark:text-slate-400">
          ({Object.keys(filteredGraph.nodes).length - 1})
        </span>
      </h3>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {Object.entries(filteredGraph.nodes)
          .filter(([addr]) => addr !== selectedAddress)
          .slice(0, 10)
          .map(([address, node]: [string, any]) => (
            <div
              key={address}
              className={`p-4 rounded-lg cursor-pointer transition-all hover:shadow-md ${
                node.risk_level === 'HIGH' || node.risk_level === 'CRITICAL'
                  ? 'border-2 border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/20 hover:bg-red-100 dark:hover:bg-red-900/30'
                  : 'border-2 border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 hover:bg-slate-100 dark:hover:bg-slate-800'
              }`}
              onClick={() => {
                onSelectAddress(address);
                graphControls?.centerOn(address);
              }}
            >
              <div className="flex justify-between items-start mb-3">
                <code className="text-xs font-mono text-slate-700 dark:text-slate-300 font-semibold">
                  {address.slice(0, 10)}...{address.slice(-8)}
                </code>
                <span
                  className={`text-xs px-2 py-1 rounded-md font-semibold ${
                    node.risk_level === 'HIGH' || node.risk_level === 'CRITICAL'
                      ? 'bg-red-100 dark:bg-red-900/40 text-red-700 dark:text-red-400'
                      : node.risk_level === 'MEDIUM'
                      ? 'bg-yellow-100 dark:bg-yellow-900/40 text-yellow-700 dark:text-yellow-400'
                      : 'bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-400'
                  }`}
                >
                  {node.risk_level}
                </span>
              </div>
              <div className="flex items-center gap-3 text-xs text-slate-600 dark:text-slate-400 mb-3">
                <span>
                  <span className="font-medium">{t('investigator.connected.taint', 'Taint')}:</span>{' '}
                  {(node.taint_score * 100).toFixed(1)}%
                </span>
                <span>•</span>
                <span>
                  <span className="font-medium">{t('investigator.connected.tx', 'Tx')}:</span>{' '}
                  {node.tx_count.toLocaleString()}
                </span>
              </div>
              {node.labels?.length > 0 && (
                <div className="flex gap-1.5 mb-3 flex-wrap">
                  {node.labels.slice(0, 2).map((label: string, i: number) => (
                    <span
                      key={i}
                      className="text-xs px-2 py-0.5 bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 rounded-md font-medium border border-primary-200 dark:border-primary-800"
                    >
                      {label}
                    </span>
                  ))}
                </div>
              )}
              <div className="flex gap-2">
                <button
                  className="text-xs px-3 py-1.5 rounded-lg bg-primary-600 dark:bg-primary-500 text-white hover:bg-primary-700 dark:hover:bg-primary-600 font-medium transition-colors shadow-sm"
                  onClick={(e) => {
                    e.stopPropagation();
                    onFindPath(address);
                  }}
                  disabled={!selectedAddress}
                  title="Find path from current selected address"
                >
                  Find Path
                </button>
                <button
                  className="text-xs px-3 py-1.5 rounded-lg bg-slate-100 dark:bg-slate-700 hover:bg-slate-200 dark:hover:bg-slate-600 text-slate-700 dark:text-slate-200 font-medium transition-colors"
                  onClick={(e) => {
                    e.stopPropagation();
                    onExpandNeighbors(address);
                    onSelectAddress(address);
                    graphControls?.centerOn(address);
                  }}
                  title="Expand neighbors"
                >
                  Expand
                </button>
                {highlightedPath && highlightedPath.includes(address) && (
                  <span className="text-xs px-2 py-1 rounded-md bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 font-semibold border border-blue-200 dark:border-blue-800">
                    On Path
                  </span>
                )}
              </div>
            </div>
          ))}
      </div>
    </div>
  );
};
