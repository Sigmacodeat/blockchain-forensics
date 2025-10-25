import React, { useState } from 'react';
import { motion } from 'framer-motion';
import {
  Shield,
  AlertTriangle,
  CheckCircle,
  TrendingUp,
  Search,
  Flag,
  Users,
  DollarSign,
  Activity,
  Eye,
} from 'lucide-react';
import { useIntelligenceStats, useIntelligenceFlags } from '@/hooks/useIntelligenceNetwork';
import { NetworkStats } from '@/components/intelligence/NetworkStats';
import { ActiveFlags } from '@/components/intelligence/ActiveFlags';
import { FlagSubmission } from '@/components/intelligence/FlagSubmission';
import { AddressChecker } from '@/components/intelligence/AddressChecker';
import { Card } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

export default function IntelligenceNetwork() {
  const [activeTab, setActiveTab] = useState('overview');
  const { data: stats, isPending: statsLoading } = useIntelligenceStats();
  const { data: flagsData, isPending: flagsLoading } = useIntelligenceFlags();

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-purple-50 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900">
      {/* Hero Section */}
      <div className="bg-gradient-to-r from-primary-600 to-purple-600 text-white py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center"
          >
            <div className="flex items-center justify-center mb-4">
              <Shield className="w-16 h-16 mr-4" />
              <h1 className="text-4xl font-bold">Intelligence Network</h1>
            </div>
            <p className="text-xl text-blue-100 max-w-3xl mx-auto">
              🌐 Collaborative intelligence sharing network für Real-Time Threat Detection
            </p>
            <p className="text-sm text-blue-200 mt-2">
              Powered by TRM Beacon-Style Architecture
            </p>
          </motion.div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <StatCard
            icon={<Users className="w-6 h-6" />}
            label="Investigators"
            value={stats?.total_investigators || 0}
            trend="+12%"
            color="blue"
            loading={statsLoading}
          />
          <StatCard
            icon={<Flag className="w-6 h-6" />}
            label="Total Flags"
            value={stats?.total_flags || 0}
            trend="+24"
            color="purple"
            loading={statsLoading}
          />
          <StatCard
            icon={<CheckCircle className="w-6 h-6" />}
            label="Confirmed"
            value={stats?.confirmed_flags || 0}
            subtitle={`${stats?.pending_flags || 0} pending`}
            color="green"
            loading={statsLoading}
          />
          <StatCard
            icon={<DollarSign className="w-6 h-6" />}
            label="Funds Frozen"
            value={formatCurrency(stats?.funds_frozen_usd || 0)}
            subtitle={`${formatCurrency(stats?.funds_recovered_usd || 0)} recovered`}
            color="orange"
            loading={statsLoading}
          />
        </div>

        {/* Main Content Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-4 lg:w-auto">
            <TabsTrigger value="overview" className="flex items-center gap-2">
              <Activity className="w-4 h-4" />
              Overview
            </TabsTrigger>
            <TabsTrigger value="flags" className="flex items-center gap-2">
              <AlertTriangle className="w-4 h-4" />
              Active Flags
            </TabsTrigger>
            <TabsTrigger value="check" className="flex items-center gap-2">
              <Search className="w-4 h-4" />
              Check Address
            </TabsTrigger>
            <TabsTrigger value="submit" className="flex items-center gap-2">
              <Flag className="w-4 h-4" />
              Submit Flag
            </TabsTrigger>
          </TabsList>

          <TabsContent value="overview">
            <div className="space-y-6">
              <NetworkStats stats={stats} loading={statsLoading} />
            </div>
          </TabsContent>

          <TabsContent value="flags">
            <ActiveFlags flags={flagsData?.flags || []} loading={flagsLoading} />
          </TabsContent>

          <TabsContent value="check">
            <AddressChecker />
          </TabsContent>

          <TabsContent value="submit">
            <FlagSubmission />
          </TabsContent>
        </Tabs>

        {/* Live Activity Feed */}
        <Card className="mt-8 p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold flex items-center gap-2">
              <Activity className="w-5 h-5 text-primary-600" />
              Live Network Activity
            </h3>
            <span className="flex items-center gap-2 text-sm text-green-600">
              <span className="w-2 h-2 bg-green-600 rounded-full animate-pulse" />
              Live
            </span>
          </div>
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {/* Activity items - Mock data for demo */}
            <ActivityItem
              icon={<Flag className="w-4 h-4" />}
              text="🚨 High-risk flag: 0x742d...3f9a (Ethereum) - Ransomware detected"
              time="2 min ago"
              type="flag"
            />
            <ActivityItem
              icon={<CheckCircle className="w-4 h-4" />}
              text="✅ Flag confirmed by FBI Cyber Division"
              time="5 min ago"
              type="confirm"
            />
            <ActivityItem
              icon={<Eye className="w-4 h-4" />}
              text="🔍 1,247 addresses checked in last hour"
              time="8 min ago"
              type="check"
            />
            <ActivityItem
              icon={<AlertTriangle className="w-4 h-4" />}
              text="⚠️ Auto-trace initiated: $2.3M flagged funds moving to mixer"
              time="12 min ago"
              type="flag"
            />
            <ActivityItem
              icon={<CheckCircle className="w-4 h-4" />}
              text="💰 $480K recovered: Binance froze flagged funds"
              time="15 min ago"
              type="confirm"
            />
            <ActivityItem
              icon={<Shield className="w-4 h-4" />}
              text="🛡️ New investigator joined: Europol Cybercrime Unit"
              time="23 min ago"
              type="check"
            />
          </div>
        </Card>
      </div>
    </div>
  );
}

// Helper Components
interface StatCardProps {
  icon: React.ReactNode;
  label: string;
  value: string | number;
  trend?: string;
  subtitle?: string;
  color: 'blue' | 'purple' | 'green' | 'orange';
  loading?: boolean;
}

function StatCard({ icon, label, value, trend, subtitle, color, loading }: StatCardProps) {
  const colorClasses = {
    blue: 'from-blue-500 to-blue-600',
    purple: 'from-purple-500 to-purple-600',
    green: 'from-green-500 to-green-600',
    orange: 'from-orange-500 to-orange-600',
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ scale: 1.02 }}
      className="relative overflow-hidden"
    >
      <Card className="p-6 border-t-4 border-primary-500">
        <div className="flex items-start justify-between">
          <div className={`p-3 rounded-lg bg-gradient-to-br ${colorClasses[color]} text-white`}>
            {icon}
          </div>
          {trend && (
            <div className="flex items-center text-green-600 text-sm font-medium">
              <TrendingUp className="w-4 h-4 mr-1" />
              {trend}
            </div>
          )}
        </div>
        <div className="mt-4">
          <p className="text-sm text-slate-600 dark:text-slate-400">{label}</p>
          {loading ? (
            <div className="h-8 w-24 bg-slate-200 dark:bg-slate-700 animate-pulse rounded mt-1" />
          ) : (
            <>
              <p className="text-3xl font-bold text-slate-900 dark:text-white mt-1">{value}</p>
              {subtitle && (
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">{subtitle}</p>
              )}
            </>
          )}
        </div>
      </Card>
    </motion.div>
  );
}

interface ActivityItemProps {
  icon: React.ReactNode;
  text: string;
  time: string;
  type: 'flag' | 'confirm' | 'check';
}

function ActivityItem({ icon, text, time, type }: ActivityItemProps) {
  const colorClasses = {
    flag: 'text-orange-600 bg-orange-50',
    confirm: 'text-green-600 bg-green-50',
    check: 'text-blue-600 bg-blue-50',
  };

  return (
    <div className="flex items-start gap-3 p-3 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors">
      <div className={`p-2 rounded-lg ${colorClasses[type]}`}>{icon}</div>
      <div className="flex-1 min-w-0">
        <p className="text-sm text-slate-900 dark:text-white">{text}</p>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">{time}</p>
      </div>
    </div>
  );
}

function formatCurrency(value: number): string {
  if (value >= 1000000000) {
    return `$${(value / 1000000000).toFixed(2)}B`;
  } else if (value >= 1000000) {
    return `$${(value / 1000000).toFixed(2)}M`;
  } else if (value >= 1000) {
    return `$${(value / 1000).toFixed(2)}K`;
  } else {
    return `$${value.toFixed(2)}`;
  }
}
