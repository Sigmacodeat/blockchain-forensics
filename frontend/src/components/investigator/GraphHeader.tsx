import React from 'react';
import { useTranslation } from 'react-i18next';
import { Route, Users, Activity, Clock } from 'lucide-react';
import { LocalGraph, TimelineEvent } from './types';

interface GraphHeaderProps {
  localGraph: LocalGraph | null;
  timelineEvents: TimelineEvent[];
}

export const GraphHeader: React.FC<GraphHeaderProps> = ({ localGraph, timelineEvents }) => {
  const { t } = useTranslation();

  return (
    <div className="mb-8">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-3">
            <div className="p-3 bg-gradient-to-br from-primary-500 to-purple-600 rounded-xl shadow-lg">
              <Route className="h-7 w-7 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-slate-900 via-primary-800 to-purple-900 dark:from-white dark:via-primary-200 dark:to-purple-200 bg-clip-text text-transparent">
                {t('investigator.header.title', 'Investigator Graph Explorer')}
              </h1>
              <p className="text-slate-600 dark:text-slate-400 text-sm mt-1">
                {t('investigator.header.subtitle', 'Interaktive Graph-Exploration mit Pfadsuche und Timeline-Analyse')}
              </p>
            </div>
          </div>
          
          {/* Stats Bar */}
          {localGraph && (
            <div className="flex items-center gap-4 mt-4">
              <div className="px-4 py-2 bg-white dark:bg-slate-800 rounded-lg shadow-sm border border-slate-200 dark:border-slate-700">
                <div className="flex items-center gap-2">
                  <Users className="h-4 w-4 text-primary-600 dark:text-primary-400" />
                  <span className="text-sm font-semibold text-slate-900 dark:text-white">
                    {Object.keys(localGraph.nodes).length}
                  </span>
                  <span className="text-xs text-slate-500 dark:text-slate-400">Nodes</span>
                </div>
              </div>
              <div className="px-4 py-2 bg-white dark:bg-slate-800 rounded-lg shadow-sm border border-slate-200 dark:border-slate-700">
                <div className="flex items-center gap-2">
                  <Activity className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
                  <span className="text-sm font-semibold text-slate-900 dark:text-white">
                    {localGraph.links.length}
                  </span>
                  <span className="text-xs text-slate-500 dark:text-slate-400">Connections</span>
                </div>
              </div>
              {timelineEvents && timelineEvents.length > 0 && (
                <div className="px-4 py-2 bg-white dark:bg-slate-800 rounded-lg shadow-sm border border-slate-200 dark:border-slate-700">
                  <div className="flex items-center gap-2">
                    <Clock className="h-4 w-4 text-amber-600 dark:text-amber-400" />
                    <span className="text-sm font-semibold text-slate-900 dark:text-white">
                      {timelineEvents.length}
                    </span>
                    <span className="text-xs text-slate-500 dark:text-slate-400">Events</span>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
