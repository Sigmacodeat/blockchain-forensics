import React from 'react';
import { motion } from 'framer-motion';
import { TrendingUp, TrendingDown, Activity, Shield } from 'lucide-react';
import { Card } from '@/components/ui/card';
import type { NetworkStats as NetworkStatsType } from '@/hooks/useIntelligenceNetwork';

interface Props {
  stats: NetworkStatsType | undefined;
  loading: boolean;
}

export function NetworkStats({ stats, loading }: Props) {
  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {[...Array(4)].map((_, i) => (
          <Card key={i} className="p-6">
            <div className="animate-pulse space-y-4">
              <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-1/2" />
              <div className="h-8 bg-slate-200 dark:bg-slate-700 rounded" />
              <div className="h-3 bg-slate-200 dark:bg-slate-700 rounded w-3/4" />
            </div>
          </Card>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Network Health */}
      <Card className="p-6 bg-gradient-to-br from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20 border-green-200">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold flex items-center gap-2 text-green-900 dark:text-green-100">
            <Shield className="w-5 h-5" />
            Network Health
          </h3>
          <span className="px-3 py-1 rounded-full text-xs font-medium bg-green-600 text-white">
            Excellent
          </span>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <MetricItem
            label="Response Time"
            value="< 100ms"
            trend="down"
            trendValue="12%"
          />
          <MetricItem
            label="Accuracy"
            value="98.5%"
            trend="up"
            trendValue="2.1%"
          />
          <MetricItem
            label="Coverage"
            value="20+ Chains"
            trend="up"
            trendValue="3 new"
          />
          <MetricItem
            label="Uptime"
            value="99.9%"
            trend="stable"
          />
        </div>
      </Card>

      {/* Investigation Impact */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Activity className="w-5 h-5 text-primary-600" />
            Investigation Impact
          </h3>
          <div className="space-y-4">
            <ImpactRow
              label="Addresses Monitored"
              value={stats?.addresses_monitored || 0}
              color="blue"
            />
            <ImpactRow
              label="Funds Frozen"
              value={`$${formatNumber(stats?.funds_frozen_usd || 0)}`}
              color="orange"
            />
            <ImpactRow
              label="Funds Recovered"
              value={`$${formatNumber(stats?.funds_recovered_usd || 0)}`}
              color="green"
            />
            <ImpactRow
              label="Active Investigations"
              value={stats?.pending_flags || 0}
              color="purple"
            />
          </div>
        </Card>

        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4">Network Activity (24h)</h3>
          <div className="space-y-4">
            <ActivityBar
              label="Flags Submitted"
              value={45}
              max={100}
              color="orange"
            />
            <ActivityBar
              label="Confirmations"
              value={78}
              max={100}
              color="green"
            />
            <ActivityBar
              label="Address Checks"
              value={stats?.total_checks || 0}
              max={5000}
              color="blue"
            />
            <ActivityBar
              label="Auto-Traces"
              value={32}
              max={100}
              color="purple"
            />
          </div>
        </Card>
      </div>

      {/* Top Contributors */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">🏆 Top Contributors (This Month)</h3>
        <div className="space-y-3">
          <ContributorRow
            rank={1}
            name="Chainalysis Investigation Team"
            flags={142}
            confirmations={89}
            tier="verified_security_firm"
          />
          <ContributorRow
            rank={2}
            name="FBI Cyber Division"
            flags={98}
            confirmations={95}
            tier="law_enforcement"
          />
          <ContributorRow
            rank={3}
            name="Binance Security"
            flags={87}
            confirmations={82}
            tier="exchange"
          />
        </div>
      </Card>
    </div>
  );
}

// Helper Components
interface MetricItemProps {
  label: string;
  value: string;
  trend?: 'up' | 'down' | 'stable';
  trendValue?: string;
}

function MetricItem({ label, value, trend, trendValue }: MetricItemProps) {
  return (
    <div>
      <p className="text-xs text-slate-600 dark:text-slate-400 mb-1">{label}</p>
      <p className="text-lg font-bold text-slate-900 dark:text-white">{value}</p>
      {trend && trendValue && (
        <div className="flex items-center gap-1 mt-1">
          {trend === 'up' && <TrendingUp className="w-3 h-3 text-green-600" />}
          {trend === 'down' && <TrendingDown className="w-3 h-3 text-green-600" />}
          <span className={`text-xs ${trend === 'stable' ? 'text-slate-500' : 'text-green-600'}`}>
            {trendValue}
          </span>
        </div>
      )}
    </div>
  );
}

interface ImpactRowProps {
  label: string;
  value: string | number;
  color: 'blue' | 'orange' | 'green' | 'purple';
}

function ImpactRow({ label, value, color }: ImpactRowProps) {
  const colorClasses = {
    blue: 'text-blue-600 bg-blue-50',
    orange: 'text-orange-600 bg-orange-50',
    green: 'text-green-600 bg-green-50',
    purple: 'text-purple-600 bg-purple-50',
  };

  return (
    <div className="flex items-center justify-between">
      <span className="text-sm text-slate-600 dark:text-slate-400">{label}</span>
      <span className={`px-3 py-1 rounded-full text-sm font-semibold ${colorClasses[color]}`}>
        {value}
      </span>
    </div>
  );
}

interface ActivityBarProps {
  label: string;
  value: number;
  max: number;
  color: 'blue' | 'orange' | 'green' | 'purple';
}

function ActivityBar({ label, value, max, color }: ActivityBarProps) {
  const percentage = Math.min((value / max) * 100, 100);
  const colorClasses = {
    blue: 'bg-blue-500',
    orange: 'bg-orange-500',
    green: 'bg-green-500',
    purple: 'bg-purple-500',
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <span className="text-sm text-slate-600 dark:text-slate-400">{label}</span>
        <span className="text-sm font-semibold text-slate-900 dark:text-white">{value}</span>
      </div>
      <div className="h-2 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${percentage}%` }}
          transition={{ duration: 0.5, ease: 'easeOut' }}
          className={`h-full ${colorClasses[color]}`}
        />
      </div>
    </div>
  );
}

interface ContributorRowProps {
  rank: number;
  name: string;
  flags: number;
  confirmations: number;
  tier: string;
}

function ContributorRow({ rank, name, flags, confirmations, tier }: ContributorRowProps) {
  const getRankBadge = (rank: number) => {
    if (rank === 1) return '🥇';
    if (rank === 2) return '🥈';
    if (rank === 3) return '🥉';
    return rank;
  };

  const getTierColor = (tier: string) => {
    const colors: Record<string, string> = {
      law_enforcement: 'text-blue-600 bg-blue-50',
      verified_security_firm: 'text-purple-600 bg-purple-50',
      exchange: 'text-green-600 bg-green-50',
      government: 'text-indigo-600 bg-indigo-50',
    };
    return colors[tier] || 'text-slate-600 bg-slate-50';
  };

  return (
    <div className="flex items-center gap-4 p-3 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors">
      <div className="text-2xl">{getRankBadge(rank)}</div>
      <div className="flex-1">
        <div className="flex items-center gap-2 mb-1">
          <span className="font-medium text-slate-900 dark:text-white">{name}</span>
          <span className={`text-xs px-2 py-0.5 rounded-full ${getTierColor(tier)}`}>
            {tier.replace('_', ' ')}
          </span>
        </div>
        <div className="flex items-center gap-4 text-xs text-slate-600 dark:text-slate-400">
          <span>{flags} flags</span>
          <span>•</span>
          <span>{confirmations} confirmations</span>
          <span>•</span>
          <span>{((confirmations / flags) * 100).toFixed(0)}% accuracy</span>
        </div>
      </div>
    </div>
  );
}

function formatNumber(value: number): string {
  if (value >= 1000000000) {
    return `${(value / 1000000000).toFixed(2)}B`;
  } else if (value >= 1000000) {
    return `${(value / 1000000).toFixed(2)}M`;
  } else if (value >= 1000) {
    return `${(value / 1000).toFixed(2)}K`;
  } else {
    return value.toFixed(0);
  }
}
