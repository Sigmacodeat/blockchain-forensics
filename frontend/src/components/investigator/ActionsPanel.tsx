import React from 'react';
import { useTranslation } from 'react-i18next';
import { Activity, Users, Play, Pause } from 'lucide-react';
import { LocalGraph } from './types';

interface ActionsPanelProps {
  localGraph: LocalGraph | null;
  isPlaying: boolean;
  clusterPending: boolean;
  onCluster: () => void;
  onTogglePlay: () => void;
}

export const ActionsPanel: React.FC<ActionsPanelProps> = ({
  localGraph,
  isPlaying,
  clusterPending,
  onCluster,
  onTogglePlay,
}) => {
  const { t } = useTranslation();

  return (
    <div className="bg-white dark:bg-slate-800 p-6 rounded-xl shadow-lg border border-slate-200 dark:border-slate-700">
      <h3 className="text-base font-semibold mb-4 flex items-center gap-2 text-slate-900 dark:text-white">
        <div className="p-2 bg-purple-100 dark:bg-purple-900/30 rounded-lg">
          <Activity className="h-4 w-4 text-purple-600 dark:text-purple-400" />
        </div>
        {t('investigator.actions.title', 'Actions')}
      </h3>
      <div className="space-y-3">
        <button
          onClick={onCluster}
          disabled={!localGraph || clusterPending}
          className="w-full bg-gradient-to-r from-emerald-600 to-emerald-700 hover:from-emerald-700 hover:to-emerald-800 dark:from-emerald-500 dark:to-emerald-600 text-white py-3 px-4 rounded-lg font-medium shadow-lg shadow-emerald-500/20 transition-all hover:shadow-xl hover:shadow-emerald-500/30 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          <Users className="h-4 w-4" />
          {clusterPending
            ? t('investigator.actions.clustering', 'Clustering...')
            : t('investigator.actions.cluster', 'Cluster Addresses')}
        </button>

        <button
          className="w-full bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 dark:from-purple-500 dark:to-purple-600 text-white py-3 px-4 rounded-lg font-medium shadow-lg shadow-purple-500/20 transition-all hover:shadow-xl hover:shadow-purple-500/30 flex items-center justify-center gap-2"
          onClick={onTogglePlay}
        >
          {isPlaying ? (
            <>
              <Pause className="h-4 w-4" />
              {t('investigator.actions.pause_timeline', 'Pause Timeline')}
            </>
          ) : (
            <>
              <Play className="h-4 w-4" />
              {t('investigator.actions.play_timeline', 'Play Timeline')}
            </>
          )}
        </button>
      </div>
    </div>
  );
};
