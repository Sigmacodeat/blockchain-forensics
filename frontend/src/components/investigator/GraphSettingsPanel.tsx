import React from 'react';
import { useTranslation } from 'react-i18next';
import { Filter } from 'lucide-react';

interface GraphSettingsPanelProps {
  maxHops: number;
  onMaxHopsChange: (value: number) => void;
  includeBridges: boolean;
  onIncludeBridgesChange: (value: boolean) => void;
  timeRange: { from: string; to: string };
  onTimeRangeChange: (range: { from: string; to: string }) => void;
  minTaint: number;
  onMinTaintChange: (value: number) => void;
  pathRiskThreshold: number;
  onPathRiskThresholdChange: (value: number) => void;
  pathMinAmount: number;
  onPathMinAmountChange: (value: number) => void;
  pathTimeWindowDays: number;
  onPathTimeWindowDaysChange: (value: number) => void;
  pathAlgorithm: 'astar' | 'bidirectional';
  onPathAlgorithmChange: (value: 'astar' | 'bidirectional') => void;
}

export const GraphSettingsPanel: React.FC<GraphSettingsPanelProps> = ({
  maxHops,
  onMaxHopsChange,
  includeBridges,
  onIncludeBridgesChange,
  timeRange,
  onTimeRangeChange,
  minTaint,
  onMinTaintChange,
  pathRiskThreshold,
  onPathRiskThresholdChange,
  pathMinAmount,
  onPathMinAmountChange,
  pathTimeWindowDays,
  onPathTimeWindowDaysChange,
  pathAlgorithm,
  onPathAlgorithmChange,
}) => {
  const { t } = useTranslation();

  return (
    <div className="bg-white dark:bg-slate-800 p-6 rounded-xl shadow-lg border border-slate-200 dark:border-slate-700">
      <h3 className="text-base font-semibold mb-4 flex items-center gap-2 text-slate-900 dark:text-white">
        <div className="p-2 bg-emerald-100 dark:bg-emerald-900/30 rounded-lg">
          <Filter className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
        </div>
        {t('investigator.settings.title', 'Graph Settings')}
      </h3>
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
            {t('investigator.settings.max_hops', 'Max Hops')}
          </label>
          <select
            value={maxHops}
            onChange={(e) => onMaxHopsChange(parseInt(e.target.value))}
            className="w-full px-4 py-2.5 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white focus:ring-2 focus:ring-primary-500 dark:focus:ring-primary-600 focus:border-transparent transition-all"
          >
            <option value={1}>{t('investigator.settings.hops_1', '1 Hop')}</option>
            <option value={2}>{t('investigator.settings.hops_2', '2 Hops')}</option>
            <option value={3}>{t('investigator.settings.hops_3', '3 Hops')}</option>
            <option value={4}>{t('investigator.settings.hops_4', '4 Hops')}</option>
            <option value={5}>{t('investigator.settings.hops_5', '5 Hops')}</option>
          </select>
        </div>

        <label className="flex items-center gap-3 p-3 bg-slate-50 dark:bg-slate-900 rounded-lg cursor-pointer hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors">
          <input
            type="checkbox"
            checked={includeBridges}
            onChange={(e) => onIncludeBridgesChange(e.target.checked)}
            className="w-4 h-4 text-primary-600 bg-slate-100 border-slate-300 rounded focus:ring-primary-500 dark:focus:ring-primary-600 dark:bg-slate-700 dark:border-slate-600"
          />
          <span className="text-sm text-slate-700 dark:text-slate-300 font-medium">
            {t('investigator.settings.include_bridges', 'Include Cross-Chain Bridges')}
          </span>
        </label>

        <div className="space-y-2">
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">Time Range</label>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs text-slate-500 dark:text-slate-400 mb-1">
                {t('investigator.settings.from', 'From')}
              </label>
              <input
                type="datetime-local"
                className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white text-sm focus:ring-2 focus:ring-primary-500 dark:focus:ring-primary-600 focus:border-transparent"
                value={timeRange.from}
                onChange={(e) => onTimeRangeChange({ ...timeRange, from: e.target.value })}
              />
            </div>
            <div>
              <label className="block text-xs text-slate-500 dark:text-slate-400 mb-1">
                {t('investigator.settings.to', 'To')}
              </label>
              <input
                type="datetime-local"
                className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white text-sm focus:ring-2 focus:ring-primary-500 dark:focus:ring-primary-600 focus:border-transparent"
                value={timeRange.to}
                onChange={(e) => onTimeRangeChange({ ...timeRange, to: e.target.value })}
              />
            </div>
          </div>
        </div>

        {/* Min Risk Filter (taint %) */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="text-sm font-medium text-slate-700 dark:text-slate-300">
              {t('investigator.settings.min_risk', 'Min Taint (%)')}
            </label>
            <span className="px-2.5 py-1 bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 rounded-lg text-sm font-semibold">
              {minTaint}%
            </span>
          </div>
          <input
            type="range"
            min={0}
            max={100}
            step={1}
            value={minTaint}
            onChange={(e) => onMinTaintChange(parseInt(e.target.value))}
            className="w-full h-2 bg-slate-200 dark:bg-slate-700 rounded-lg appearance-none cursor-pointer accent-primary-600 dark:accent-primary-500"
            aria-label="Minimum Taint Percentage"
          />
          <div className="flex justify-between text-xs text-slate-500 dark:text-slate-400 mt-1">
            <span>0%</span>
            <span>50%</span>
            <span>100%</span>
          </div>
        </div>

        <div className="pt-4 border-t border-slate-200 dark:border-slate-700">
          <h4 className="text-sm font-semibold text-slate-800 dark:text-slate-200 mb-3">
            {t('investigator.settings.path_constraints', 'Path Constraints')}
          </h4>

          <div className="space-y-4">
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-sm font-medium text-slate-700 dark:text-slate-300">
                  {t('investigator.settings.path_risk_threshold', 'Max Risk Score (%)')}
                </label>
                <span className="px-2.5 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded-lg text-sm font-semibold">
                  {pathRiskThreshold}%
                </span>
              </div>
              <input
                type="range"
                min={0}
                max={100}
                step={1}
                value={pathRiskThreshold}
                onChange={(e) => onPathRiskThresholdChange(parseInt(e.target.value))}
                className="w-full h-2 bg-slate-200 dark:bg-slate-700 rounded-lg appearance-none cursor-pointer accent-blue-600 dark:accent-blue-500"
                aria-label="Maximum Risk Threshold"
              />
              <div className="flex justify-between text-xs text-slate-500 dark:text-slate-400 mt-1">
                <span>0%</span>
                <span>50%</span>
                <span>100%</span>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                {t('investigator.settings.path_min_amount', 'Minimum Amount (native units)')}
              </label>
              <input
                type="number"
                min={0}
                step="0.0001"
                value={pathMinAmount}
                onChange={(e) => onPathMinAmountChange(parseFloat(e.target.value) || 0)}
                className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white text-sm focus:ring-2 focus:ring-primary-500 dark:focus:ring-primary-600 focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                {t('investigator.settings.path_time_window', 'Time Window (Days)')}
              </label>
              <input
                type="number"
                min={1}
                max={3650}
                value={pathTimeWindowDays}
                onChange={(e) => onPathTimeWindowDaysChange(Math.max(1, Math.min(3650, parseInt(e.target.value) || 1)))}
                className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white text-sm focus:ring-2 focus:ring-primary-500 dark:focus:ring-primary-600 focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                {t('investigator.settings.path_algorithm', 'Pathfinding Algorithm')}
              </label>
              <select
                value={pathAlgorithm}
                onChange={(e) => onPathAlgorithmChange(e.target.value as 'astar' | 'bidirectional')}
                className="w-full px-4 py-2.5 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white focus:ring-2 focus:ring-primary-500 dark:focus:ring-primary-600 focus:border-transparent transition-all"
              >
                <option value="astar">{t('investigator.settings.path_algorithm_astar', 'A* Search')}</option>
                <option value="bidirectional">{t('investigator.settings.path_algorithm_bidirectional', 'Bidirectional Search')}</option>
              </select>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
