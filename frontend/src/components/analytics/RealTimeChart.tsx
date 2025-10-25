import React from 'react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Area,
  AreaChart,
} from 'recharts';
import { motion } from 'framer-motion';

/**
 * Premium Chart Components for Advanced Analytics
 * Beautiful, interactive charts with real-time updates
 */

// Color Palettes
export const RISK_COLORS = {
  critical: '#ef4444', // red-500
  high: '#f97316', // orange-500
  medium: '#eab308', // yellow-500
  low: '#22c55e', // green-500
};

export const GRADIENT_COLORS = {
  primary: ['#6366f1', '#8b5cf6'], // indigo-500 to purple-500
  success: ['#22c55e', '#16a34a'], // green-500 to green-600
  warning: ['#f59e0b', '#d97706'], // amber-500 to amber-600
  danger: ['#ef4444', '#dc2626'], // red-500 to red-600
};

// Custom Tooltip
interface CustomTooltipProps {
  active?: boolean;
  payload?: any[];
  label?: string;
  formatter?: (value: any, name: string) => string;
}

const CustomTooltip: React.FC<CustomTooltipProps> = ({ active, payload, label, formatter }) => {
  if (!active || !payload || payload.length === 0) {
    return null;
  }

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg shadow-lg p-4"
    >
      {label && (
        <p className="font-medium text-slate-900 dark:text-white mb-2">
          {label}
        </p>
      )}
      {payload.map((entry, index) => (
        <div key={index} className="flex items-center gap-2 text-sm">
          <div
            className="w-3 h-3 rounded-full"
            style={{ backgroundColor: entry.color }}
          />
          <span className="text-slate-600 dark:text-slate-400">
            {entry.name}:
          </span>
          <span className="font-medium text-slate-900 dark:text-white">
            {formatter ? formatter(entry.value, entry.name) : entry.value}
          </span>
        </div>
      ))}
    </motion.div>
  );
};

// ===================================
// RISK DISTRIBUTION CHART (Area)
// ===================================

interface RiskDistributionChartProps {
  data: any[];
  height?: number;
}

export const RiskDistributionChart: React.FC<RiskDistributionChartProps> = ({
  data,
  height = 300,
}) => {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={data}>
        <defs>
          <linearGradient id="criticalGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor={RISK_COLORS.critical} stopOpacity={0.8} />
            <stop offset="95%" stopColor={RISK_COLORS.critical} stopOpacity={0.1} />
          </linearGradient>
          <linearGradient id="highGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor={RISK_COLORS.high} stopOpacity={0.8} />
            <stop offset="95%" stopColor={RISK_COLORS.high} stopOpacity={0.1} />
          </linearGradient>
          <linearGradient id="mediumGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor={RISK_COLORS.medium} stopOpacity={0.8} />
            <stop offset="95%" stopColor={RISK_COLORS.medium} stopOpacity={0.1} />
          </linearGradient>
          <linearGradient id="lowGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor={RISK_COLORS.low} stopOpacity={0.8} />
            <stop offset="95%" stopColor={RISK_COLORS.low} stopOpacity={0.1} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" className="dark:stroke-slate-700" />
        <XAxis
          dataKey="date"
          stroke="#94a3b8"
          tick={{ fill: '#64748b' }}
          tickFormatter={(value) => new Date(value).toLocaleDateString('de-DE', { month: 'short', day: 'numeric' })}
        />
        <YAxis stroke="#94a3b8" tick={{ fill: '#64748b' }} />
        <Tooltip content={<CustomTooltip />} />
        <Legend />
        <Area
          type="monotone"
          dataKey="critical"
          stackId="1"
          stroke={RISK_COLORS.critical}
          fill="url(#criticalGradient)"
          name="Critical"
        />
        <Area
          type="monotone"
          dataKey="high"
          stackId="1"
          stroke={RISK_COLORS.high}
          fill="url(#highGradient)"
          name="High"
        />
        <Area
          type="monotone"
          dataKey="medium"
          stackId="1"
          stroke={RISK_COLORS.medium}
          fill="url(#mediumGradient)"
          name="Medium"
        />
        <Area
          type="monotone"
          dataKey="low"
          stackId="1"
          stroke={RISK_COLORS.low}
          fill="url(#lowGradient)"
          name="Low"
        />
      </AreaChart>
    </ResponsiveContainer>
  );
};

// ===================================
// THREAT CATEGORIES CHART (Pie)
// ===================================

interface ThreatCategoriesChartProps {
  data: any[];
  height?: number;
}

export const ThreatCategoriesChart: React.FC<ThreatCategoriesChartProps> = ({
  data,
  height = 300,
}) => {
  const COLORS = ['#6366f1', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981', '#3b82f6', '#ef4444'];

  return (
    <ResponsiveContainer width="100%" height={height}>
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          labelLine={false}
          label={({ name, percentage }) => `${name}: ${percentage.toFixed(1)}%`}
          outerRadius={100}
          fill="#8884d8"
          dataKey="count"
        >
          {data.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
          ))}
        </Pie>
        <Tooltip
          content={<CustomTooltip formatter={(value, name) => `${value} (${name})`} />}
        />
      </PieChart>
    </ResponsiveContainer>
  );
};

// ===================================
// TOP ENTITIES CHART (Bar)
// ===================================

interface TopEntitiesChartProps {
  data: any[];
  height?: number;
  dataKey: string;
  entityType: 'exchange' | 'mixer';
}

export const TopEntitiesChart: React.FC<TopEntitiesChartProps> = ({
  data,
  height = 300,
  dataKey,
  entityType,
}) => {
  const color = entityType === 'exchange' ? '#6366f1' : '#f97316';

  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} layout="vertical">
        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" className="dark:stroke-slate-700" />
        <XAxis type="number" stroke="#94a3b8" tick={{ fill: '#64748b' }} />
        <YAxis
          type="category"
          dataKey="name"
          stroke="#94a3b8"
          tick={{ fill: '#64748b' }}
          width={100}
        />
        <Tooltip
          content={<CustomTooltip formatter={(value) => {
            if (dataKey === 'volume_usd') {
              return `$${(value / 1000000).toFixed(2)}M`;
            }
            return value.toLocaleString();
          }} />}
        />
        <Bar dataKey={dataKey} fill={color} radius={[0, 8, 8, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
};

// ===================================
// COMPARISON CHART (Line)
// ===================================

interface ComparisonChartProps {
  data: any[];
  height?: number;
}

export const ComparisonChart: React.FC<ComparisonChartProps> = ({ data, height = 300 }) => {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" className="dark:stroke-slate-700" />
        <XAxis dataKey="name" stroke="#94a3b8" tick={{ fill: '#64748b' }} />
        <YAxis stroke="#94a3b8" tick={{ fill: '#64748b' }} />
        <Tooltip content={<CustomTooltip />} />
        <Legend />
        <Line
          type="monotone"
          dataKey="period1"
          stroke="#6366f1"
          strokeWidth={2}
          dot={{ r: 4 }}
          name="Period 1"
        />
        <Line
          type="monotone"
          dataKey="period2"
          stroke="#8b5cf6"
          strokeWidth={2}
          dot={{ r: 4 }}
          name="Period 2"
        />
      </LineChart>
    </ResponsiveContainer>
  );
};

// ===================================
// REAL-TIME METRICS (Mini Cards)
// ===================================

interface MetricCardProps {
  title: string;
  value: number | string;
  change?: number;
  icon?: React.ReactNode;
  trend?: 'up' | 'down' | 'neutral';
  color?: 'primary' | 'success' | 'warning' | 'danger';
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  change,
  icon,
  trend,
  color = 'primary',
}) => {
  const colorClasses = {
    primary: 'from-primary-500 to-purple-500',
    success: 'from-green-500 to-emerald-500',
    warning: 'from-amber-500 to-orange-500',
    danger: 'from-red-500 to-pink-500',
  };

  const trendColors = {
    up: 'text-green-600 dark:text-green-400',
    down: 'text-red-600 dark:text-red-400',
    neutral: 'text-slate-600 dark:text-slate-400',
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -4 }}
      className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-6 hover:shadow-lg transition-all duration-200"
    >
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-medium text-slate-600 dark:text-slate-400">{title}</h3>
        {icon && (
          <div className={`p-2 rounded-lg bg-gradient-to-br ${colorClasses[color]}`}>
            <div className="text-white">{icon}</div>
          </div>
        )}
      </div>
      <div className="flex items-end justify-between">
        <p className="text-3xl font-bold text-slate-900 dark:text-white">{value}</p>
        {change !== undefined && trend && (
          <div className={`flex items-center gap-1 text-sm font-medium ${trendColors[trend]}`}>
            {trend === 'up' && '↗'}
            {trend === 'down' && '↘'}
            {trend === 'neutral' && '→'}
            <span>{Math.abs(change)}%</span>
          </div>
        )}
      </div>
    </motion.div>
  );
};

export default {
  RiskDistributionChart,
  ThreatCategoriesChart,
  TopEntitiesChart,
  ComparisonChart,
  MetricCard,
};
