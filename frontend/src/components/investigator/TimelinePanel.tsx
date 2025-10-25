import React from 'react';
import { useTranslation } from 'react-i18next';
import { Clock, Download } from 'lucide-react';
import { TimelineEvent } from './types';

interface TimelinePanelProps {
  events: TimelineEvent[];
  onExportCSV: () => void;
}

export const TimelinePanel: React.FC<TimelinePanelProps> = ({ events, onExportCSV }) => {
  const { t } = useTranslation();

  return (
    <div className="bg-white dark:bg-slate-800 p-6 rounded-xl shadow-lg border border-slate-200 dark:border-slate-700">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold flex items-center gap-2 text-slate-900 dark:text-white">
          <Clock className="h-5 w-5 text-amber-600 dark:text-amber-400" />
          {t('investigator.timeline.title', 'Timeline Analysis')}
        </h3>
        {events.length > 0 && (
          <div className="flex items-center gap-3">
            <span className="text-sm text-slate-500 dark:text-slate-400">
              {events.length} {t('investigator.timeline.events', 'events')}
            </span>
            <button
              onClick={onExportCSV}
              className="px-3 py-1.5 rounded-lg bg-slate-100 dark:bg-slate-700 hover:bg-slate-200 dark:hover:bg-slate-600 text-slate-700 dark:text-slate-200 text-xs font-medium transition-colors flex items-center gap-1.5"
              aria-label="Export timeline as CSV"
              title="Export timeline as CSV"
            >
              <Download className="h-3.5 w-3.5" />
              CSV Export
            </button>
          </div>
        )}
      </div>

      {events.length > 0 ? (
        <div className="space-y-3 max-h-64 overflow-y-auto pr-2 scrollbar-thin scrollbar-thumb-slate-300 dark:scrollbar-thumb-slate-600">
          {events.slice(0, 20).map((event: TimelineEvent, index: number) => (
            <div
              key={index}
              className="flex items-center gap-3 p-4 bg-slate-50 dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
            >
              <div
                className={`w-3 h-3 rounded-full ring-4 ${
                  event.risk_score >= 70
                    ? 'bg-red-500 dark:bg-red-400 ring-red-500/20 dark:ring-red-400/20'
                    : event.risk_score >= 40
                    ? 'bg-yellow-500 dark:bg-yellow-400 ring-yellow-500/20 dark:ring-yellow-400/20'
                    : 'bg-green-500 dark:bg-green-400 ring-green-500/20 dark:ring-green-400/20'
                }`}
              />
              <div className="flex-1 min-w-0">
                <div className="text-sm font-semibold text-slate-900 dark:text-white">
                  {event.event_type.replace('_', ' ').toUpperCase()}
                </div>
                <div className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                  {new Date(event.timestamp).toLocaleString()}
                </div>
              </div>
              <div className="text-right">
                <div className="text-sm font-mono font-semibold text-slate-900 dark:text-white">
                  {event.value.toFixed(4)} ETH
                </div>
                <div className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                  {t('investigator.timeline.risk', 'Risk')}:{' '}
                  <span className="font-semibold">{event.risk_score}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-12">
          <Clock className="h-12 w-12 text-slate-300 dark:text-slate-600 mx-auto mb-4" />
          <p className="text-slate-600 dark:text-slate-400 font-medium mb-2">
            {t('investigator.timeline.empty', 'No timeline data available')}
          </p>
          <p className="text-sm text-slate-500 dark:text-slate-500">
            {t('investigator.timeline.select_address', 'Select an address to view its transaction timeline')}
          </p>
        </div>
      )}
    </div>
  );
};
